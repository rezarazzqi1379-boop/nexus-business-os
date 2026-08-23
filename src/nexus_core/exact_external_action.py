from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Literal
from unicodedata import category

from nexus_core.policy import ActionApproval, ActionIntent, GateDecision, evaluate_action


ExternalChannel = Literal["email", "whatsapp", "linkedin", "sms", "other"]
_ALLOWED_CHANNELS = {"email", "whatsapp", "linkedin", "sms", "other"}
_DISALLOWED_METADATA_CATEGORIES = {"Cc", "Cf", "Zl", "Zp"}
_MAX_ID = 256
_MAX_RECIPIENT = 512
_MAX_SUBJECT = 2048
_MAX_BODY = 50_000
_MAX_REF = 512


@dataclass(frozen=True)
class ExactExternalMessage:
    """One exact, reviewable external message.

    This primitive deliberately knows nothing about campaigns, schedulers, agents, or
    follow-up sequences. Those systems may prepare messages, but authorization is bound
    to this exact recipient/content/source snapshot at execution time.
    """

    message_id: str
    channel: ExternalChannel
    recipient: str
    subject: str
    body: str
    source_version_refs: tuple[str, ...]
    attachment_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExactExternalRelease:
    action_id: str
    digest: str
    gate: GateDecision


def _text_error(name: str, value: object, *, max_length: int, allow_empty: bool = False) -> str | None:
    if not isinstance(value, str):
        return f"{name} must be a string"
    if not allow_empty and not value.strip():
        return f"{name} is required"
    if value != value.strip():
        return f"{name} cannot have leading or trailing whitespace"
    if len(value) > max_length:
        return f"{name} must be at most {max_length} characters"
    if any(category(ch) in _DISALLOWED_METADATA_CATEGORIES for ch in value):
        return f"{name} cannot contain control or formatting characters"
    return None


def _refs_error(name: str, refs: object, *, required: bool) -> str | None:
    if not isinstance(refs, tuple):
        return f"{name} must be a tuple"
    if required and not refs:
        return f"{name} requires at least one reference"

    normalized: list[str] = []
    for ref in refs:
        error = _text_error(name, ref, max_length=_MAX_REF)
        if error:
            return error
        normalized.append(ref)

    if len(set(normalized)) != len(normalized):
        return f"{name} cannot contain duplicates"
    return None


def validate_exact_external_message(message: ExactExternalMessage) -> tuple[str, ...]:
    if not isinstance(message, ExactExternalMessage):
        return ("message must be an ExactExternalMessage",)

    errors: list[str] = []
    for error in (
        _text_error("message_id", message.message_id, max_length=_MAX_ID),
        _text_error("recipient", message.recipient, max_length=_MAX_RECIPIENT),
        _text_error("subject", message.subject, max_length=_MAX_SUBJECT, allow_empty=True),
        _text_error("body", message.body, max_length=_MAX_BODY),
        _refs_error("source_version_refs", message.source_version_refs, required=True),
        _refs_error("attachment_refs", message.attachment_refs, required=False),
    ):
        if error:
            errors.append(error)

    if not isinstance(message.channel, str) or message.channel not in _ALLOWED_CHANNELS:
        errors.append("channel is invalid")
    return tuple(errors)


def exact_external_digest(message: ExactExternalMessage) -> str:
    errors = validate_exact_external_message(message)
    if errors:
        return ""
    payload = {
        "message_id": message.message_id,
        "channel": message.channel,
        "recipient": message.recipient,
        "subject": message.subject,
        "body": message.body,
        "source_version_refs": list(message.source_version_refs),
        "attachment_refs": list(message.attachment_refs),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(encoded).hexdigest()


def exact_external_action_id(message: ExactExternalMessage) -> str:
    digest = exact_external_digest(message)
    if not digest:
        return ""
    return f"external-send:{digest}"


def authorize_exact_external_message(
    message: ExactExternalMessage,
    *,
    approval: ActionApproval | None = None,
) -> ExactExternalRelease:
    """Evaluate authorization for exactly one content-bound external send.

    A prior campaign/batch/initial-message approval cannot authorize a different future
    message because any message-id, recipient, content, attachment, or source-version
    change produces a different action_id.
    """

    errors = validate_exact_external_message(message)
    if errors:
        return ExactExternalRelease("", "", GateDecision(False, False, "; ".join(errors)))

    digest = exact_external_digest(message)
    action_id = f"external-send:{digest}"
    gate = evaluate_action(
        ActionIntent(
            action_id=action_id,
            kind="send_external_message",
            description=f"Send exact reviewed external message {message.message_id}",
            reversible=False,
        ),
        approval=approval,
    )
    return ExactExternalRelease(action_id, digest, gate)
