from datetime import datetime, timedelta, timezone

import pytest

from nexus_autonomy.scheduler import ScheduledCycle, due_schedule_ids, evaluate_schedule


NOW = datetime(2026, 8, 21, 7, 30, tzinfo=timezone.utc)


def test_never_run_schedule_is_due() -> None:
    decision = evaluate_schedule(ScheduledCycle("research-hourly", 3600), NOW)
    assert decision.status == "due"
    assert decision.next_due_at == NOW


def test_schedule_is_not_due_before_interval() -> None:
    schedule = ScheduledCycle("research-hourly", 3600, last_started_at=NOW - timedelta(minutes=30))
    decision = evaluate_schedule(schedule, NOW)
    assert decision.status == "not_due"
    assert decision.next_due_at == NOW + timedelta(minutes=30)


def test_schedule_is_due_at_interval_boundary() -> None:
    schedule = ScheduledCycle("research-hourly", 3600, last_started_at=NOW - timedelta(hours=1))
    assert evaluate_schedule(schedule, NOW).status == "due"


def test_disabled_schedule_never_becomes_due() -> None:
    schedule = ScheduledCycle("research-hourly", 3600, enabled=False)
    assert evaluate_schedule(schedule, NOW).status == "disabled"


def test_naive_datetime_fails_closed() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        evaluate_schedule(ScheduledCycle("research-hourly", 3600), datetime(2026, 8, 21, 7, 30))


def test_future_last_started_at_fails_closed() -> None:
    schedule = ScheduledCycle("research-hourly", 3600, last_started_at=NOW + timedelta(seconds=1))
    with pytest.raises(ValueError, match="cannot be in the future"):
        evaluate_schedule(schedule, NOW)


def test_intervals_shorter_than_one_minute_are_rejected() -> None:
    with pytest.raises(ValueError, match="at least 60"):
        evaluate_schedule(ScheduledCycle("too-fast", 59), NOW)


def test_due_ids_are_unique_and_deterministic() -> None:
    schedules = (
        ScheduledCycle("z-news", 3600),
        ScheduledCycle("a-research", 3600),
    )
    assert due_schedule_ids(schedules, NOW) == ("a-research", "z-news")


def test_duplicate_schedule_ids_fail_closed() -> None:
    schedules = (
        ScheduledCycle("research", 3600),
        ScheduledCycle("research", 7200),
    )
    with pytest.raises(ValueError, match="must be unique"):
        due_schedule_ids(schedules, NOW)
