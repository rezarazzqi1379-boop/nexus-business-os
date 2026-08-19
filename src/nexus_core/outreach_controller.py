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
    """Exact external message proposed for one qualified target."""

    target_id: str
    subject: str
    body: str
    thread_ref: str | None = None


@dataclass(frozen=True)
class OutreachBatch:
    """Immutable, source-versioned unit that can be released with one approval.

    One-click approval is deliberately batch-scoped rather than blanket authorization.
    Any material mutation changes the digest and therefore invalidates prior approval.
    """

    batch_id: str
    campaign_ref: str
    created_at: str
    expires_at: str
    source_version_refs: tuple[str, ...]
    targets: tuple[OutreachTarget, ...]
    messages: tuple[PreparedMessage, ...]


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
    """Authorize only an exact, unexpired, immutable prepared batch.

    This is the enforcement point behind the proposed UI button. The approval must match
    the digest-derived action id. Editing a target/message/source version after review
    changes the digest, so stale or blanket approval cannot bleed into a new send.
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
    approved = tuple(message.target_id for message in batch.messages) if gate.allowed_now else ()
    return OutreachRelease(batch.batch_id, digest, action_id, gate, approved)


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
