from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autonomy import AutonomyStore, WorkItem


NOW = datetime(2026, 8, 29, 8, 0, tzinfo=timezone.utc)


def item(work_id: str = "w-defer") -> WorkItem:
    return WorkItem(work_id, "PRJ-HYD-01", "connector_work", {"x": 1}, max_attempts=2)


def read_row(store: AutonomyStore, work_id: str):
    with sqlite3.connect(store.path) as db:
        db.row_factory = sqlite3.Row
        return db.execute("SELECT * FROM work_items WHERE work_id=?", (work_id,)).fetchone()


def test_defer_releases_lease_without_burning_attempt(tmp_path):
    store = AutonomyStore(tmp_path / "autonomy.db")
    assert store.enqueue(item(), now=NOW)
    claimed = store.claim_next("worker-1", now=NOW)
    assert claimed is not None and claimed.attempt == 1

    assert store.defer("w-defer", "worker-1", "waiting_access", delay_seconds=120, now=NOW) == "queued"
    row = read_row(store, "w-defer")
    assert row["status"] == "queued"
    assert row["attempts"] == 0
    assert row["lease_owner"] is None
    assert row["lease_until"] is None
    assert row["not_before"] == (NOW + timedelta(seconds=120)).isoformat()

    assert store.claim_next("worker-2", now=NOW + timedelta(seconds=119)) is None
    reclaimed = store.claim_next("worker-2", now=NOW + timedelta(seconds=120))
    assert reclaimed is not None
    assert reclaimed.attempt == 1


def test_repeated_waits_never_exhaust_retry_budget(tmp_path):
    store = AutonomyStore(tmp_path / "autonomy.db")
    assert store.enqueue(item(), now=NOW)
    current = NOW
    for idx in range(5):
        claimed = store.claim_next(f"worker-{idx}", now=current)
        assert claimed is not None
        assert claimed.attempt == 1
        store.defer("w-defer", f"worker-{idx}", "waiting_approval", delay_seconds=1, now=current)
        current += timedelta(seconds=1)
    row = read_row(store, "w-defer")
    assert row["attempts"] == 0
    assert row["status"] == "queued"


def test_wrong_worker_cannot_defer_another_workers_lease(tmp_path):
    store = AutonomyStore(tmp_path / "autonomy.db")
    assert store.enqueue(item(), now=NOW)
    assert store.claim_next("worker-1", now=NOW) is not None
    try:
        store.defer("w-defer", "worker-2", "steal", delay_seconds=10, now=NOW)
    except PermissionError as exc:
        assert "lease_owner_mismatch" in str(exc)
    else:
        raise AssertionError("wrong worker deferred another worker's lease")


def test_second_defer_after_release_fails_closed(tmp_path):
    store = AutonomyStore(tmp_path / "autonomy.db")
    assert store.enqueue(item(), now=NOW)
    assert store.claim_next("worker-1", now=NOW) is not None
    store.defer("w-defer", "worker-1", "waiting_access", delay_seconds=10, now=NOW)
    try:
        store.defer("w-defer", "worker-1", "duplicate", delay_seconds=10, now=NOW)
    except PermissionError as exc:
        assert "lease_owner_mismatch" in str(exc)
    else:
        raise AssertionError("duplicate defer unexpectedly succeeded")


def test_defer_rejects_non_positive_delay_without_mutation(tmp_path):
    store = AutonomyStore(tmp_path / "autonomy.db")
    assert store.enqueue(item(), now=NOW)
    assert store.claim_next("worker-1", now=NOW) is not None
    try:
        store.defer("w-defer", "worker-1", "bad", delay_seconds=0, now=NOW)
    except ValueError as exc:
        assert "invalid_defer_delay" in str(exc)
    else:
        raise AssertionError("zero-delay defer unexpectedly succeeded")
    row = read_row(store, "w-defer")
    assert row["status"] == "leased"
    assert row["attempts"] == 1
