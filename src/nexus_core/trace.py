from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence


TraceEventType = Literal[
    "evidence_observed",
    "decision_recorded",
    "evaluation_completed",
    "promotion_decided",
    "human_gate_evaluated",
    "external_action_requested",
]
ResultClass = Literal[
    "observed",
    "accepted",
    "rejected",
    "blocked",
    "passed",
    "failed",
    "unknown",
]
DataClassification = Literal[
    "public",
    "internal",
    "confidential",
    "restricted",
]

_ALLOWED_EVENT_TYPES = {
    "evidence_observed",
    "decision_recorded",
    "evaluation_completed",
    "promotion_decided",
    "human_gate_evaluated",
    "external_action_requested",
}
_ALLOWED_RESULT_CLASSES = {
    "observed",
    "accepted",
    "rejected",
    "blocked",
    "passed",
    "failed",
    "unknown",
}
_ALLOWED_DATA_CLASSIFICATIONS = {
    "public",
    "internal",
    "confidential",
    "restricted",
}


@dataclass(frozen=True)
class TraceEvent:
    """A stable, payload-light audit event for one NEXUS execution chain.

    The envelope stores references and classifications, not commercial/model payloads.
    `payload_ref` may point to an approved source-of-record when reconstruction is
    required; the sensitive payload itself is excluded by default.
    """

    event_id: str
    trace_id: str
    event_type: TraceEventType
    occurred_at: str
    subject_ref: str
    result_class: ResultClass
    evidence_refs: tuple[str, ...] = ()
    parent_event_id: str = ""
    decision_ref: str = ""
    eval_ref: str = ""
    action_ref: str = ""
    payload_ref: str = ""
    data_classification: DataClassification = "internal"
    sensitive_payload_included: bool = False

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name, value in (
            ("event_id", self.event_id),
            ("trace_id", self.trace_id),
            ("occurred_at", self.occurred_at),
            ("subject_ref", self.subject_ref),
        ):
            if not value.strip():
                errors.append(f"{name} is required")

        if self.event_type not in _ALLOWED_EVENT_TYPES:
            errors.append("event_type is unsupported")
        if self.result_class not in _ALLOWED_RESULT_CLASSES:
            errors.append("result_class is unsupported")
        if self.data_classification not in _ALLOWED_DATA_CLASSIFICATIONS:
            errors.append("data_classification is unsupported")

        if self.parent_event_id and self.parent_event_id == self.event_id:
            errors.append("parent_event_id cannot reference the same event")

        if any(not ref.strip() for ref in self.evidence_refs):
            errors.append("evidence_refs cannot contain blank references")

        if self.sensitive_payload_included:
            errors.append("sensitive payloads are forbidden in the canonical trace envelope")

        if self.event_type == "evidence_observed" and not self.evidence_refs:
            errors.append("evidence_observed requires at least one evidence_ref")
        if self.event_type == "decision_recorded" and not self.decision_ref.strip():
            errors.append("decision_recorded requires decision_ref")
        if self.event_type in {"evaluation_completed", "promotion_decided"} and not self.eval_ref.strip():
            errors.append(f"{self.event_type} requires eval_ref")
        if self.event_type in {"human_gate_evaluated", "external_action_requested"} and not self.action_ref.strip():
            errors.append(f"{self.event_type} requires action_ref")

        return errors


@dataclass(frozen=True)
class TraceValidationResult:
    valid: bool
    errors: tuple[str, ...]
    root_event_ids: tuple[str, ...]
    terminal_event_ids: tuple[str, ...]


def validate_trace(events: Sequence[TraceEvent]) -> TraceValidationResult:
    errors: list[str] = []
    if not events:
        return TraceValidationResult(
            valid=False,
            errors=("trace must contain at least one event",),
            root_event_ids=(),
            terminal_event_ids=(),
        )

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
                errors.append(
                    f"event[{event.event_id or '?'}]: parent_event_id must reference an event in the same trace"
                )
            else:
                children_by_parent[event.parent_event_id].append(event.event_id)

    # Detect cycles independently of input order. Parent links form a directed graph.
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(event_id: str) -> None:
        if event_id in visited:
            return
        if event_id in visiting:
            errors.append("trace parent links cannot contain a cycle")
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

    terminals = tuple(
        event.event_id
        for event in events
        if not children_by_parent.get(event.event_id)
    )

    return TraceValidationResult(
        valid=not errors,
        errors=tuple(errors),
        root_event_ids=roots,
        terminal_event_ids=terminals,
    )
