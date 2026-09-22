from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class ObservationPhase(str, Enum):
    RUNNING = "running"
    BLOCKED = "blocked"
    PRODUCED = "produced"
    FAILED = "failed"


@dataclass(frozen=True)
class RunnerObservation:
    observation_id: str
    project_id: str
    packet_digest: str
    phase: ObservationPhase
    reason: str


_RUNNING = {
    "thread/started",
    "turn/started",
    "item/started",
    "item/delta",
}
_BLOCKED = {
    "item/commandExecution/requestApproval",
    "item/fileChange/requestApproval",
    "item/tool/requestUserInput",
}
_PRODUCED = {"turn/completed"}
_FAILED = {"turn/failed", "error"}


def normalize_app_server_event(
    event: Mapping[str, Any],
    *,
    project_id: str,
    packet_digest: str,
) -> RunnerObservation:
    """Normalize one Codex App Server event without granting acceptance.

    This adapter deliberately has no ACCEPTED state. A completed turn only means
    that a runner produced output; the NEXUS Supervisor must still verify the
    exact project/packet binding, artifact, evidence, tests, budget and approval.
    """
    if not project_id.strip():
        raise ValueError("project_id_required")
    if len(packet_digest) != 64 or any(c not in "0123456789abcdef" for c in packet_digest):
        raise ValueError("packet_digest_must_be_lowercase_sha256")

    method = event.get("method")
    if not isinstance(method, str) or not method.strip():
        raise ValueError("event_method_required")
    event_id = event.get("id") or event.get("event_id")
    if not isinstance(event_id, (str, int)) or not str(event_id).strip():
        raise ValueError("event_id_required")

    if method in _RUNNING:
        phase, reason = ObservationPhase.RUNNING, "structured_runner_activity"
    elif method in _BLOCKED:
        phase, reason = ObservationPhase.BLOCKED, "exact_human_input_or_approval_required"
    elif method in _PRODUCED:
        phase, reason = ObservationPhase.PRODUCED, "runner_turn_completed_unverified"
    elif method in _FAILED:
        phase, reason = ObservationPhase.FAILED, "runner_reported_failure"
    else:
        phase, reason = ObservationPhase.BLOCKED, "unknown_app_server_event"

    return RunnerObservation(
        observation_id=f"codex-app-server:{event_id}",
        project_id=project_id,
        packet_digest=packet_digest,
        phase=phase,
        reason=reason,
    )
