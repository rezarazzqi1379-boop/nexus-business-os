from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from nexus_brain.command import recommend_internal_actions
from nexus_brain.durable_queue import (
    DurableQueueError,
    IdempotencyConflictError,
    InMemoryDurableShadowQueue,
    QueueOwnershipError,
)
from nexus_brain.execution import build_read_only_execution_intent
from nexus_brain.execution_bridge import build_shadow_execution_envelope
from nexus_brain.live_snapshot import load_live_snapshot


NOW = datetime(2026, 8, 24, 9, 0, tzinfo=timezone.utc)
CREATED = "2026-08-24T08:50:00Z"


def envelope():
    graph, _ = load_live_snapshot("data/operational/live_evidence_snapshot_2026-08-24.json")
    rec = next(a for a in recommend_internal_actions(graph) if a.source_node_id == "LIVE-HYD-GH-REV12-ACK-20260823")
    intent = build_read_only_execution_intent(graph, rec, created_at=CREATED, payload={"mode": "normalize_against_rev_1_2"})
    return build_shadow_execution_envelope(graph, intent)


def test_duplicate_enqueue_is_idempotent():
    q = InMemoryDurableShadowQueue()
    e = envelope()
    first = q.enqueue(e)
    second = q.enqueue(e)
    assert first.run_id == second.run_id


def test_idempotency_rebind_fails_closed():
    q = InMemoryDurableShadowQueue()
    e = envelope()
    q.enqueue(e)
    with pytest.raises(IdempotencyConflictError):
        q.enqueue(replace(e, decision_ref="gmail:tampered"))


def test_claim_and_read_only_completion_require_current_lease_owner():
    q = InMemoryDurableShadowQueue()
    q.enqueue(envelope())
    claimed = q.claim_next("worker-a", now=NOW, lock_seconds=30)
    assert claimed and claimed.status == "RUNNING"
    with pytest.raises(QueueOwnershipError):
        q.complete_read_only(claimed.run_id, claimed.lease_token, "worker-b", "result:1", now=NOW)
    completed = q.complete_read_only(claimed.run_id, claimed.lease_token, "worker-a", "result:1", now=NOW)
    assert completed.status == "COMPLETED"
    assert completed.result_ref == "result:1"


def test_expired_lease_cannot_complete_and_is_recoverable():
    q = InMemoryDurableShadowQueue()
    q.enqueue(envelope())
    claimed = q.claim_next("worker-a", now=NOW, lock_seconds=10)
    later = NOW + timedelta(seconds=11)
    with pytest.raises(QueueOwnershipError):
        q.complete_read_only(claimed.run_id, claimed.lease_token, "worker-a", "late", now=later)
    recovered = q.recover_expired(now=later)
    assert len(recovered) == 1
    assert recovered[0].status == "PENDING"
    reclaimed = q.claim_next("worker-b", now=later, lock_seconds=30)
    assert reclaimed.run_id == claimed.run_id
    assert reclaimed.lease_token != claimed.lease_token
    assert reclaimed.task_version > claimed.task_version


def test_old_lease_is_fenced_after_recovery_and_reclaim():
    q = InMemoryDurableShadowQueue()
    q.enqueue(envelope())
    old = q.claim_next("worker-a", now=NOW, lock_seconds=5)
    later = NOW + timedelta(seconds=6)
    q.recover_expired(now=later)
    current = q.claim_next("worker-b", now=later, lock_seconds=30)
    with pytest.raises(QueueOwnershipError):
        q.complete_read_only(old.run_id, old.lease_token, "worker-a", "stale-result", now=later)
    assert q.complete_read_only(current.run_id, current.lease_token, "worker-b", "result:new", now=later).status == "COMPLETED"


def test_queue_has_no_path_for_consequential_or_external_envelope():
    q = InMemoryDurableShadowQueue()
    e = envelope()
    for bad in (
        replace(e, execution_class="CONSEQUENTIAL"),
        replace(e, external_effect=True),
        replace(e, approval_ref="approval:any"),
    ):
        with pytest.raises(DurableQueueError):
            q.enqueue(bad)


def test_naive_clock_and_invalid_lock_fail_closed():
    q = InMemoryDurableShadowQueue()
    q.enqueue(envelope())
    with pytest.raises(DurableQueueError):
        q.claim_next("worker", now=datetime(2026, 8, 24, 9, 0), lock_seconds=30)
    with pytest.raises(DurableQueueError):
        q.claim_next("worker", now=NOW, lock_seconds=0)
