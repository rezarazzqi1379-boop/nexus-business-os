from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Sequence
from unicodedata import category


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
_DISALLOWED_UNICODE_CATEGORIES = {"Cc", "Cf", "Zl", "Zp"}


def _metadata_errors(field_name: str, value: object, *, required: bool = False) -> list[str]:
    """Reject malformed metadata and covert free-form payload/log-injection channels."""

    errors: list[str] = []
    if not isinstance(value, str):
        errors.append(f"{field_name} must be a string")
        return errors
    if required and not value.strip():
        errors.append(f"{field_name} is required")
        return errors
    if not value:
        return errors
    if value != value.strip():
        errors.append(f"{field_name} cannot have leading or trailing whitespace")
    if len(value) > _MAX_METADATA_LENGTH:
        errors.append(f"{field_name} must be at most {_MAX_METADATA_LENGTH} characters")
    if any(category(character) in _DISALLOWED_UNICODE_CATEGORIES for character in value):
        errors.append(f"{field_name} cannot contain control or formatting characters")
    return errors


def _enum_error(field_name: str, value: object, allowed: set[str]) -> str | None:
    if not isinstance(value, str):
        return f"{field_name} must be a string"
    if value not in allowed:
        return f"{field_name} is unsupported"
    return None


@dataclass(frozen=True)
class AuditEvent:
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
        for field_name, value, allowed in (
            ("event_type", self.event_type, _ALLOWED_EVENT_TYPES),
            ("actor_type", self.actor_type, _ALLOWED_ACTOR_TYPES),
            ("result_class", self.result_class, _ALLOWED_RESULT_CLASSES),
            ("privacy_mode", self.privacy_mode, _ALLOWED_PRIVACY_MODES),
        ):
            error = _enum_error(field_name, value, allowed)
            if error:
                errors.append(error)
        if isinstance(self.occurred_at, str) and self.occurred_at.strip():
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
        if (
            isinstance(self.parent_event_id, str)
            and isinstance(self.event_id, str)
            and self.parent_event_id
            and self.parent_event_id == self.event_id
        ):
            errors.append("parent_event_id cannot reference the same event")
        if self.event_type in _ACTION_BOUND_EVENT_TYPES and (
            not isinstance(self.action_ref, str) or not self.action_ref.strip()
        ):
            errors.append(f"{self.event_type} requires action_ref")
        for field_name, refs in (
            ("evidence_refs", self.evidence_refs),
            ("correlation_refs", self.correlation_refs),
            ("tags", self.tags),
        ):
            if not isinstance(refs, tuple):
                errors.append(f"{field_name} must be a tuple")
                continue
            seen: set[str] = set()
            duplicate_found = False
            for value in refs:
                errors.extend(_metadata_errors(field_name, value, required=True))
                if isinstance(value, str):
                    if value in seen:
                        duplicate_found = True
                    seen.add(value)
            if duplicate_found:
                errors.append(f"{field_name} cannot contain duplicates")
        return errors


@dataclass(frozen=True)
class AuditTraceValidation:
    valid: bool
    errors: tuple[str, ...]


def validate_audit_trace(events: Sequence[AuditEvent]) -> AuditTraceValidation:
    errors: list[str] = []
    if not events:
        return AuditTraceValidation(False, ("at least one audit event is required",))
    by_id: dict[str, AuditEvent] = {}
    for index, event in enumerate(events):
        if not isinstance(event, AuditEvent):
            errors.append(f"event[{index}]: must be an AuditEvent")
            continue
        safe_event_id = event.event_id if isinstance(event.event_id, str) and event.event_id else "?"
        errors.extend(f"event[{safe_event_id}]: {error}" for error in event.validate())
        if isinstance(event.event_id, str) and event.event_id:
            if event.event_id in by_id:
                errors.append(f"duplicate event_id: {event.event_id}")
            else:
                by_id[event.event_id] = event
    valid_events = [event for event in events if isinstance(event, AuditEvent)]
    for event in valid_events:
        if not isinstance(event.parent_event_id, str) or not event.parent_event_id:
            continue
        parent = by_id.get(event.parent_event_id)
        if parent is None:
            errors.append(
                f"event[{event.event_id if isinstance(event.event_id, str) else '?'}]: "
                "parent_event_id must reference an event in the trace set"
            )
            continue
        if parent.trace_id != event.trace_id:
            errors.append(
                f"event[{event.event_id if isinstance(event.event_id, str) else '?'}]: "
                "parent_event_id must stay within the same trace_id"
            )
    for event in valid_events:
        if not isinstance(event.event_id, str) or event.event_id not in by_id:
            continue
        seen: set[str] = set()
        current = event
        while (
            isinstance(current.parent_event_id, str)
            and current.parent_event_id
            and current.parent_event_id in by_id
        ):
            if current.event_id in seen:
                errors.append(f"event[{event.event_id}]: parent chain contains a cycle")
                break
            seen.add(current.event_id)
            current = by_id[current.parent_event_id]
    return AuditTraceValidation(valid=not errors, errors=tuple(errors))
