from datetime import datetime, timedelta, timezone

import pytest

from nexus_core.critical_path_scheduler import TaskNode, schedule_waves
from nexus_core.latency_telemetry import (
    ConnectorObservation,
    ingest_connector_observations,
    summarize_route,
)


def _obs(route: str, ms: int, ref: str, *, success: bool = True):
    start = datetime(2026, 8, 20, 0, 0, tzinfo=timezone.utc)
    return ConnectorObservation(
        route_id=route,
        started_at=start,
        finished_at=start + timedelta(milliseconds=ms),
        success=success,
        source_ref=ref,
    )


def test_observations_require_traceable_unique_evidence():
    with pytest.raises(ValueError, match="missing_source_ref"):
        ingest_connector_observations((_obs("gmail", 10, ""),))
    duplicate = (_obs("gmail", 10, "gmail:1"), _obs("gmail", 20, "gmail:1"))
    with pytest.raises(ValueError, match="duplicate_source_ref"):
        ingest_connector_observations(duplicate)


def test_observations_reject_naive_or_negative_time():
    naive = ConnectorObservation(
        "gmail",
        datetime(2026, 8, 20, 0, 0),
        datetime(2026, 8, 20, 0, 0, 1),
        True,
        "gmail:naive",
    )
    with pytest.raises(ValueError, match="naive_timestamp"):
        ingest_connector_observations((naive,))

    start = datetime(2026, 8, 20, 0, 0, 1, tzinfo=timezone.utc)
    negative = ConnectorObservation(
        "gmail", start, start - timedelta(milliseconds=1), True, "gmail:negative"
    )
    with pytest.raises(ValueError, match="negative_observed_duration"):
        ingest_connector_observations((negative,))


def test_measured_p95_replaces_static_estimate_when_sample_is_sufficient():
    samples = ingest_connector_observations(
        tuple(_obs("gmail", ms, f"gmail:{i}") for i, ms in enumerate((100, 120, 140, 160, 900), 1))
    )
    telemetry = summarize_route(samples)
    nodes = (
        TaskNode("gmail-read", (), 50, 1, route_id="gmail"),
        TaskNode("local", (), 400, 1),
    )
    plan = schedule_waves(nodes, max_parallel=1, telemetry={"gmail": telemetry})
    assert plan.waves[0] == ("gmail-read",)
    assert plan.estimated_critical_path_ms == 1300


def test_scheduler_keeps_static_estimate_when_observation_count_is_too_low():
    telemetry = summarize_route(
        ingest_connector_observations((_obs("gmail", 900, "gmail:1"),))
    )
    nodes = (TaskNode("gmail-read", (), 50, 1, route_id="gmail"),)
    plan = schedule_waves(nodes, telemetry={"gmail": telemetry}, minimum_samples=5)
    assert plan.estimated_critical_path_ms == 50
