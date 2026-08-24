from __future__ import annotations

from dataclasses import dataclass
import re

from .execution import ExecutionIntent, validate_execution_intent_binding
from .graph import BrainGraph


_HEX64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ShadowExecutionEnvelope:
    project_id: str
    task_id: str
    decision_ref: str
    control_ref: str
    action_digest: str
    idempotency_key: str
    execution_class: str = "SHADOW"
    external_effect: bool = False
    exact_approval_ref: None = None


def to_shadow_execution_envelope(graph: BrainGraph, intent: ExecutionIntent) -> ShadowExecutionEnvelope:
    """Translate a valid Brain ExecutionIntent to the narrow PLO shadow shape.

    This adapter intentionally carries no approval and cannot authorize external effects.
    The durable runtime remains an execution-state owner only.
    """
    if not validate_execution_intent_binding(graph, intent):
        raise ValueError("execution intent binding is stale or invalid")
    if intent.consequential or intent.external_execution_allowed:
        raise ValueError("only internal read-only intents may cross the shadow bridge")
    if not intent.intent_id.startswith("EI-"):
        raise ValueError("invalid execution intent id")
    digest = intent.intent_id[3:]
    if not _HEX64.fullmatch(digest):
        raise ValueError("execution intent id must contain lowercase sha256 digest")

    return ShadowExecutionEnvelope(
        project_id=intent.project_id,
        task_id=intent.intent_id,
        decision_ref=intent.source_node_id,
        control_ref=intent.canonical_snapshot_digest,
        action_digest=digest,
        idempotency_key=intent.intent_id,
    )
