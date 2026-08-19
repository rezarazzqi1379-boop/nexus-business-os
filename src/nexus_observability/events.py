from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Mapping, Sequence


EventType = Literal[
    "workflow_started",
    "workflow_finished",
    "evidence_read",
    "decision_recorded",
    "evaluation_completed",
    "promotion_decided",
    "tool_requested",
    "tool_completed",
    "approval_requested",
    "approval_decided",
    "guardrail_triggered",
    "external_action_requested",
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
    "evaluation_completed",
    "promotion_decided",
    "tool_requested",
    "tool_completed",
    "approval_requested",
    "approval_decided",
    "guardrail_triggered",
    "external_action_requested",
    "error",
}
_ALLOWED_RESULTS = {"success", "failure", "blocked", "unknown", "not_applicable"}
_ALLOWED_PRIVACY = {"metadata_only", "redacted"}
_ALLOWED_ATTRIBUTE_KEYS = {
    "case_id",
    "domain",
    "status",
    "reason_code",
    "system",
    "system_version",
    "harness_version",
    "count",
    "critical",
    "reversible",
}
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
    "price",
    "credential",
}


def _looks_sensitive_key(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_").replace(" ", "_")
    return any(fragment in normalized for fragment in _FORBIDDEN_ATTRIBUTE_FRAGMENTS)


@dataclass(frozen=True)
class TraceEvent:
    event_id: str
    trace_id: str
    occurred_at: str
    event_type: EventType
    actor: str
    result: EventResult
    privacy: EventPrivacy = "metadata_only"
    parent_event_id: str | None = None
    correlation_ref: str | None = None
    decision_ref: str | None = None
    eval_ref: str | None = None
    action_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()
    payload_ref: str | None = None
    attributes: Mapping[str, Scalar] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name, value in (
            ("event_id", self.event_id),
            ("trace_id", self.trace_id),
            ("occurred_at", self.occurred_at),
            ("actor", self.actor),
        ):
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
            ("decision_ref", self.decision_ref),
            ("eval_ref", self.eval_ref),
            ("action_ref", self.action_ref),
            ("payload_ref", self.payload_ref),
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
            normalized = key.strip().lower().replace("-", "_").replace(" ", "_")
            if _looks_sensitive_key(normalized):
                errors.append(f"attribute key is disallowed for privacy: {key}")
                continue
            if normalized not in _ALLOWED_ATTRIBUTE_KEYS:
                errors.append(f"attribute key is not in the metadata allowlist: {key}")
            if not isinstance(value, (str, int, float, bool, type(None))):
                errors.append(f"attribute value must be scalar: {key}")
            if isinstance(value, str) and ("\n" in value or len(value) > 200):
                errors.append(f"attribute string must remain compact metadata: {key}")

        if self.event_type == "evidence_read" and not self.evidence_refs:
            errors.append("evidence_read requires at least one evidence_ref")
        if self.event_type == "decision_recorded" and not self.decision_ref:
            errors.append("decision_recorded requires decision_ref")
        if self.event_type in {"evaluation_completed", "promotion_decided"} and not self.eval_ref:
            errors.append(f"{self.event_type} requires eval_ref")
        if self.event_type in {
            "approval_requested",
            "approval_decided",
            "external_action_requested",
        } and not self.action_ref:
            errors.append(f"{self.event_type} requires action_ref")
        return errors

    def to_dict(self) -> dict[str, object]:
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
            "decision_ref": self.decision_ref,
            "eval_ref": self.eval_ref,
            "action_ref": self.action_ref,
            "evidence_refs": list(self.evidence_refs),
            "payload_ref": self.payload_ref,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class TraceValidationResult:
    valid: bool
    errors: tuple[str, ...]
    root_event_ids: tuple[str, ...]
    terminal_event_ids: tuple[str, ...]


def validate_trace(events: Sequence[TraceEvent]) -> TraceValidationResult:
    if not events:
        return TraceValidationResult(False, ("trace must contain at least one event",), (), ())

    errors: list[str] = []
    event_ids = [event.event_id for event in events]
    if len(event_ids) != len(set(event_ids)):
        errors.append("trace cannot contain duplicate event_id values")

    trace_ids = {event.trace_id for event in events}
    if len(trace_ids) != 1:
        errors.append("all trace events must share exactly one trace_id")

    event_by_id = {event.event_id: event for event in events}
    children_by_parent: dict[str, list[str]] = {event.event_id: [] for event in events}
    for event in events:
        errors.extend(f"event[{event.event_id or '?'}]: {error}" for error in event.validate())
        if event.parent_event_id:
            if event.parent_event_id not in event_by_id:
                errors.append(f"event[{event.event_id or '?'}]: parent_event_id must reference an event in the same trace")
            else:
                children_by_parent[event.parent_event_id].append(event.event_id)

    visiting: set[str] = set()
    visited: set[str] = set()
    cycle_reported = False

    def visit(event_id: str) -> None:
        nonlocal cycle_reported
        if event_id in visited:
            return
        if event_id in visiting:
            if not cycle_reported:
                errors.append("trace parent links cannot contain a cycle")
                cycle_reported = True
            return
        visiting.add(event_id)
        parent_id = event_by_id[event_id].parent_event_id
        if parent_id and parent_id in event_by_id:
            visit(parent_id)
        visiting.remove(event_id)
        visited.add(event_id)

    for event_id in event_ids:
        visit(event_id)

    roots = tuple(event.event_id for event in events if not event.parent_event_id)
    if len(roots) != 1:
        errors.append("trace must contain exactly one root event")

    terminals = tuple(event.event_id for event in events if not children_by_parent.get(event.event_id))
    return TraceValidationResult(not errors, tuple(errors), roots, terminals)
