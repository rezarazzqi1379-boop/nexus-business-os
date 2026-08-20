from dataclasses import dataclass, field
from hashlib import sha256
from unicodedata import category

from nexus_core.autonomy import AutonomyPlan, plan_autonomy
from nexus_core.autonomy_adapters import inbox_reply_work_item
from nexus_core.capabilities import Capability
from nexus_core.policy import ActionIntent


_MAX_REF_LENGTH = 256
_MAX_THREAD_KEY_LENGTH = 256
_MAX_EXTERNAL_CONTENT_LENGTH = 100_000
_DISALLOWED_METADATA_CATEGORIES = {"Cc", "Cf", "Zl", "Zp"}


@dataclass(frozen=True)
class ExternalMessageIngress:
    """Untrusted message payload plus trusted connector metadata.

    The raw body is deliberately kept out of control-plane fields. It may be inspected
    later as evidence, but it cannot supply action kinds, capability IDs, approvals,
    permissions, reversibility, or other authorization metadata.
    """

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


def ingest_external_message(
    *,
    source_ref: str,
    thread_key: str,
    raw_content: str,
    decision_relevant: bool,
    external_reply_needed: bool,
) -> ExternalMessageIngress:
    """Ingest external text as evidence without allowing it to become control metadata."""

    source_ref = _validate_metadata("source_ref", source_ref, _MAX_REF_LENGTH)
    thread_key = _validate_metadata("thread_key", thread_key, _MAX_THREAD_KEY_LENGTH)
    if not isinstance(raw_content, str):
        raise ValueError("raw_content must be a string")
    if len(raw_content) > _MAX_EXTERNAL_CONTENT_LENGTH:
        raise ValueError(
            f"raw_content must be at most {_MAX_EXTERNAL_CONTENT_LENGTH} characters"
        )
    if not isinstance(decision_relevant, bool):
        raise ValueError("decision_relevant must be a boolean")
    if not isinstance(external_reply_needed, bool):
        raise ValueError("external_reply_needed must be a boolean")

    return ExternalMessageIngress(
        source_ref=source_ref,
        thread_key=thread_key,
        content_sha256=sha256(raw_content.encode("utf-8")).hexdigest(),
        decision_relevant=decision_relevant,
        external_reply_needed=external_reply_needed,
        raw_content=raw_content,
    )


def build_message_review_work_item(ingress: ExternalMessageIngress):
    """Create the review task strictly from trusted metadata, never from message text."""

    if not isinstance(ingress, ExternalMessageIngress):
        raise ValueError("ingress must be an ExternalMessageIngress")
    return inbox_reply_work_item(
        message_ref=ingress.source_ref,
        thread_key=ingress.thread_key,
        decision_relevant=ingress.decision_relevant,
        external_reply_needed=ingress.external_reply_needed,
    )


def plan_message_review(
    ingress: ExternalMessageIngress,
    capabilities: tuple[Capability, ...],
) -> AutonomyPlan:
    """Replay ingress through the canonical planner with no raw-content control path."""

    return plan_autonomy((build_message_review_work_item(ingress),), capabilities)


def build_external_send_intent(*, thread_key: str, response_ref: str) -> ActionIntent:
    """Build a consequential send intent only from trusted internal references.

    Untrusted supplier/customer/model content never supplies the action kind or approval.
    The canonical policy layer must still require exact-action human approval.
    """

    thread_key = _validate_metadata("thread_key", thread_key, _MAX_THREAD_KEY_LENGTH)
    response_ref = _validate_metadata("response_ref", response_ref, _MAX_REF_LENGTH)
    action_suffix = sha256(response_ref.encode("utf-8")).hexdigest()[:16]
    return ActionIntent(
        action_id=f"external-send:{thread_key}:{action_suffix}",
        kind="send_external_message",
        description=f"Send the human-reviewed response referenced by {response_ref}",
        reversible=False,
    )
