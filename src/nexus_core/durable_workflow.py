from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256


TERMINAL_STATES = {"completed", "failed", "cancelled", "human_gate"}
RUNNABLE_STATES = {"pending", "running", "waiting_retry", "waiting_external"}
ALL_STATES = TERMINAL_STATES | RUNNABLE_STATES


@dataclass(frozen=True)
class WorkflowState:
    workflow_id: str
    workflow_type: str
    state: str
    sequence: int
    idempotency_key: str
    payload_digest: str
    source_version_ref: str
    updated_at: datetime


def digest_payload(payload: str) -> str:
    return sha256(payload.encode("utf-8")).hexdigest()


def validate_workflow_state(state: WorkflowState) -> tuple[str, ...]:
    errors: list[str] = []
    if not state.workflow_id.strip():
        errors.append("invalid_workflow_id")
    if not state.workflow_type.strip():
        errors.append("invalid_workflow_type")
    if state.state not in ALL_STATES:
        errors.append("invalid_state")
    if state.sequence < 0:
        errors.append("invalid_sequence")
    if not state.idempotency_key.strip():
        errors.append("missing_idempotency_key")
    if len(state.payload_digest) != 64:
        errors.append("invalid_payload_digest")
    if not state.source_version_ref.strip():
        errors.append("missing_source_version_ref")
    if state.updated_at.tzinfo is None:
        errors.append("timezone_naive_updated_at")
    return tuple(errors)


def can_transition(current: WorkflowState, candidate: WorkflowState) -> tuple[bool, tuple[str, ...]]:
    """Validate replay-safe state movement.

    Sequence numbers prevent out-of-order writes. Exact idempotency/source-version binding
    prevents a retry from silently applying a different payload under an old approval.
    Terminal states do not reopen implicitly.
    """
    errors = list(validate_workflow_state(current)) + list(validate_workflow_state(candidate))
    if current.workflow_id != candidate.workflow_id:
        errors.append("workflow_identity_changed")
    if current.workflow_type != candidate.workflow_type:
        errors.append("workflow_type_changed")
    if current.state in TERMINAL_STATES:
        errors.append("terminal_state_reopen")
    if candidate.sequence != current.sequence + 1:
        errors.append("non_monotonic_sequence")
    if candidate.updated_at < current.updated_at:
        errors.append("time_reversal")
    if candidate.idempotency_key == current.idempotency_key and candidate.payload_digest != current.payload_digest:
        errors.append("idempotency_payload_mismatch")
    return (not errors, tuple(dict.fromkeys(errors)))


def is_replay_equivalent(a: WorkflowState, b: WorkflowState) -> bool:
    """Return True only for the same logical event observed more than once."""
    return (
        a.workflow_id == b.workflow_id
        and a.sequence == b.sequence
        and a.idempotency_key == b.idempotency_key
        and a.payload_digest == b.payload_digest
        and a.source_version_ref == b.source_version_ref
        and a.state == b.state
    )
