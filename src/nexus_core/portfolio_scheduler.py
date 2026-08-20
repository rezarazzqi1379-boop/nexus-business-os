from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class GoalLane(str, Enum):
    COMMERCIAL = "commercial"
    NETWORK = "network"
    ENGINEERING = "engineering"
    SECURITY = "security"
    RESEARCH = "research"
    LEARNING = "learning"
    FUTURE_INTELLIGENCE = "future_intelligence"
    BACKUP_RECOVERY = "backup_recovery"
    PERSONAL = "personal"


@dataclass(frozen=True)
class GoalWork:
    work_id: str
    goal_ref: str
    lane: GoalLane
    value: int
    urgency: int
    blocker: bool
    revenue_linked: bool
    evidence_strength: int
    estimated_cost: int
    last_progress_at: datetime
    runnable: bool = True


@dataclass(frozen=True)
class ScheduleDecision:
    selected: tuple[GoalWork, ...]
    deferred: tuple[GoalWork, ...]
    reasons: tuple[str, ...]


def validate_goal_work(work: GoalWork) -> tuple[str, ...]:
    errors: list[str] = []
    if not work.work_id.strip():
        errors.append("invalid_work_id")
    if not work.goal_ref.strip():
        errors.append("invalid_goal_ref")
    for name, value in {
        "value": work.value,
        "urgency": work.urgency,
        "evidence_strength": work.evidence_strength,
    }.items():
        if not isinstance(value, int) or not 0 <= value <= 5:
            errors.append(f"invalid_{name}")
    if not isinstance(work.estimated_cost, int) or work.estimated_cost < 0:
        errors.append("invalid_estimated_cost")
    if work.last_progress_at.tzinfo is None:
        errors.append("timezone_naive_last_progress_at")
    return tuple(errors)


def _priority_key(work: GoalWork, *, now: datetime, starvation_after: timedelta) -> tuple[int, ...]:
    starved = now - work.last_progress_at >= starvation_after
    # Blockers and revenue stay first, but starvation prevents research/security/backup
    # lanes from disappearing indefinitely under noisy commercial activity.
    return (
        int(work.blocker),
        int(work.revenue_linked),
        int(starved),
        work.urgency,
        work.value,
        work.evidence_strength,
        -work.estimated_cost,
    )


def schedule_portfolio(
    items: tuple[GoalWork, ...],
    *,
    now: datetime,
    max_parallel: int = 5,
    max_per_lane: int = 2,
    starvation_after: timedelta = timedelta(hours=24),
) -> ScheduleDecision:
    """Select a bounded parallel portfolio without collapsing into one noisy lane.

    Exploration can be broad, but execution capacity is finite. The scheduler keeps
    blocker/revenue work dominant while reserving room for compounding research,
    security, recovery and learning work when they have made no progress recently.
    """
    if now.tzinfo is None:
        raise ValueError("timezone_naive_now")
    if max_parallel <= 0 or max_per_lane <= 0:
        raise ValueError("invalid_capacity")

    valid: list[GoalWork] = []
    deferred: list[GoalWork] = []
    reasons: list[str] = []
    seen_ids: set[str] = set()

    for item in items:
        errors = validate_goal_work(item)
        if item.work_id in seen_ids:
            errors = (*errors, "duplicate_work_id")
        if errors or not item.runnable:
            deferred.append(item)
            reasons.extend(f"{item.work_id}:{e}" for e in errors)
            if not item.runnable:
                reasons.append(f"{item.work_id}:not_runnable")
            continue
        seen_ids.add(item.work_id)
        valid.append(item)

    ranked = sorted(valid, key=lambda w: _priority_key(w, now=now, starvation_after=starvation_after), reverse=True)
    selected: list[GoalWork] = []
    lane_counts: dict[GoalLane, int] = {}

    for item in ranked:
        if len(selected) >= max_parallel:
            deferred.append(item)
            continue
        if lane_counts.get(item.lane, 0) >= max_per_lane:
            deferred.append(item)
            reasons.append(f"{item.work_id}:lane_capacity")
            continue
        selected.append(item)
        lane_counts[item.lane] = lane_counts.get(item.lane, 0) + 1

    return ScheduleDecision(tuple(selected), tuple(deferred), tuple(reasons))
