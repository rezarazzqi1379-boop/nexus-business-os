from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Literal, Sequence

from nexus_core.policy import ActionApproval, ActionIntent, GateDecision, evaluate_action


OutreachChannel = Literal["email", "linkedin", "whatsapp", "other"]
_MAX_TEXT = 2048
_MAX_BODY = 20_000
_MAX_FOLLOWUPS_PER_TARGET = 4
_MAX_FOLLOWUP_DELAY_HOURS = 24 * 30


@dataclass(frozen=True)
class OutreachTarget:
    """Qualified recipient candidate before any external message is authorized.

    The controller requires separate evidence for company fit, business need and a
    retrievable contact path. A name or social profile alone is intentionally not enough.
    """

    target_id: str
    company_name: str
    recipient: str
    role: str
    channel: OutreachChannel
    company_fit_refs: tuple[str, ...]
    need_evidence_refs: tuple[str, ...]
    contact_path_refs: tuple[str, ...]


@dataclass(frozen=True)
class PreparedMessage:
    """Exact first external message proposed for one qualified target."""

    target_id: str
    subject: str
    body: str
    thread_ref: str | None = None


@dataclass(frozen=True)
class PreparedFollowUp:
    """Pre-reviewed bounded follow-up step included in the same approval envelope.

    stop_on_reply is intentionally required to remain true by validation. A live reply is
    new evidence and must stop blind scheduled outreach rather than letting a sequence
    continue against an already-engaged counterparty.
    """

    target_id: str
    step: int
    wait_after_hours: int
    subject: str
    body: str
    stop_on_reply: bool = True


@dataclass(frozen=True)
class OutreachBatch:
    """Immutable, source-versioned unit that can be released with one approval.

    One-click approval is deliberately batch-scoped rather than blanket authorization.
    Any material mutation changes the digest and therefore invalidates prior approval.
    Optional follow-ups are exact, bounded and stop-on-reply; they are part of the same
    digest so one button may approve a finite pre-reviewed communication sequence.
    """

    batch_id: str
    campaign_ref: str
    created_at: str
    expires_at: str
    source_version_refs: tuple[str, ...]
    targets: tuple[OutreachTarget, ...]
    messages: tuple[PreparedMessage, ...]
    followups: tuple[PreparedFollowUp, ...] = ()


@dataclass(frozen=True)
class OutreachRelease:
    batch_id: str
    digest: str
    action_id: str
    gate: GateDecision
    approved_message_ids: tuple[str, ...]


def _parse_time(value: str) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _valid_text(value: object, *, max_length: int = _MAX_TEXT) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip() and len(value) <= max_length


def _valid_refs(refs: object) -> bool:
    return (
        isinstance(refs, tuple)
        and bool(refs)
        and all(_valid_text(ref) for ref in refs)
        and len(set(refs)) == len(refs)
    )


