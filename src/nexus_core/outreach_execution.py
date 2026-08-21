from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Literal

from nexus_core.outreach_controller import OutreachBatch, PreparedFollowUp, PreparedMessage, validate_outreach_batch
from nexus_core.policy import ActionApproval, ActionIntent, GateDecision, evaluate_action


MessageKind = Literal["initial", "followup"]


@dataclass(frozen=True)
class ExactSendRelease:
    batch_id: str
    message_id: str
    action_id: str
    gate: GateDecision


def _exact_payload(batch: OutreachBatch, message_id: str) -> dict[str, object] | None:
    if message_id.endswith(":initial"):
        target_id = message_id.removesuffix(":initial")
        message = next((m for m in batch.messages if isinstance(m, PreparedMessage) and m.target_id == target_id), None)
        if message is None:
            return None
        return {"kind": "initial", "target_id": target_id, "subject": message.subject, "body": message.body, "thread_ref": message.thread_ref}

    marker = ":followup:"
    if marker in message_id:
        target_id, raw_step = message_id.rsplit(marker, 1)
        try:
            step = int(raw_step)
        except ValueError:
            return None
        followup = next((f for f in batch.followups if isinstance(f, PreparedFollowUp) and f.target_id == target_id and f.step == step), None)
        if followup is None:
            return None
        return {"kind": "followup", "target_id": target_id, "step": step, "wait_after_hours": followup.wait_after_hours, "subject": followup.subject, "body": followup.body, "stop_on_reply": followup.stop_on_reply}
    return None


def exact_send_action_id(batch: OutreachBatch, message_id: str) -> str:
    payload = _exact_payload(batch, message_id)
    if payload is None:
        return ""
    bound = {
        "batch_id": batch.batch_id,
        "campaign_ref": batch.campaign_ref,
        "source_version_refs": list(batch.source_version_refs),
        "message_id": message_id,
        "message": payload,
    }
    digest = sha256(json.dumps(bound, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
    return f"outreach-send:{batch.batch_id}:{message_id}:{digest}"


def authorize_exact_send(
    batch: OutreachBatch,
    *,
    message_id: str,
    approval: ActionApproval,
    now: datetime | None = None,
    reply_observed: bool = False,
) -> ExactSendRelease:
    """Authorize exactly one external message at execution time.

    Batch review never authorizes future sends. Each initial or follow-up has its own
    content-bound action id. Follow-ups fail closed when a reply has been observed.
    """
    errors = validate_outreach_batch(batch)
    if errors:
        return ExactSendRelease(getattr(batch, "batch_id", ""), message_id, "", GateDecision(False, False, "; ".join(errors)))
    if not isinstance(message_id, str) or not message_id.strip() or message_id != message_id.strip():
        return ExactSendRelease(batch.batch_id, "", "", GateDecision(False, False, "message_id is invalid"))
    if now is not None and (not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None):
        return ExactSendRelease(batch.batch_id, message_id, "", GateDecision(False, False, "now must be timezone-aware"))
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    expires_at = datetime.fromisoformat(batch.expires_at.replace("Z", "+00:00")).astimezone(timezone.utc)
    if current >= expires_at:
        return ExactSendRelease(batch.batch_id, message_id, "", GateDecision(False, True, "outreach batch expired"))
    payload = _exact_payload(batch, message_id)
    if payload is None:
        return ExactSendRelease(batch.batch_id, message_id, "", GateDecision(False, False, "message_id is not present in reviewed batch"))
    if payload.get("kind") == "followup" and reply_observed:
        return ExactSendRelease(batch.batch_id, message_id, "", GateDecision(False, True, "reply observed; follow-up requires fresh review"))
    action_id = exact_send_action_id(batch, message_id)
    gate = evaluate_action(ActionIntent(action_id=action_id, kind="send_external_message", description=f"Send exact reviewed outreach message {message_id}", reversible=False), approval=approval)
    return ExactSendRelease(batch.batch_id, message_id, action_id, gate)
