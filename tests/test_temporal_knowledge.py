from datetime import datetime, timedelta, timezone

from nexus_core.temporal_knowledge import (
    TemporalFact,
    current_facts,
    is_valid_at,
    latest_observation,
    validate_temporal_fact,
)


def fact(fid: str, value: str, start: datetime, end: datetime | None, observed: datetime):
    return TemporalFact(
        fact_id=fid,
        subject="supplier:x",
        predicate="max_pressure",
        value=value,
        valid_from=start,
        valid_to=end,
        observed_at=observed,
        source_ref=f"source:{fid}",
    )


def test_recent_observation_is_not_automatically_current_truth():
    now = datetime(2026, 8, 19, tzinfo=timezone.utc)
    old = fact("old", "70 MPa", now - timedelta(days=30), now - timedelta(days=1), now)
    current = fact("current", "120 MPa", now - timedelta(days=1), None, now - timedelta(days=2))
    assert latest_observation((old, current)) == old
    assert current_facts((old, current), now=now) == (current,)


def test_invalid_or_naive_temporal_data_fails_closed():
    naive = datetime(2026, 8, 19)
    f = fact("x", "70 MPa", naive, None, naive)
    errors = validate_temporal_fact(f)
    assert "valid_from_must_be_timezone_aware" in errors
    assert "observed_at_must_be_timezone_aware" in errors
    assert not is_valid_at(f, datetime.now(timezone.utc))


def test_validity_window_is_half_open():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 2, 1, tzinfo=timezone.utc)
    f = fact("x", "A", start, end, start)
    assert is_valid_at(f, start)
    assert not is_valid_at(f, end)