def validate_outreach_batch(batch: OutreachBatch) -> tuple[str, ...]:
    """Return fail-closed validation errors for a proposed outbound batch."""

    if not isinstance(batch, OutreachBatch):
        return ("batch must be an OutreachBatch",)

    errors: list[str] = []
    if not _valid_text(batch.batch_id): errors.append("batch_id is invalid")
    if not _valid_text(batch.campaign_ref): errors.append("campaign_ref is invalid")
    if not _valid_refs(batch.source_version_refs): errors.append("source_version_refs are invalid")

    created_at = _parse_time(batch.created_at)
    expires_at = _parse_time(batch.expires_at)
    if created_at is None: errors.append("created_at must be timezone-aware ISO-8601")
    if expires_at is None: errors.append("expires_at must be timezone-aware ISO-8601")
    if created_at is not None and expires_at is not None and expires_at <= created_at:
        errors.append("expires_at must be later than created_at")

    if not isinstance(batch.targets, tuple) or not batch.targets:
        errors.append("targets requires at least one target")
    if not isinstance(batch.messages, tuple) or not batch.messages:
        errors.append("messages requires at least one prepared message")
    if not isinstance(batch.followups, tuple):
        errors.append("followups must be a tuple")

    target_ids: set[str] = set()
    recipients: set[tuple[str, str]] = set()
    for target in batch.targets if isinstance(batch.targets, tuple) else ():
        if not isinstance(target, OutreachTarget):
            errors.append("targets must contain OutreachTarget values")
            continue
        if not _valid_text(target.target_id): errors.append("target_id is invalid")
        if target.target_id in target_ids: errors.append("duplicate target_id")
        target_ids.add(target.target_id)
        if not _valid_text(target.company_name): errors.append("company_name is invalid")
        if not _valid_text(target.recipient): errors.append("recipient is invalid")
        if not _valid_text(target.role): errors.append("role is invalid")
        if target.channel not in ("email", "linkedin", "whatsapp", "other"):
            errors.append("channel is invalid")
        recipient_key = (target.channel, target.recipient.casefold() if isinstance(target.recipient, str) else "")
        if recipient_key in recipients: errors.append("duplicate recipient/channel pair")
        recipients.add(recipient_key)
        if not _valid_refs(target.company_fit_refs): errors.append("company_fit_refs are invalid")
        if not _valid_refs(target.need_evidence_refs): errors.append("need_evidence_refs are invalid")
        if not _valid_refs(target.contact_path_refs): errors.append("contact_path_refs are invalid")

    message_target_ids: set[str] = set()
    for message in batch.messages if isinstance(batch.messages, tuple) else ():
        if not isinstance(message, PreparedMessage):
            errors.append("messages must contain PreparedMessage values")
            continue
        if not _valid_text(message.target_id): errors.append("message target_id is invalid")
        if message.target_id in message_target_ids: errors.append("duplicate message target_id")
        message_target_ids.add(message.target_id)
        if not _valid_text(message.subject): errors.append("subject is invalid")
        if not _valid_text(message.body, max_length=_MAX_BODY): errors.append("body is invalid")
        if message.thread_ref is not None and not _valid_text(message.thread_ref):
            errors.append("thread_ref is invalid")

    if target_ids and message_target_ids and target_ids != message_target_ids:
        errors.append("every target must have exactly one prepared message")

    followup_keys: set[tuple[str, int]] = set()
    followup_counts: dict[str, int] = {}
    last_step_by_target: dict[str, int] = {}
    last_delay_by_target: dict[str, int] = {}
    for followup in batch.followups if isinstance(batch.followups, tuple) else ():
        if not isinstance(followup, PreparedFollowUp):
            errors.append("followups must contain PreparedFollowUp values")
            continue
        if followup.target_id not in target_ids:
            errors.append("followup target_id must reference a batch target")
        if not isinstance(followup.step, int) or isinstance(followup.step, bool) or followup.step < 1:
            errors.append("followup step must be a positive integer")
        if (
            not isinstance(followup.wait_after_hours, int)
            or isinstance(followup.wait_after_hours, bool)
            or not 1 <= followup.wait_after_hours <= _MAX_FOLLOWUP_DELAY_HOURS
        ):
            errors.append("followup wait_after_hours is invalid")
        if followup.stop_on_reply is not True:
            errors.append("followups must stop_on_reply")
        if not _valid_text(followup.subject): errors.append("followup subject is invalid")
        if not _valid_text(followup.body, max_length=_MAX_BODY): errors.append("followup body is invalid")
        if isinstance(followup.step, int) and not isinstance(followup.step, bool):
            key = (followup.target_id, followup.step)
            if key in followup_keys: errors.append("duplicate followup target/step")
            followup_keys.add(key)
            followup_counts[followup.target_id] = followup_counts.get(followup.target_id, 0) + 1
            previous_step = last_step_by_target.get(followup.target_id, 0)
            if followup.step != previous_step + 1:
                errors.append("followup steps must be contiguous per target")
            last_step_by_target[followup.target_id] = followup.step
            if isinstance(followup.wait_after_hours, int) and not isinstance(followup.wait_after_hours, bool):
                previous_delay = last_delay_by_target.get(followup.target_id, 0)
                if followup.wait_after_hours <= previous_delay:
                    errors.append("followup delays must increase per target")
                last_delay_by_target[followup.target_id] = followup.wait_after_hours

    if any(count > _MAX_FOLLOWUPS_PER_TARGET for count in followup_counts.values()):
        errors.append("too many followups for one target")

    return tuple(errors)


