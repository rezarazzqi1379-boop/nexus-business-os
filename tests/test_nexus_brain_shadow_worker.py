from dataclasses import replace
from datetime import datetime, timezone

import pytest

from nexus_brain.command import recommend_internal_actions
from nexus_brain.durable_queue import InMemoryDurableShadowQueue
from nexus_brain.execution import build_read_only_execution_intent
from nexus_brain.execution_bridge import to_shadow_execution_envelope
from nexus_brain.fixtures import canonical_portfolio_graph
from nexus_brain.live import apply_live_evidence_signals
from nexus_brain.runtime_snapshot import load_manual_snapshot
from nexus_brain.shadow_worker import ShadowWorker, ShadowWorkerError


NOW = datetime(2026, 8, 24, 9, 10, tzinfo=timezone.utc)
SNAPSHOT = "data/operational/live_evidence_snapshot_2026-08-24.json"


def env():
    graph = canonical_portfolio_graph()
    apply_live_evidence_signals(graph, load_manual_snapshot(SNAPSHOT))
    rec = next(a for a in recommend_internal_actions(graph) if a.source_node_id == "LIVE-HYD-GH-REV12-ACK-20260823")
    intent = build_read_only_execution_intent(
        graph,
        rec,
        created_at="2026-08-24T08:55:00Z",
        payload={"task": "normalize_supplier_reply", "read_only": True},
    )
    return to_shadow_execution_envelope(graph, intent)


def test_worker_completes_one_shadow_task_end_to_end():
    q = InMemoryDurableShadowQueue()
    e = env()
    q.enqueue(e)
    worker = ShadowWorker(q, "worker-1", lambda task: f"result:{task.envelope.task_id}")
    result = worker.run_once(now=NOW)
    assert result is not None
    assert result.project_id == "PRJ-HYD-01"
    assert result.task_id == e.task_id
    assert q.get(result.run_id).status == "COMPLETED"


def test_worker_returns_none_when_queue_is_empty():
    q = InMemoryDurableShadowQueue()
    worker = ShadowWorker(q, "worker-1", lambda task: "result:none")
    assert worker.run_once(now=NOW) is None


def test_executor_failure_does_not_forge_completion():
    q = InMemoryDurableShadowQueue()
    task = q.enqueue(env())

    def boom(_):
        raise RuntimeError("failed")

    worker = ShadowWorker(q, "worker-1", boom)
    with pytest.raises(ShadowWorkerError):
        worker.run_once(now=NOW, lock_seconds=5)
    assert q.get(task.run_id).status == "RUNNING"


def test_invalid_result_reference_fails_without_completion():
    q = InMemoryDurableShadowQueue()
    task = q.enqueue(env())
    worker = ShadowWorker(q, "worker-1", lambda _: " ")
    with pytest.raises(ShadowWorkerError):
        worker.run_once(now=NOW)
    assert q.get(task.run_id).status == "RUNNING"


def test_worker_rejects_mutated_external_envelope_even_if_injected():
    q = InMemoryDurableShadowQueue()
    good = env()
    task = q.enqueue(good)
    # simulate corrupted storage after ingress validation
    q._by_run[task.run_id] = replace(task, envelope=replace(good, external_effect=True))
    worker = ShadowWorker(q, "worker-1", lambda _: "result:x")
    with pytest.raises(ShadowWorkerError):
        worker.run_once(now=NOW)
