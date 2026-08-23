from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Mapping, Sequence
from unicodedata import category

_MAX_ID = 256
_MAX_TEXT = 100_000
_DISALLOWED_CATEGORIES = {"Cc", "Cf", "Zl", "Zp"}
_ALLOWED_BODY_CONTROLS = {"\n", "\r", "\t"}


@dataclass(frozen=True)
class ExactSendApproval:
    action_id: str
    approved: bool = True


@dataclass(frozen=True)
class ExactSendDecision:
    allowed: bool
    requires_human_approval: bool
    action_id: str
    reason: str


def _clean_control_text(name: str, value: object, max_len: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    if not value.strip() or value != value.strip():
        raise ValueError(f"{name} must be non-empty and trimmed")
    if len(value) > max_len:
        raise ValueError(f"{name} is too long")
    if any(category(ch) in _DISALLOWED_CATEGORIES for ch in value):
        raise ValueError(f"{name} contains disallowed control/formatting characters")
    return value


def _clean_message_body(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("body must be a string")
    if not value.strip():
        raise ValueError("body must be non-empty")
    if len(value) > _MAX_TEXT:
        raise ValueError("body is too long")
    for ch in value:
        if category(ch) in _DISALLOWED_CATEGORIES and ch not in _ALLOWED_BODY_CONTROLS:
            raise ValueError("body contains disallowed control/formatting characters")
    return value


def exact_send_action_id(
    *,
    batch_id: str,
    message_id: str,
    target: str,
    subject: str,
    body: str,
    source_version_refs: Sequence[str] = (),
    thread_ref: str | None = None,
) -> str:
    """Return a content-bound action id for exactly one external send.

    The approval authority is intentionally bound to the exact message payload and
    provenance. Any later follow-up or edited message receives a different action id.
    """
    batch_id = _clean_control_text("batch_id", batch_id, _MAX_ID)
    message_id = _clean_control_text("message_id", message_id, _MAX_ID)
    target = _clean_control_text("target", target, _MAX_ID)
    subject = _clean_control_text("subject", subject, _MAX_TEXT)
    body = _clean_message_body(body)
    if thread_ref is not None:
        thread_ref = _clean_control_text("thread_ref", thread_ref, _MAX_ID)

    refs = []
    for ref in source_version_refs:
        refs.append(_clean_control_text("source_version_ref", ref, _MAX_ID))

    payload: Mapping[str, object] = {
        "batch_id": batch_id,
        "message_id": message_id,
        "target": target,
        "subject": subject,
        "body": body,
        "thread_ref": thread_ref,
        "source_version_refs": refs,
    }
    digest = sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"external-send:{batch_id}:{message_id}:{digest}"


def authorize_exact_send(*, action_id: str, approval: ExactSendApproval | None) -> ExactSendDecision:
    """Fail closed unless approval matches this exact send action id."""
    try:
        action_id = _clean_control_text("action_id", action_id, _MAX_TEXT)
    except ValueError as exc:
        return ExactSendDecision(False, False, "", str(exc))

    if approval is None:
        return ExactSendDecision(False, True, action_id, "exact send requires human approval")
    if not isinstance(approval, ExactSendApproval):
        return ExactSendDecision(False, True, action_id, "approval must be ExactSendApproval")
    if not isinstance(approval.approved, bool):
        return ExactSendDecision(False, True, action_id, "approval.approved must be boolean")
    if approval.approved is not True:
        return ExactSendDecision(False, True, action_id, "send not approved")
    if approval.action_id != action_id:
        return ExactSendDecision(False, True, action_id, "approval is for a different exact send")
    return ExactSendDecision(True, False, action_id, "matching exact-send approval")
