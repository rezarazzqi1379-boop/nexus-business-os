from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from unicodedata import category

from nexus_security.exact_external_gate import ExactExternalMessage

_MAX_REF_LENGTH = 256
_MAX_THREAD_KEY_LENGTH = 256
_MAX_EXTERNAL_CONTENT_LENGTH = 100_000
_DISALLOWED_METADATA_CATEGORIES = {"Cc", "Cf", "Zl", "Zp"}


@dataclass(frozen=True)
class ExternalMessageIngress:
    source_ref: str
    thread_key: str
    content_sha256: str
    decision_relevant: bool
    external_reply_needed: bool
    raw_content: str = field(repr=False)


def _validate_metadata(name: str, value: object, max_length: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} is required")
    if value != value.strip():
        raise ValueError(f"{name} cannot have leading or trailing whitespace")
    if len(value) > max_length:
        raise ValueError(f"{name} must be at most {max_length} characters")
    if any(category(ch) in _DISALLOWED_METADATA_CATEGORIES for ch in value):
        raise ValueError(f"{name} cannot contain control or formatting characters")
    return value


def ingest_external_message(*, source_ref: str, thread_key: str, raw_content: str, decision_relevant: bool, external_reply_needed: bool) -> ExternalMessageIngress:
    source_ref = _validate_metadata("source_ref", source_ref, _MAX_REF_LENGTH)
    thread_key = _validate_metadata("thread_key", thread_key, _MAX_THREAD_KEY_LENGTH)
    if not isinstance(raw_content, str):
        raise ValueError("raw_content must be a string")
    if len(raw_content) > _MAX_EXTERNAL_CONTENT_LENGTH:
        raise ValueError(f"raw_content must be at most {_MAX_EXTERNAL_CONTENT_LENGTH} characters")
    if not isinstance(decision_relevant, bool):
        raise ValueError("decision_relevant must be a boolean")
    if not isinstance(external_reply_needed, bool):
        raise ValueError("external_reply_needed must be a boolean")
    return ExternalMessageIngress(source_ref, thread_key, sha256(raw_content.encode("utf-8")).hexdigest(), decision_relevant, external_reply_needed, raw_content)


def build_review_descriptor(ingress: ExternalMessageIngress) -> dict[str, object]:
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


def build_exact_message_from_reviewed_payload(ingress: ExternalMessageIngress, *, message_id: str, channel: str, recipient: str, subject: str, reviewed_body: str, response_ref: str, attachment_refs: tuple[str, ...] = ()) -> ExactExternalMessage:
    if not isinstance(ingress, ExternalMessageIngress):
        raise ValueError("ingress must be an ExternalMessageIngress")
    response_ref = _validate_metadata("response_ref", response_ref, _MAX_REF_LENGTH)
    return ExactExternalMessage(
        message_id=message_id,
        channel=channel,
        recipient=recipient,
        subject=subject,
        body=reviewed_body,
        source_version_refs=(ingress.source_ref, f"content-sha256:{ingress.content_sha256}", response_ref),
        attachment_refs=attachment_refs,
    )
