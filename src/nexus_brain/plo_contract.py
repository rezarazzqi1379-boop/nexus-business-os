from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .shadow_loop import ShadowTaskIntent


@dataclass(frozen=True)
class PLOShadowEnvelopeFields:
    project_id: str
    task_id: str
    decision_ref: str
    control_ref: str
    action_digest: str
    idempotency_key: str
    execution_class: str = "SHADOW"
    external_effect: bool = False
    exact_approval_ref: None = None


def _sha256(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def to_plo_shadow_envelope(
    intent: ShadowTaskIntent,
    *,
    decision_ref: str,
    control_ref: str,
) -> PLOShadowEnvelopeFields:
    """Translate a governed Brain shadow intent into the exact field contract PLO expects.

    This adapter is intentionally data-only. It does not import or execute PLO, does not
    grant approval, and cannot create an external effect. PLO remains the durable execution
    substrate; Brain remains the decision/evidence authority.
    """
    for name, value in (("decision_ref", decision_ref), ("control_ref", control_ref)):
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise ValueError(f"invalid {name}")
    if intent.external_effect:
        raise ValueError("Brain shadow intent cannot map to external-effect PLO work")
    if not isinstance(intent.action_digest, str) or len(intent.action_digest) != 64:
        raise ValueError("invalid shadow action digest")
    try:
        int(intent.action_digest, 16)
    except ValueError as exc:
        raise ValueError("invalid shadow action digest") from exc

    idempotency_key = _sha256(
        {
            "project_id": intent.project_id,
            "task_id": intent.task_id,
            "decision_ref": decision_ref,
            "control_ref": control_ref,
            "action_digest": intent.action_digest,
            "execution_class": "SHADOW",
            "external_effect": False,
        }
    )
    return PLOShadowEnvelopeFields(
        project_id=intent.project_id,
        task_id=intent.task_id,
        decision_ref=decision_ref,
        control_ref=control_ref,
        action_digest=intent.action_digest,
        idempotency_key=idempotency_key,
    )


def plo_binding_digest(fields: PLOShadowEnvelopeFields) -> str:
    """Mirror PLO immutable-binding semantics for pre-integration compatibility tests."""
    return _sha256(
        {
            "project_id": fields.project_id,
            "task_id": fields.task_id,
            "decision_ref": fields.decision_ref,
            "control_ref": fields.control_ref,
            "action_digest": fields.action_digest,
            "execution_class": fields.execution_class,
            "external_effect": fields.external_effect,
        }
    )
