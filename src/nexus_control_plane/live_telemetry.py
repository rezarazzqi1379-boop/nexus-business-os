from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TelemetryKind(str, Enum):
    DECISION = "decision"
    TOOL = "tool"
    RECOVERY = "recovery"
    STATE_TRANSITION = "state_transition"
    HUMAN_OVERRIDE = "human_override"
    OUTCOME = "outcome"


@dataclass(frozen=True)
class TelemetryEvent:
    event_id: str
    project_id: str
    kind: TelemetryKind
    operation: str
    latency_ms: int
    tool_calls: int = 0
    context_units: int = 0
    accepted_decision: bool = False
    success: bool = True
    human_override: bool = False
    recovered_failure: bool = False
    recoverable_failure: bool = False
    evidence_refs: tuple[str, ...] = ()
    decision_ref: str | None = None
    outcome_ref: str | None = None


@dataclass(frozen=True)
class TelemetrySnapshot:
    event_count: int
    accepted_decisions: int
    total_latency_ms: int
    mean_latency_ms: float
    total_tool_calls: int
    total_context_units: int
    human_overrides: int
    recoverable_failures: int
    recovered_failures: int
    successful_events: int

    @property
    def recovery_rate(self) -> float:
        return 1.0 if self.recoverable_failures == 0 else self.recovered_failures / self.recoverable_failures

    @property
    def tool_calls_per_accepted_decision(self) -> float:
        return 0.0 if self.accepted_decisions == 0 else self.total_tool_calls / self.accepted_decisions

    @property
    def context_units_per_accepted_decision(self) -> float:
        return 0.0 if self.accepted_decisions == 0 else self.total_context_units / self.accepted_decisions


def _clean(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def _valid_event(event: TelemetryEvent) -> bool:
    if not isinstance(event, TelemetryEvent):
        return False
    if not all(_clean(x) for x in (event.event_id, event.project_id, event.operation)):
        return False
    if not isinstance(event.kind, TelemetryKind):
        return False
    if not isinstance(event.latency_ms, int) or isinstance(event.latency_ms, bool) or event.latency_ms < 0:
        return False
    for field in ("tool_calls", "context_units"):
        value = getattr(event, field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            return False
    for field in ("accepted_decision", "success", "human_override", "recovered_failure", "recoverable_failure"):
        if not isinstance(getattr(event, field), bool):
            return False
    if not isinstance(event.evidence_refs, tuple) or any(not _clean(x) for x in event.evidence_refs):
        return False
    if len(set(event.evidence_refs)) != len(event.evidence_refs):
        return False
    if event.decision_ref is not None and not _clean(event.decision_ref):
        return False
    if event.outcome_ref is not None and not _clean(event.outcome_ref):
        return False
    if event.recovered_failure and not event.recoverable_failure:
        return False
    return True


def summarize_telemetry(events: tuple[TelemetryEvent, ...]) -> TelemetrySnapshot:
    """Aggregate observed telemetry without inferring missing events or business outcomes."""
    if not isinstance(events, tuple):
        raise TypeError("events must be a tuple")
    if any(not _valid_event(event) for event in events):
        raise ValueError("invalid telemetry event")
    ids = tuple(event.event_id for event in events)
    if len(set(ids)) != len(ids):
        raise ValueError("telemetry event ids must be unique")

    count = len(events)
    total_latency = sum(event.latency_ms for event in events)
    accepted = sum(1 for event in events if event.accepted_decision)
    return TelemetrySnapshot(
        event_count=count,
        accepted_decisions=accepted,
        total_latency_ms=total_latency,
        mean_latency_ms=0.0 if count == 0 else total_latency / count,
        total_tool_calls=sum(event.tool_calls for event in events),
        total_context_units=sum(event.context_units for event in events),
        human_overrides=sum(1 for event in events if event.human_override),
        recoverable_failures=sum(1 for event in events if event.recoverable_failure),
        recovered_failures=sum(1 for event in events if event.recovered_failure),
        successful_events=sum(1 for event in events if event.success),
    )
