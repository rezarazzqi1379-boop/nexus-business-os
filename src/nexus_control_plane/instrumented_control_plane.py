from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic_ns
from typing import Callable

from nexus_control_plane.control_plane import ControlPlane, WorkItem, WorkState
from nexus_control_plane.live_telemetry import TelemetryEvent, TelemetryKind, TelemetrySnapshot, summarize_telemetry


ClockMs = Callable[[], int]


def _default_clock_ms() -> int:
    return monotonic_ns() // 1_000_000


@dataclass
class InstrumentedControlPlane:
    """Observe ControlPlane runtime behavior without changing its decision authority."""

    control_plane: ControlPlane
    clock_ms: ClockMs = _default_clock_ms
    events: list[TelemetryEvent] = field(default_factory=list)
    _sequence: int = 0

    def _event_id(self, operation: str) -> str:
        self._sequence += 1
        return f"cp:{self._sequence}:{operation}"

    def _elapsed(self, start_ms: int) -> int:
        end_ms = self.clock_ms()
        return max(0, end_ms - start_ms)

    def submit(self, item: WorkItem) -> None:
        start = self.clock_ms()
        self.control_plane.submit(item)
        success = item.state not in {WorkState.BLOCKED, WorkState.REJECTED, WorkState.REVIEW}
        self.events.append(TelemetryEvent(
            event_id=self._event_id("submit"),
            project_id=item.project_id,
            kind=TelemetryKind.STATE_TRANSITION,
            operation=f"submit:{item.kind}:{item.state.value}",
            latency_ms=self._elapsed(start),
            success=success,
            evidence_refs=tuple(item.forge_preflight.evidence_refs) if item.forge_preflight is not None else (),
        ))

    def route(self, item_id: str) -> str | None:
        item = self.control_plane.work[item_id]
        before = item.state
        start = self.clock_ms()
        selected = self.control_plane.route(item_id)
        accepted = selected is not None and item.state is WorkState.RUNNING
        self.events.append(TelemetryEvent(
            event_id=self._event_id("route"),
            project_id=item.project_id,
            kind=TelemetryKind.DECISION,
            operation=f"route:{before.value}->{item.state.value}",
            latency_ms=self._elapsed(start),
            accepted_decision=accepted,
            success=accepted,
            decision_ref=f"work:{item.id}:agent:{selected}" if selected else None,
        ))
        return selected

    def complete(
        self,
        item_id: str,
        *,
        success: bool,
        quality: float,
        human_correction: bool = False,
        policy_violation: bool = False,
        notes: str = "",
    ) -> None:
        item = self.control_plane.work[item_id]
        before = item.state
        start = self.clock_ms()
        self.control_plane.complete(
            item_id,
            success=success,
            quality=quality,
            human_correction=human_correction,
            policy_violation=policy_violation,
            notes=notes,
        )
        self.events.append(TelemetryEvent(
            event_id=self._event_id("complete"),
            project_id=item.project_id,
            kind=TelemetryKind.HUMAN_OVERRIDE if human_correction else TelemetryKind.OUTCOME,
            operation=f"complete:{before.value}->{item.state.value}",
            latency_ms=self._elapsed(start),
            success=item.state is WorkState.DONE,
            human_override=human_correction,
            outcome_ref=f"work:{item.id}:{item.state.value}",
        ))

    def snapshot(self) -> TelemetrySnapshot:
        return summarize_telemetry(tuple(self.events))
