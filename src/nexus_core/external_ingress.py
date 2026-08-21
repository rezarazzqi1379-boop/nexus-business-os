from dataclasses import dataclass, field
from hashlib import sha256
from unicodedata import category

from nexus_core.autonomy import AutonomyPlan, plan_autonomy
from nexus_core.autonomy_adapters import inbox_reply_work_item
from nexus_core.capabilities import Capability

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


def build_message_review_work_item(ingress: ExternalMessageIngress):
    if not isinstance(ingress, ExternalMessageIngress):
        raise ValueError("ingress must be an ExternalMessageIngress")
    return inbox_reply_work_item(
        message_ref=ingress.source_ref,
        thread_key=ingress.thread_key,
        decision_relevant=ingress.decision_relevant,
        external_reply_needed=ingress.external_reply_needed,
    )


def plan_message_review(ingress: ExternalMessageIngress, capabilities: tuple[Capability, ...]) -> AutonomyPlan:
    return plan_autonomy((build_message_review_work_item(ingress),), capabilities)
