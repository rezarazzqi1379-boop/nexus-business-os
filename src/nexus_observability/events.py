from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Literal


EventType = Literal[
    "workflow_started",
    "workflow_finished",
    "evidence_read",
    "decision_recorded",
    "tool_requested",
    "tool_completed",
    "approval_requested",
    "approval_decided",
    "guardrail_triggered",
    "error",
]
EventResult = Literal["success", "failure", "blocked", "unknown", "not_applicable"]
EventPrivacy = Literal["metadata_only", "redacted"]
Scalar = str | int | float | bool | None

_ALLOWED_EVENT_TYPES = {
    "workflow_started",
    "workflow_finished",
    "evidence_read",
    "decision_recorded",
    "tool_requested",
    "tool_completed",
    "approval_requested",
    "approval_decided",
    "guardrail_triggered",
    "error",
}
_ALLOWED_RESULTS = {"success", "failure", "blocked", "unknown", "not_applicable"}
_ALLOWED_PRIVACY = {"metadata_only", "redacted"}
_FORBIDDEN_ATTRIBUTE_FRAGMENTS = {
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "prompt",
    "completion",
    "email_body",
    "message_body",
    "raw_content",
    "attachment_content",
    "contract_text",
}


def _looks_sensitive_key(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_").replace(" ", "_")
    return any(fragment in normalized for fragment in _FORBIDDEN_ATTRIBUTE_FRAGMENTS)


@dataclass(frozen=True)
class TraceEvent:
    """Stable internal NEXUS event envelope.

    The envelope stores metadata and references, not raw commercial/model content.
    Exporters may later map this stable contract to OpenAI tracing,
    OpenTelemetry, or another observability system.
    """

    event_id: str
    trace_id: str
    occurred_at: str
    event_type: EventType
    actor: str
    result: EventResult
    privacy: EventPrivacy = "metadata_only"
    parent_event_id: str | None = None
    correlation_ref: str | None = None
    action_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()
    attributes: Mapping[str, Scalar] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []

        required = (
            ("event_id", self.event_id),
            ("trace_id", self.trace_id),
            ("occurred_at", self.occurred_at),
            ("actor", self.actor),
        )
        for name, value in required:
            if not value.strip():
                errors.append(f"{name} is required")

        if self.event_type not in _ALLOWED_EVENT_TYPES:
            errors.append("event_type is unsupported")
        if self.result not in _ALLOWED_RESULTS:
            errors.append("result is unsupported")
        if self.privacy not in _ALLOWED_PRIVACY:
            errors.append("privacy is unsupported")

        if self.parent_event_id is not None:
            if not self.parent_event_id.strip():
                errors.append("parent_event_id must be nonblank when provided")
            if self.parent_event_id == self.event_id:
                errors.append("event cannot be its own parent")

        for name, value in (
            ("correlation_ref", self.correlation_ref),
            ("action_ref", self.action_ref),
        ):
            if value is not None and not value.strip():
                errors.append(f"{name} must be nonblank when provided")

        for ref in self.evidence_refs:
            if not ref.strip():
                errors.append("evidence_refs must contain only nonblank refs")

        for key, value in self.attributes.items():
            if not isinstance(key, str) or not key.strip():
                errors.append("attribute keys must be nonblank strings")
                continue
            if _looks_sensitive_key(key):
                errors.append(f"attribute key is disallowed for privacy: {key}")
            if not isinstance(value, (str, int, float, bool, type(None))):
                errors.append(f"attribute value must be scalar: {key}")

        if self.event_type == "approval_requested" and not self.action_ref:
            errors.append("approval_requested requires action_ref")
        if self.event_type == "approval_decided" and not self.action_ref:
            errors.append("approval_decided requires action_ref")
        if self.event_type == "evidence_read" and not self.evidence_refs:
            errors.append("evidence_read requires at least one evidence_ref")

        return errors

    def to_dict(self) -> dict[str, object]:
        """Return a stable serialization without inventing vendor telemetry names."""

        return {
            "event_id": self.event_id,
            "trace_id": self.trace_id,
            "parent_event_id": self.parent_event_id,
            "occurred_at": self.occurred_at,
            "event_type": self.event_type,
            "actor": self.actor,
            "result": self.result,
            "privacy": self.privacy,
            "correlation_ref": self.correlation_ref,
            "action_ref": self.action_ref,
            "evidence_refs": list(self.evidence_refs),
            "attributes": dict(self.attributes),
        }
