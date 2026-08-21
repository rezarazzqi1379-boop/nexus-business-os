from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal, Sequence


ScheduleStatus = Literal["due", "not_due", "disabled"]


@dataclass(frozen=True)
class ScheduledCycle:
    schedule_id: str
    interval_seconds: int
    enabled: bool = True
    last_started_at: datetime | None = None


@dataclass(frozen=True)
class ScheduleDecision:
    schedule_id: str
    status: ScheduleStatus
    next_due_at: datetime | None
    reason: str


def _require_aware_utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def evaluate_schedule(schedule: ScheduledCycle, now: datetime) -> ScheduleDecision:
    """Decide whether one bounded autonomy cycle is due.

    This module only emits timing decisions. It never executes work and therefore
    cannot bypass the AutonomyPlan or action-specific human gates.
    """
    if not isinstance(schedule, ScheduledCycle):
        raise TypeError("schedule must be a ScheduledCycle")
    current = _require_aware_utc(now, "now")
    if not isinstance(schedule.schedule_id, str) or not schedule.schedule_id.strip():
        raise ValueError("schedule_id must be a nonblank string")
    if not isinstance(schedule.enabled, bool):
        raise ValueError("enabled must be a boolean")
    if (
        not isinstance(schedule.interval_seconds, int)
        or isinstance(schedule.interval_seconds, bool)
        or schedule.interval_seconds < 60
    ):
        raise ValueError("interval_seconds must be an integer of at least 60")

    if not schedule.enabled:
        return ScheduleDecision(schedule.schedule_id, "disabled", None, "schedule disabled")

    if schedule.last_started_at is None:
        return ScheduleDecision(schedule.schedule_id, "due", current, "schedule has never run")

    last = _require_aware_utc(schedule.last_started_at, "last_started_at")
    if last > current:
        raise ValueError("last_started_at cannot be in the future")
    next_due = last + timedelta(seconds=schedule.interval_seconds)
    if current >= next_due:
        return ScheduleDecision(schedule.schedule_id, "due", next_due, "interval elapsed")
    return ScheduleDecision(schedule.schedule_id, "not_due", next_due, "interval has not elapsed")


def due_schedule_ids(
    schedules: Sequence[ScheduledCycle],
    now: datetime,
) -> tuple[str, ...]:
    """Return due schedules deterministically in schedule_id order, failing closed."""
    decisions = [evaluate_schedule(schedule, now) for schedule in schedules]
    ids = [decision.schedule_id for decision in decisions]
    if len(ids) != len(set(ids)):
        raise ValueError("schedule_id values must be unique")
    return tuple(
        decision.schedule_id
        for decision in sorted(decisions, key=lambda value: value.schedule_id)
        if decision.status == "due"
    )
