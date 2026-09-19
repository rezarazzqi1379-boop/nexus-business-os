from datetime import datetime, timezone

import pytest

from nexus_core.settlement_executor import apply_settlement
from nexus_core.worker_lifecycle import SettlementDisposition, SettlementPlan


NOW = datetime(2026, 8, 29, 8, 0, tzinfo=timezone.utc)


class FakeStore:
    def __init__(self):
        self.calls = []

    def complete(self, work_id, worker_id):
        self.calls.append(("complete", work_id, worker_id))

    def fail(self, work_id, worker_id, error, *, now=None):
        self.calls.append(("fail", work_id, worker_id, error, now))
        return "queued"

    def defer(self, work_id, worker_id, reason, *, delay_seconds=60, now=None):
        self.calls.append(("defer", work_id, worker_id, reason, delay_seconds, now))
        return "queued"


def plan(disposition, *, complete=False, consume=False, reason="reason"):
    return SettlementPlan(disposition, complete, consume, (reason,))


def test_complete_requires_explicit_planner_permission():
    store = FakeStore()
    with pytest.raises(PermissionError):
        apply_settlement(store, "w1", "worker", plan(SettlementDisposition.COMPLETE), now=NOW)
    assert store.calls == []


def test_successful_complete_uses_complete_only():
    store = FakeStore()
    result = apply_settlement(
        store,
        "w1",
        "worker",
        plan(SettlementDisposition.COMPLETE, complete=True, consume=True),
        now=NOW,
    )
    assert result.mutated is True
    assert result.durable_status == "completed"
    assert store.calls == [("complete", "w1", "worker")]


def test_execution_retry_uses_failure_budget():
    store = FakeStore()
    result = apply_settlement(
        store,
        "w2",
        "worker",
        plan(SettlementDisposition.RETRY_EXECUTION, consume=True, reason="operation failed"),
        now=NOW,
    )
    assert result.durable_action == "fail"
    assert store.calls[0][0] == "fail"


def test_access_wait_uses_defer_not_fail_or_complete():
    store = FakeStore()
    result = apply_settlement(
        store,
        "w3",
        "worker",
        plan(SettlementDisposition.WAIT_ACCESS_REFRESH, reason="stale connector"),
        now=NOW,
        access_refresh_delay_seconds=90,
    )
    assert result.durable_action == "defer_access"
    assert store.calls[0][0] == "defer"
    assert store.calls[0][4] == 90
    assert "access_refresh" in store.calls[0][3]


def test_approval_wait_uses_defer_and_cannot_complete():
    store = FakeStore()
    result = apply_settlement(
        store,
        "w4",
        "worker",
        plan(SettlementDisposition.WAIT_EXACT_APPROVAL, reason="exact approval required"),
        now=NOW,
        approval_poll_delay_seconds=600,
    )
    assert result.durable_action == "defer_approval"
    assert store.calls[0][0] == "defer"
    assert store.calls[0][4] == 600
    assert "exact_approval" in store.calls[0][3]


def test_hold_is_deliberately_non_mutating():
    store = FakeStore()
    result = apply_settlement(store, "w5", "worker", plan(SettlementDisposition.HOLD), now=NOW)
    assert result.mutated is False
    assert result.durable_action == "hold_manual"
    assert store.calls == []


def test_missing_worker_or_work_id_fails_before_mutation():
    store = FakeStore()
    with pytest.raises(ValueError):
        apply_settlement(store, "", "worker", plan(SettlementDisposition.HOLD), now=NOW)
    with pytest.raises(ValueError):
        apply_settlement(store, "w", "", plan(SettlementDisposition.HOLD), now=NOW)
    assert store.calls == []
