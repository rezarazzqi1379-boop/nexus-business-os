"""Continuity and balanced-growth checks for the governed project portfolio."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from execution_scheduler import ExecutionLane, ExecutionSchedule, schedule_execution
from projects import ProjectPolicy


@dataclass(frozen=True)
class ProjectPulse:
    project_id: str
    observed_at: int
    last_progress_at: int
    open_needs: int
    evidence_ready: int
    risk: int


@dataclass(frozen=True)
class PortfolioWatch:
    schedule: ExecutionSchedule
    neglected_projects: tuple[str, ...]
    coverage: tuple[str, ...]


def watch_portfolio(policies: Iterable[ProjectPolicy], pulses: Iterable[ProjectPulse], *, now: int,
                    neglect_after: int = 604_800, concurrency: int = 4) -> PortfolioWatch:
    """Guarantee every known project has a visible running/queued/waiting lane."""
    policy_items, pulse_items = tuple(policies), tuple(pulses)
    if neglect_after < 1 or now < 0:
        raise ValueError("invalid_watch_window")
    if len({p.project_id for p in policy_items}) != len(policy_items):
        raise ValueError("duplicate_project_policy")
    pulse_by_id = {p.project_id: p for p in pulse_items}
    if len(pulse_by_id) != len(pulse_items):
        raise ValueError("duplicate_project_pulse")
    unknown = set(pulse_by_id) - {p.project_id for p in policy_items}
    if unknown:
        raise ValueError("unknown_project_pulse")

    lanes, neglected = [], []
    for policy in policy_items:
        pulse = pulse_by_id.get(policy.project_id)
        stale = pulse is None or now - pulse.last_progress_at > neglect_after
        if stale:
            neglected.append(policy.project_id)
        state = "waiting" if policy.status in {"hold", "blocked"} and not stale else "ready"
        evidence = pulse.evidence_ready if pulse else 0
        risk = pulse.risk if pulse else 1
        lanes.append(ExecutionLane(
            f"watch-{policy.project_id}", policy.project_id,
            "recovery" if stale else "research", state,
            min(5, max(0, round(policy.priority / 20))), 5 if stale else 2,
            min(5, max(0, evidence)), min(5, max(0, risk)), True,
        ))
    schedule = schedule_execution(lanes, concurrency=concurrency)
    coverage = tuple(sorted((*schedule.running, *schedule.queued, *schedule.waiting)))
    return PortfolioWatch(schedule, tuple(sorted(neglected)), coverage)

