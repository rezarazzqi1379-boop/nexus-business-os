import json

import pytest

from nexus_control_plane.live_telemetry import TelemetryEvent, TelemetryKind
from nexus_control_plane.telemetry_store import JsonlTelemetryStore, TelemetryStoreError


def _event(event_id="e1", *, success=True):
    return TelemetryEvent(
        event_id=event_id,
        project_id="KCL",
        kind=TelemetryKind.DECISION,
        operation="route",
        latency_ms=12,
        accepted_decision=success,
        success=success,
        decision_ref="work:w1:agent:a1" if success else None,
    )


def test_jsonl_store_round_trips_and_summarizes(tmp_path):
    path = tmp_path / "telemetry.jsonl"
    store = JsonlTelemetryStore(path)
    store.append(_event("e1"))
    store.append(_event("e2", success=False))

    events = store.read_all()
    assert [e.event_id for e in events] == ["e1", "e2"]
    snapshot = store.snapshot()
    assert snapshot.event_count == 2
    assert snapshot.accepted_decisions == 1


def test_jsonl_store_rejects_duplicate_event_id(tmp_path):
    store = JsonlTelemetryStore(tmp_path / "telemetry.jsonl")
    store.append(_event("dup"))
    with pytest.raises(TelemetryStoreError):
        store.append(_event("dup"))


def test_jsonl_store_fails_closed_on_corrupt_record(tmp_path):
    path = tmp_path / "telemetry.jsonl"
    path.write_text('{"event_id":"broken"}\n', encoding="utf-8")
    store = JsonlTelemetryStore(path)
    with pytest.raises(TelemetryStoreError):
        store.read_all()


def test_jsonl_store_does_not_silently_overwrite_existing_history(tmp_path):
    path = tmp_path / "telemetry.jsonl"
    store = JsonlTelemetryStore(path)
    store.append(_event("e1"))
    before = path.read_text(encoding="utf-8")

    with pytest.raises(TelemetryStoreError):
        store.append(_event("e1"))

    assert path.read_text(encoding="utf-8") == before
    parsed = json.loads(before.strip())
    assert parsed["event_id"] == "e1"
