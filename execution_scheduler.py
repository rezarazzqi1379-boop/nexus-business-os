from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ExecutionLane:
    work_id: str
    project_id: str
    lane: str
    state: str
    strategic_value: int
    urgency: int
    evidence_readiness: int
    risk: int
    reversible: bool


@dataclass(frozen=True)
class ExecutionSchedule:
    running: tuple[str, ...]
    queued: tuple[str, ...]
    waiting: tuple[str, ...]


_STATES = frozenset({"ready", "waiting", "blocked", "done"})
_LANES = frozenset({"recovery", "research", "engineering", "build", "commercial", "learning", "infrastructure", "sandbox"})


def _validate(item: ExecutionLane) -> None:
    if not item.work_id.strip() or not item.project_id.strip() or item.state not in _STATES or item.lane not in _LANES:
        raise ValueError("invalid_execution_lane")
    for value in (item.strategic_value, item.urgency, item.evidence_readiness, item.risk):
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 5:
            raise ValueError("invalid_execution_score")
    if not isinstance(item.reversible, bool):
        raise ValueError("invalid_reversibility")


def schedule_execution(items: Iterable[ExecutionLane], *, concurrency: int = 4) -> ExecutionSchedule:
    """Schedule bounded work across an unbounded active portfolio."""
    if not 1 <= concurrency <= 20:
        raise ValueError("invalid_concurrency")
    lanes = tuple(items)
    seen: set[str] = set()
    for item in lanes:
        _validate(item)
        if item.work_id in seen:
            raise ValueError("duplicate_work_id")
        seen.add(item.work_id)
    ready = [item for item in lanes if item.state == "ready"]
    ready.sort(key=lambda item: (
        -(item.strategic_value * 4 + item.urgency * 3 + item.evidence_readiness * 2 - item.risk * 3 + int(item.reversible)),
        item.project_id,
        item.work_id,
    ))
    running = tuple(item.work_id for item in ready[:concurrency])
    queued = tuple(item.work_id for item in ready[concurrency:])
    waiting = tuple(sorted(item.work_id for item in lanes if item.state in {"waiting", "blocked"}))
    return ExecutionSchedule(running, queued, waiting)
