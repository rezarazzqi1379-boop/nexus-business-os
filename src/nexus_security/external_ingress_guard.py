"""Validate untrusted inbound external content and gate any reply through the
canonical ApprovalStore -- never a second, parallel approval mechanism.

Two concerns:

1. Inbound external messages (email, WhatsApp, LinkedIn, SMS, etc.) are
   untrusted data. `ingest_external_message` sanitizes their metadata and
   hashes their content; `build_review_descriptor` turns that into a bounded
   review task that explicitly marks `external_action_authorized: False` --
   nothing here ever sends anything.

2. Any reply is a `send_external_message` consequential action. Instead of
   inventing a second, stateless approval object, `approval_request_for_reply`
   builds a real `approvals.ApprovalRequest`, scoped to the EXACT reviewed
   reply content, that goes through the existing `approvals.ApprovalStore`'s
   persistent, single-use `.request()` / `.decide()` / `.consume()` flow --
   the same store `autonomy.py`, `coordination_kit.py`, and
   `external_account_orchestrator.py` already use for every other
   consequential action in this codebase. A different reply body, subject,
   channel, or recipient produces a different `action_digest` and is a
   different, separately-gated action; the same approval can never be
   replayed against different content or consumed twice, because that
   enforcement lives in `ApprovalStore` itself, not reimplemented here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Literal
from unicodedata import category

from approvals import ApprovalRequest

ExternalChannel = Literal["email", "whatsapp", "linkedin", "sms", "other"]
_ALLOWED_CHANNELS = {"email", "whatsapp", "linkedin", "sms", "other"}
_DISALLOWED_METADATA_CATEGORIES = {"Cc", "Cf", "Zl", "Zp"}
_MAX_REF_LENGTH = 256
_MAX_THREAD_KEY_LENGTH = 256
_MAX_EXTERNAL_CONTENT_LENGTH = 100_000
_MAX_RECIPIENT_LENGTH = 512
_MAX_SUBJECT_LENGTH = 2048
_MAX_BODY_LENGTH = 50_000


def _validate_field(name: str, value: object, max_length: int, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    if not allow_empty and not value.strip():
        raise ValueError(f"{name} is required")
    if value != value.strip():
        raise ValueError(f"{name} cannot have leading or trailing whitespace")
    if len(value) > max_length:
        raise ValueError(f"{name} must be at most {max_length} characters")
    if any(category(ch) in _DISALLOWED_METADATA_CATEGORIES for ch in value):
        raise ValueError(f"{name} cannot contain control or formatting characters")
    return value


@dataclass(frozen=True)
class ExternalMessageIngress:
    source_ref: str
    thread_key: str
    content_sha256: str
    decision_relevant: bool
    external_reply_needed: bool
    raw_content: str = field(repr=False)


def ingest_external_message(
    *,
    source_ref: str,
    thread_key: str,
    raw_content: str,
    decision_relevant: bool,
    external_reply_needed: bool,
) -> ExternalMessageIngress:
    """Sanitize and hash one untrusted inbound external message."""
    source_ref = _validate_field("source_ref", source_ref, _MAX_REF_LENGTH)
    thread_key = _validate_field("thread_key", thread_key, _MAX_THREAD_KEY_LENGTH)
    if not isinstance(raw_content, str):
        raise ValueError("raw_content must be a string")
    if len(raw_content) > _MAX_EXTERNAL_CONTENT_LENGTH:
        raise ValueError(f"raw_content must be at most {_MAX_EXTERNAL_CONTENT_LENGTH} characters")
    if not isinstance(decision_relevant, bool):
        raise ValueError("decision_relevant must be a boolean")
    if not isinstance(external_reply_needed, bool):
        raise ValueError("external_reply_needed must be a boolean")
    return ExternalMessageIngress(
        source_ref,
        thread_key,
        sha256(raw_content.encode("utf-8")).hexdigest(),
        decision_relevant,
        external_reply_needed,
        raw_content,
    )


def build_review_descriptor(ingress: ExternalMessageIngress) -> dict[str, object]:
    """A bounded review task for a human/agent to draft from -- never a send."""
    if not isinstance(ingress, ExternalMessageIngress):
        raise ValueError("ingress must be an ExternalMessageIngress")
    return {
        "task_id": f"reply-review:{ingress.thread_key}",
        "source_ref": ingress.source_ref,
        "thread_key": ingress.thread_key,
        "content_sha256": ingress.content_sha256,
        "decision_relevant": ingress.decision_relevant,
        "external_reply_needed": ingress.external_reply_needed,
        "action_kind": "review_and_draft",
        "external_action_authorized": False,
    }


def approval_request_for_reply(
    ingress: ExternalMessageIngress,
    *,
    project_id: str,
    channel: ExternalChannel,
    recipient: str,
    subject: str,
    reviewed_body: str,
    requested_by: str,
    attachment_refs: tuple[str, ...] = (),
    ttl_seconds: int = 3600,
) -> ApprovalRequest:
    """Build a real, single-use ApprovalRequest scoped to this exact reply.

    The caller still has to take this through `approvals.ApprovalStore`:
    `.request()` to open it, a human `.decide()`, then `.consume()` against
    the returned request's `action_digest` right before the actual send.
    Nothing in this module authorizes or sends anything by itself.
    """
    if not isinstance(ingress, ExternalMessageIngress):
        raise ValueError("ingress must be an ExternalMessageIngress")
    if not isinstance(channel, str) or channel not in _ALLOWED_CHANNELS:
        raise ValueError("channel is invalid")
    project_id = _validate_field("project_id", project_id, _MAX_REF_LENGTH)
    recipient = _validate_field("recipient", recipient, _MAX_RECIPIENT_LENGTH)
    subject = _validate_field("subject", subject, _MAX_SUBJECT_LENGTH, allow_empty=True)
    reviewed_body = _validate_field("reviewed_body", reviewed_body, _MAX_BODY_LENGTH)
    requested_by = _validate_field("requested_by", requested_by, _MAX_REF_LENGTH)
    normalized_refs: list[str] = []
    for ref in attachment_refs:
        normalized_refs.append(_validate_field("attachment_ref", ref, _MAX_REF_LENGTH))
    if len(set(normalized_refs)) != len(normalized_refs):
        raise ValueError("attachment_refs cannot contain duplicates")
    return ApprovalRequest(
        project_id=project_id,
        action="send_external_message",
        target=recipient,
        parameters={
            "channel": channel,
            "subject": subject,
            "body": reviewed_body,
            "thread_key": ingress.thread_key,
            "source_content_sha256": ingress.content_sha256,
            "attachment_refs": normalized_refs,
        },
        requested_by=requested_by,
        ttl_seconds=ttl_seconds,
    )
