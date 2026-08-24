from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
import re


class EnvelopeError(ValueError):
    pass


class ExecutionClass(str, Enum):
    SHADOW = "SHADOW"
    CONSEQUENTIAL = "CONSEQUENTIAL"


_HEX64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ExecutionEnvelope:
    project_id: str
    task_id: str
    decision_ref: str
    control_ref: str
    action_digest: str
    idempotency_key: str
    execution_class: ExecutionClass
    external_effect: bool = False
    exact_approval_ref: str | None = None


def validate_envelope(e: ExecutionEnvelope) -> None:
    for name in ("project_id", "task_id", "decision_ref", "control_ref", "idempotency_key"):
        value = getattr(e, name)
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise EnvelopeError(f"invalid {name}")
    if not isinstance(e.action_digest, str) or not _HEX64.fullmatch(e.action_digest):
        raise EnvelopeError("action_digest must be lowercase sha256 hex")
    if e.execution_class is ExecutionClass.SHADOW:
        if e.external_effect:
            raise EnvelopeError("shadow envelope cannot authorize an external effect")
        if e.exact_approval_ref is not None:
            raise EnvelopeError("shadow envelope must not carry consequential approval")
    elif e.execution_class is ExecutionClass.CONSEQUENTIAL:
        if not e.exact_approval_ref or not e.exact_approval_ref.strip():
            raise EnvelopeError("consequential envelope requires upstream exact-approval reference")
    else:
        raise EnvelopeError("unsupported execution class")


def immutable_binding_digest(e: ExecutionEnvelope) -> str:
    """Bind logical idempotency to the immutable action/control snapshot, not an approval token."""
    validate_envelope(e)
    payload = {
        "project_id": e.project_id,
        "task_id": e.task_id,
        "decision_ref": e.decision_ref,
        "control_ref": e.control_ref,
        "action_digest": e.action_digest,
        "execution_class": e.execution_class.value,
        "external_effect": e.external_effect,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def enqueue_from_control(store, envelope: ExecutionEnvelope):
    """Persist execution intent only. This never validates or grants upstream approval."""
    binding = immutable_binding_digest(envelope)
    approval_required = envelope.execution_class is ExecutionClass.CONSEQUENTIAL
    return store.enqueue(envelope.task_id, envelope.idempotency_key, approval_required, binding_digest=binding)
