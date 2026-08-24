import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from nexus_brain.command import recommend_internal_actions
from nexus_brain.durable_queue import IdempotencyConflictError, QueueOwnershipError
from nexus_brain.execution import build_read_only_execution_intent
from nexus_brain.execution_bridge import to_shadow_execution_envelope
from nexus_brain.fixtures import canonical_portfolio_graph
from nexus_brain.live import apply_live_evidence_signals
from nexus_brain.postgres_shadow_queue import PostgresShadowQueue
from nexus_brain.runtime_snapshot import load_manual_snapshot


DSN = os.getenv("NEXUS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="NEXUS_TEST_DATABASE_URL not configured")
NOW = datetime(2026, 8, 24, 9, 20, tzinfo=timezone.utc)
SNAPSHOT = "data/operational/live_evidence_snapshot_2026-08-24.json"


def env():
    graph = canonical_portfolio_graph()
    apply_live_evidence_signals(graph, load_manual_snapshot(SNAPSHOT))
    rec = next(a for a in recommend_internal_actions(graph) if a.source_node_id == "LIVE-HYD-GH-REV12-ACK-20260823")
    intent = build_read_only_execution_intent(
        graph,
        rec,
        created_at="2026-08-24T09:15:00Z",
        payload={"task": "postgres_shadow_probe", "read_only": True},
    )
    return to_shadow_execution_envelope(graph, intent)


@pytest.fixture
def queue():
    q = PostgresShadowQueue(DSN)
    q.migrate()
    with q.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE nexus_shadow_tasks")
    return q


def test_postgres_duplicate_enqueue_is_idempotent_and_rebind_fails(queue):
    e = env()
    first = queue.enqueue(e)
    second = queue.enqueue(e)
    assert first.run_id == second.run_id
    with pytest.raises(IdempotencyConflictError):
        queue.enqueue(replace(e, decision_ref="LIVE-HYD-TAMPERED"))


def test_postgres_claim_completion_and_lease_fencing(queue):
    initial = queue.enqueue(env())
    claimed = queue.claim_next("pg-worker-a", now=NOW, lock_seconds=30)
    assert claimed.run_id == initial.run_id
    with pytest.raises(QueueOwnershipError):
        queue.complete_read_only(claimed.run_id, claimed.lease_token, "pg-worker-b", "result:bad", now=NOW)
    completed = queue.complete_read_only(claimed.run_id, claimed.lease_token, "pg-worker-a", "result:ok", now=NOW)
    assert completed.status == "COMPLETED"
    assert queue.get(initial.run_id).result_ref == "result:ok"


def test_postgres_expired_lease_recovers_and_old_token_is_fenced(queue):
    queue.enqueue(env())
    old = queue.claim_next("pg-worker-a", now=NOW, lock_seconds=5)
    later = NOW + timedelta(seconds=6)
    recovered = queue.recover_expired(now=later)
    assert len(recovered) == 1
    current = queue.claim_next("pg-worker-b", now=later, lock_seconds=30)
    assert current.run_id == old.run_id
    assert current.lease_token != old.lease_token
    with pytest.raises(QueueOwnershipError):
        queue.complete_read_only(old.run_id, old.lease_token, "pg-worker-a", "result:stale", now=later)
    assert queue.complete_read_only(current.run_id, current.lease_token, "pg-worker-b", "result:new", now=later).status == "COMPLETED"
