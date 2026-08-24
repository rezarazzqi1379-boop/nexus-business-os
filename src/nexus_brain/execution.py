from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import unicodedata
from typing import Any, Mapping

from .command import InternalActionRecommendation
from .graph import BrainGraph
from .projection import project_projection


def _compact_text(name: str, value: object, *, max_len: int = 512) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > max_len:
        raise ValueError(f"invalid {name}")
    if any(unicodedata.category(ch) in {"Cc", "Cf", "Zl", "Zp"} for ch in value):
        raise ValueError(f"invalid {name}")
    return value


def _aware_iso(value: object) -> str:
    text = _compact_text("created_at", value, max_len=64)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("created_at must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("created_at must be timezone-aware")
    return text


def _canonical_json(value: object) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("payload must be canonical JSON data") from exc


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def canonical_project_snapshot_digest(graph: BrainGraph, project_id: str) -> str:
    _compact_text("project_id", project_id, max_len=128)
    projection = project_projection(graph, project_id)
    if projection["project_id"] != project_id:
        raise ValueError("project projection mismatch")
    return _sha256(projection)


@dataclass(frozen=True)
class ExecutionIntent:
    """Immutable hand-off from Brain/Control to a durable executor.

    v0.1 intentionally supports internal read-only work only.  It creates no
    approval authority and grants no external execution capability.
    """

    intent_id: str
    version: str
    project_id: str
    action: str
    source_node_id: str
    source_refs: tuple[str, ...]
    canonical_snapshot_digest: str
    payload_digest: str
    payload: Mapping[str, Any]
    created_at: str
    consequential: bool = False
    external_execution_allowed: bool = False

    def envelope(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "project_id": self.project_id,
            "action": self.action,
            "source_node_id": self.source_node_id,
            "source_refs": list(self.source_refs),
            "canonical_snapshot_digest": self.canonical_snapshot_digest,
            "payload_digest": self.payload_digest,
            "payload": dict(self.payload),
            "created_at": self.created_at,
            "consequential": self.consequential,
            "external_execution_allowed": self.external_execution_allowed,
        }


def build_read_only_execution_intent(
    graph: BrainGraph,
    recommendation: InternalActionRecommendation,
    *,
    created_at: str,
    payload: Mapping[str, Any] | None = None,
) -> ExecutionIntent:
    if not isinstance(recommendation, InternalActionRecommendation):
        raise ValueError("recommendation must be InternalActionRecommendation")
    if recommendation.external_execution_allowed is not False:
        raise ValueError("v0.1 accepts internal-only recommendations")

    project_id = _compact_text("project_id", recommendation.project_id, max_len=128)
    action = _compact_text("action", recommendation.action, max_len=256)
    source_node_id = _compact_text("source_node_id", recommendation.source_node_id, max_len=256)
    created = _aware_iso(created_at)

    source = graph.nodes.get(source_node_id)
    if source is None:
        raise ValueError("source node not found")
    if source.project_id != project_id:
        raise ValueError("source node project mismatch")
    if not source.source_refs:
        raise ValueError("source node has no provenance")

    normalized_refs = tuple(_compact_text("source_ref", ref, max_len=512) for ref in source.source_refs)
    if len(normalized_refs) != len(set(normalized_refs)):
        raise ValueError("duplicate source refs")

    payload_dict: dict[str, Any] = dict(payload or {})
    payload_digest = _sha256(payload_dict)
    snapshot_digest = canonical_project_snapshot_digest(graph, project_id)

    binding = {
        "version": "execution-intent-v0.1",
        "project_id": project_id,
        "action": action,
        "source_node_id": source_node_id,
        "source_refs": list(normalized_refs),
        "canonical_snapshot_digest": snapshot_digest,
        "payload_digest": payload_digest,
        "payload": payload_dict,
        "created_at": created,
        "consequential": False,
        "external_execution_allowed": False,
    }
    intent_id = "EI-" + _sha256(binding)
    return ExecutionIntent(
        intent_id=intent_id,
        version="execution-intent-v0.1",
        project_id=project_id,
        action=action,
        source_node_id=source_node_id,
        source_refs=normalized_refs,
        canonical_snapshot_digest=snapshot_digest,
        payload_digest=payload_digest,
        payload=payload_dict,
        created_at=created,
    )


def validate_execution_intent_binding(graph: BrainGraph, intent: ExecutionIntent) -> bool:
    """Fail closed if an intent no longer matches current governed state."""
    if not isinstance(intent, ExecutionIntent):
        raise ValueError("intent must be ExecutionIntent")
    if intent.version != "execution-intent-v0.1":
        return False
    if intent.consequential or intent.external_execution_allowed:
        return False
    source = graph.nodes.get(intent.source_node_id)
    if source is None or source.project_id != intent.project_id:
        return False
    if tuple(source.source_refs) != tuple(intent.source_refs):
        return False
    if _sha256(dict(intent.payload)) != intent.payload_digest:
        return False
    if canonical_project_snapshot_digest(graph, intent.project_id) != intent.canonical_snapshot_digest:
        return False

    binding = intent.envelope()
    expected_id = "EI-" + _sha256(binding)
    return expected_id == intent.intent_id