def outreach_batch_digest(batch: OutreachBatch) -> str:
    """Hash all authorization-relevant fields in deterministic order."""

    payload = {
        "batch_id": batch.batch_id,
        "campaign_ref": batch.campaign_ref,
        "created_at": batch.created_at,
        "expires_at": batch.expires_at,
        "source_version_refs": list(batch.source_version_refs),
        "targets": [
            {
                "target_id": t.target_id,
                "company_name": t.company_name,
                "recipient": t.recipient,
                "role": t.role,
                "channel": t.channel,
                "company_fit_refs": list(t.company_fit_refs),
                "need_evidence_refs": list(t.need_evidence_refs),
                "contact_path_refs": list(t.contact_path_refs),
            }
            for t in batch.targets
        ],
        "messages": [
            {
                "target_id": m.target_id,
                "subject": m.subject,
                "body": m.body,
                "thread_ref": m.thread_ref,
            }
            for m in batch.messages
        ],
        "followups": [
            {
                "target_id": f.target_id,
                "step": f.step,
                "wait_after_hours": f.wait_after_hours,
                "subject": f.subject,
                "body": f.body,
                "stop_on_reply": f.stop_on_reply,
            }
            for f in batch.followups
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(encoded).hexdigest()


def outreach_action_id(batch: OutreachBatch) -> str:
    return f"outreach:{batch.batch_id}:{outreach_batch_digest(batch)}"


def preview_outreach_release(batch: OutreachBatch) -> OutreachRelease:
    """Create the exact one-click approval envelope without authorizing a send."""

    errors = validate_outreach_batch(batch)
    digest = outreach_batch_digest(batch)
    action_id = f"outreach:{batch.batch_id}:{digest}"
    if errors:
        gate = GateDecision(False, False, "; ".join(errors))
        return OutreachRelease(batch.batch_id, digest, action_id, gate, ())

    gate = evaluate_action(
        ActionIntent(
            action_id=action_id,
            kind="send_external_message",
            description=f"Release prepared outreach batch {batch.batch_id}",
            reversible=False,
        )
    )
    return OutreachRelease(batch.batch_id, digest, action_id, gate, ())


def authorize_outreach_release(
    batch: OutreachBatch,
    *,
    approval: ActionApproval,
    now: datetime | None = None,
) -> OutreachRelease:
    """Authorize only an exact, unexpired, immutable prepared batch/sequence.

    This is the enforcement point behind the proposed UI button. The approval must match
    the digest-derived action id. Editing a target, first message, follow-up, schedule or
    source version after review changes the digest, so stale or blanket approval cannot
    bleed into a new send sequence.
    """

    errors = validate_outreach_batch(batch)
    digest = outreach_batch_digest(batch)
    action_id = f"outreach:{batch.batch_id}:{digest}"
    if errors:
        return OutreachRelease(batch.batch_id, digest, action_id, GateDecision(False, False, "; ".join(errors)), ())

    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    expires_at = _parse_time(batch.expires_at)
    assert expires_at is not None
    if current >= expires_at:
        return OutreachRelease(batch.batch_id, digest, action_id, GateDecision(False, True, "outreach batch approval envelope expired"), ())

    gate = evaluate_action(
        ActionIntent(
            action_id=action_id,
            kind="send_external_message",
            description=f"Release prepared outreach batch {batch.batch_id}",
            reversible=False,
        ),
        approval=approval,
    )
    if not gate.allowed_now:
        return OutreachRelease(batch.batch_id, digest, action_id, gate, ())

    approved = [f"{message.target_id}:initial" for message in batch.messages]
    approved.extend(f"{followup.target_id}:followup:{followup.step}" for followup in batch.followups)
    return OutreachRelease(batch.batch_id, digest, action_id, gate, tuple(approved))


def qualified_targets(targets: Sequence[OutreachTarget]) -> tuple[OutreachTarget, ...]:
    """Keep only evidence-complete, de-duplicated candidates before drafting.

    This intentionally does not score by lead volume; candidates without fit, need and
    contact-path evidence are excluded rather than promoted into an outreach queue.
    """

    retained: list[OutreachTarget] = []
    seen: set[tuple[str, str]] = set()
    for target in targets:
        if not isinstance(target, OutreachTarget):
            continue
        if not (
            _valid_text(target.target_id)
            and _valid_text(target.company_name)
            and _valid_text(target.recipient)
            and _valid_text(target.role)
            and target.channel in ("email", "linkedin", "whatsapp", "other")
            and _valid_refs(target.company_fit_refs)
            and _valid_refs(target.need_evidence_refs)
            and _valid_refs(target.contact_path_refs)
        ):
            continue
        key = (target.channel, target.recipient.casefold())
        if key in seen:
            continue
        seen.add(key)
        retained.append(target)
    return tuple(retained)
