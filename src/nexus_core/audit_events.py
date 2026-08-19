from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Sequence


AuditEventType = Literal[
    "evidence_observed",
    "decision_recorded",
    "evaluation_completed",
    "promotion_decided",
    "human_gate_evaluated",
    "action_attempted",
]
AuditActorType = Literal["system", "human", "external_source"]
AuditResultClass = Literal[
    "observed",
    "accepted",
    "blocked",
    "failed",
    "passed",
    "unknown",
]
PrivacyMode = Literal["metadata_only", "sensitive_omitted"]

_ALLOWED_EVENT_TYPES = {
    "evidence_observed",
    "decision_recorded",
    "evaluation_completed",
    "promotion_decided",
    "human_gate_evaluated",
    "action_attempted",
}
_ALLOWED_ACTOR_TYPES = {"system", "human", "external_source"}
_ALLOWED_RESULT_CLASSES = {
    "observed",
    "accepted",
    "blocked",
    "failed",
    "passed",
    "unknown",
}
_ALLOWED_PRIVACY_MODES = {"metadata_only", "sensitive_omitted"}
_ACTION_BOUND_EVENT_TYPES = {"human_gate_evaluated", "action_attempted"}
_MAX_METADATA_LENGTH = 256


def _metadata_errors(field_name: str, value: str, *, required: bool = False) -> list[str]:
    """Reject metadata that can become a covert free-form payload channel."""

    errors: list[str] = []
    if required and not value.strip():
        errors.append(f"{field_name} is required")
        return errors
    if not value:
        return errors
    if value != value.strip():
        errors.append(f"{field_name} cannot have leading or trailing whitespace")
    if len(value) > _MAX_METADATA_LENGTH:
        errors.append(f"{field_name} must be at most {_MAX_METADATA_LENGTH} characters")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        errors.append(f"{field_name} cannot contain control characters")
    return errors


@dataclass(frozen=True)
class AuditEvent:
    """Stable, provider-neutral audit metadata for one NEXUS control-plane event.

    v0.1 deliberately stores compact references and classifications only. It does
    not carry email bodies, prompts, model/tool payloads, contracts, pricing,
    credentials or other free-form sensitive content. Exporters may map this
    envelope to vendor tracing later without making that vendor schema canonical.
    """

    event_id: str
    trace_id: str
    event_type: AuditEventType
    occurred_at: str
    actor_type: AuditActorType
    subject_ref: str
    result_class: AuditResultClass
    privacy_mode: PrivacyMode = "metadata_only"
    parent_event_id: str = ""
    action_ref: str = ""
    evidence_refs: tuple[str, ...] = ()
    correlation_refs: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

    def validate(self) -> list[str]:
        errors: list[str] = []

        for name, value in (
            ("event_id", self.event_id),
            ("trace_id", self.trace_id),
            ("occurred_at", self.occurred_at),
            ("subject_ref", self.subject_ref),
        ):
            errors.extend(_metadata_errors(name, value, required=True))

        if self.event_type not in _ALLOWED_EVENT_TYPES:
            errors.append("event_type is unsupported")
        if self.actor_type not in _ALLOWED_ACTOR_TYPES:
            errors.append("actor_type is unsupported")
        if self.result_class not in _ALLOWED_RESULT_CLASSES:
            errors.append("result_class is unsupported")
        if self.privacy_mode not in _ALLOWED_PRIVACY_MODES:
            errors.append("privacy_mode is unsupported")

        if self.occurred_at.strip():
            try:
                parsed = datetime.fromisoformat(self.occurred_at.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    errors.append("occurred_at must include a timezone offset")
            except ValueError:
                errors.append("occurred_at must be ISO-8601")

        for name, value in (
            ("parent_event_id", self.parent_event_id),
            ("action_ref", self.action_ref),
        ):
            errors.extend(_metadata_errors(name, value))

        if self.parent_event_id and self.parent_event_id == self.event_id:
            errors.append("parent_event_id cannot reference the same event")

        if self.event_type in _ACTION_BOUND_EVENT_TYPES and not self.action_ref.strip():
            errors.append(f"{self.event_type} requires action_ref")

        for field_name, refs in (
            ("evidence_refs", self.evidence_refs),
            ("correlation_refs", self.correlation_refs),
            ("tags", self.tags),
        ):
            if len(refs) != len(set(refs)):
                errors.append(f"{field_name} cannot contain duplicates")
            for value in refs:
                errors.extend(_metadata_errors(field_name, value, required=True))

        return errors


@dataclass(frozen=True)
class AuditTraceValidation:
    valid: bool
    errors: tuple[str, ...]


def validate_audit_trace(events: Sequence[AuditEvent]) -> AuditTraceValidation:
    """Validate identity, parent links and acyclic ordering for one or more traces."""

    errors: list[str] = []
    if not events:
        return AuditTraceValidation(False, ("at least one audit event is required",))

    by_id: dict[str, AuditEvent] = {}
    for event in events:
        errors.extend(f"event[{event.event_id or '?'}]: {error}" for error in event.validate())
        if event.event_id in by_id:
            errors.append(f"duplicate event_id: {event.event_id}")
        else:
            by_id[event.event_id] = event

    for event in events:
        if not event.parent_event_id:
            continue
        parent = by_id.get(event.parent_event_id)
        if parent is None:
            errors.append(
                f"event[{event.event_id}]: parent_event_id must reference an event in the trace set"
            )
            continue
        if parent.trace_id != event.trace_id:
            errors.append(
                f"event[{event.event_id}]: parent_event_id must stay within the same trace_id"
            )

    # Detect cycles independently of event ordering. Missing parents were handled above.
    for event in events:
        seen: set[str] = set()
        current = event
        while current.parent_event_id and current.parent_event_id in by_id:
            if current.event_id in seen:
                errors.append(f"event[{event.event_id}]: parent chain contains a cycle")
                break
            seen.add(current.event_id)
            current = by_id[current.parent_event_id]

    return AuditTraceValidation(valid=not errors, errors=tuple(errors))
