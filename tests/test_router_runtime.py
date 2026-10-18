from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import sys

import pytest

from autonomy import WorkItem
from nexus_router_runtime import SyntheticRuntime, PROJECT
from nexus_agent_router_pilot import WorkRequest, synthetic_worker
from project_control_plane import WorkRequest as PlannedWork, build_coordination_plan


@pytest.fixture
def runtime(tmp_path):
    return SyntheticRuntime(tmp_path / "queue.db")


def result(item):
    return asdict(synthetic_worker(item.payload["role"])(
        WorkRequest(PROJECT, item.payload["task_id"], "Synthetic proof")))


def test_durable_vertical_and_replay(runtime):
    assert runtime.submit("proof", thread_id="test_thread")
    assert not runtime.submit("proof", thread_id="test_thread")
    assert runtime.drain() == 3
    assert runtime.review("proof") == "accepted"
    restarted = SyntheticRuntime(runtime.store.path)
    assert restarted.drain() == 0
    assert len([e for e in restarted.snapshot()["events"] if e["kind"] == "checkpoint"]) == 3
    assert restarted.review("proof") == "accepted"


@pytest.mark.parametrize("kwargs", [
    {"project_id": "OTHER"}, {"action": "SEND"}, {"authority": "SAFE"},
    {"approval_id": "forged"}, {"budget_units": 2}, {"budget_units": True},
    {"task_id": "../escape"}, {"thread_id": "../secret"},
])
def test_reject_before_submission(runtime, kwargs):
    with pytest.raises((ValueError, PermissionError)):
        runtime.submit(**{"task_id": "proof", **kwargs})
    assert runtime.snapshot()["tasks"] == []


def test_duplicate_conflict(runtime):
    runtime.submit("proof")
    with pytest.raises(ValueError):
        runtime.submit("proof", thread_id="different")


def test_queue_isolation(runtime):
    runtime.store.enqueue(WorkItem("foreign", "OTHER", "SEND", {}))
    runtime.store.enqueue(WorkItem("same_project_unsafe", PROJECT, "SEND", {}))
    runtime.submit("proof")
    assert runtime.drain() == 3
    item = runtime.store.claim_next("outside")
    assert item.work_id in {"foreign", "same_project_unsafe"}


def test_crash_reclaim_fencing_renewal(runtime):
    runtime.submit("proof")
    now = datetime.now(timezone.utc) + timedelta(seconds=1)
    old = runtime.claim("owner", now=now, lease_seconds=1)
    assert old is not None
    later = now + timedelta(seconds=2)
    # Same textual owner after restart still cannot reuse an old attempt token.
    new = runtime.claim("owner", now=later)
    assert new.work_id == old.work_id and new.attempt == 2
    with pytest.raises(PermissionError):
        runtime.finish(old, "owner", result(old), now=later)
    runtime.renew(new, "owner", now=later, seconds=60)
    runtime.finish(new, "owner", result(new), now=later)
    assert runtime.drain() == 2
    assert runtime.review("proof") == "accepted"


def test_expired_completion_and_renewal_rejected(runtime):
    runtime.submit("proof")
    now = datetime.now(timezone.utc) + timedelta(seconds=1)
    item = runtime.claim("owner", now=now, lease_seconds=1)
    with pytest.raises(PermissionError):
        runtime.finish(item, "owner", result(item), now=now + timedelta(seconds=2))
    with pytest.raises(PermissionError):
        runtime.renew(item, "owner", now=now + timedelta(seconds=2))


def test_partial_checkpoint_recovery(runtime):
    runtime.submit("proof")
    item = runtime.claim("owner")
    runtime.finish(item, "owner", result(item))
    assert runtime.review("proof") == "rejected"
    restarted = SyntheticRuntime(runtime.store.path)
    assert restarted.drain() == 2
    assert restarted.review("proof") == "accepted"


def test_invalid_evidence_is_atomic(runtime):
    runtime.submit("proof")
    item = runtime.claim("owner")
    for wrong in ({**result(item), "project_id": "OTHER"},
                  {**result(item), "evidence": ("https://wrong.example",)}):
        with pytest.raises(ValueError):
            runtime.finish(item, "owner", wrong)
    assert len(runtime.snapshot()["events"]) == 1
    runtime.finish(item, "owner", result(item))


def test_cancel_and_stop(runtime):
    runtime.submit("proof")
    item = runtime.claim("owner")
    runtime.cancel("proof")
    with pytest.raises(PermissionError):
        runtime.finish(item, "owner", result(item))
    assert runtime.drain() == 0
    runtime.submit("next")
    runtime.stop()
    assert runtime.claim("owner") is None
    assert SyntheticRuntime(runtime.store.path).snapshot()["stopped"]


def test_budget_retry_limit(runtime):
    runtime.submit("proof", budget_units=3)
    now = datetime.now(timezone.utc) + timedelta(seconds=1)
    item = runtime.claim("crashed", now=now, lease_seconds=1)
    runtime.claim("replacement", now=now + timedelta(seconds=2))
    row = next(x for x in runtime.snapshot()["tasks"] if x["work_id"] == item.work_id)
    assert row["status"] == "dead_letter" and row["attempts"] == 1
    assert runtime.review("proof") == "rejected"


def test_missing_connector_and_partial_capability_fail_closed():
    request = PlannedWork("proof", PROJECT, "Test", ("agent-runtime",), ("agents",), lane="research")
    assert ("proof", "no_safe_read_source") in build_coordination_plan((request,), ()).blocked
    request = replace(request, lane="engineering", required_capabilities=("agents", "unavailable_unique_capability"))
    assert ("proof", "no_qualified_agent") in build_coordination_plan((request,), ()).blocked


def test_independent_process_restart(runtime):
    runtime.submit("proof")
    code = "from pathlib import Path; from nexus_router_runtime import SyntheticRuntime; import sys; r=SyntheticRuntime(Path(sys.argv[1])); assert r.drain()==3"
    completed = subprocess.run([sys.executable, "-c", code, str(runtime.store.path)],
                               cwd=Path(__file__).resolve().parents[1], capture_output=True, timeout=20)
    assert completed.returncode == 0, completed.stderr.decode()
    assert SyntheticRuntime(runtime.store.path).review("proof") == "accepted"
    assert runtime.drain() == 0


def test_process_dies_after_claim(runtime):
    import time
    runtime.submit("proof")
    code = "from pathlib import Path; from nexus_router_runtime import SyntheticRuntime; import os,sys; r=SyntheticRuntime(Path(sys.argv[1])); assert r.claim('crash',lease_seconds=1); os._exit(23)"
    process = subprocess.run([sys.executable, "-c", code, str(runtime.store.path)],
                             cwd=Path(__file__).resolve().parents[1], capture_output=True, timeout=20)
    assert process.returncode == 23
    time.sleep(1.1)
    assert SyntheticRuntime(runtime.store.path).drain() == 3
    assert runtime.review("proof") == "accepted"
    assert sum(x["attempts"] for x in runtime.snapshot()["tasks"]) == 4


def test_concurrent_duplicate_submission(runtime):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as pool:
        inserted = list(pool.map(lambda _: runtime.submit("same"), range(6)))
    assert sum(inserted) == 1
    assert len(runtime.snapshot()["tasks"]) == 3


def test_killed_transaction_rolls_back(runtime):
    runtime.submit("proof")
    before = runtime.snapshot()
    code = "from pathlib import Path; from nexus_router_runtime import SyntheticRuntime; import os,sys; r=SyntheticRuntime(Path(sys.argv[1])); db=r.store._connect(); db.execute('BEGIN IMMEDIATE'); db.execute(\"UPDATE work_items SET status='completed'\"); os._exit(24)"
    process = subprocess.run([sys.executable, "-c", code, str(runtime.store.path)],
                             cwd=Path(__file__).resolve().parents[1], capture_output=True, timeout=20)
    assert process.returncode == 24
    assert runtime.snapshot() == before
    assert runtime.drain() == 3


def test_worker_failure_does_not_starve_other_tasks(runtime, monkeypatch):
    runtime.submit('bad'); runtime.submit('good')
    original=runtime.execute
    def execute(payload):
        if payload['task_id']=='bad' and payload['role']=='research':
            raise RuntimeError('PRIVATE_PROVIDER_RESPONSE_MUST_NOT_BE_RELAYED')
        return original(payload)
    monkeypatch.setattr(runtime,'execute',execute)
    assert runtime.drain()==5
    assert runtime.review('good')=='accepted'
    bad=next(row for row in runtime.snapshot()['tasks'] if row['work_id']=='router:bad:research')
    assert bad['status']=='queued' and bad['attempts']==1
    failures=[event for event in runtime.snapshot()['events'] if event['kind']=='failed']
    assert len(failures)==1
    assert 'PRIVATE_PROVIDER_RESPONSE' not in str(runtime.snapshot())


def test_failure_fenced_to_attempt_and_retry_limit(runtime):
    runtime.submit('proof')
    now=datetime.now(timezone.utc)+timedelta(seconds=1)
    old=runtime.claim('owner',now=now,lease_seconds=1)
    later=now+timedelta(seconds=2)
    current=runtime.claim('owner',now=later)
    with pytest.raises(PermissionError): runtime.fail(old,'owner',now=later)
    assert runtime.fail(current,'owner',now=later)=='queued'
    later+=timedelta(seconds=61)
    final=runtime.claim('owner',now=later)
    # Older untouched siblings fairly precede the delayed retry.
    while final.work_id!=old.work_id:
        runtime.finish(final,'owner',result(final),now=later)
        final=runtime.claim('owner',now=later)
    assert final.attempt==3 and final.work_id==old.work_id
    assert runtime.fail(final,'owner',now=later)=='dead_letter'


def test_cancel_prevents_failure_overwrite(runtime):
    runtime.submit('proof'); item=runtime.claim('owner'); runtime.cancel('proof')
    with pytest.raises(PermissionError): runtime.fail(item,'owner')
    assert all(row['status']=='cancelled' for row in runtime.snapshot()['tasks'])


def test_expired_failure_cannot_commit(runtime):
    runtime.submit('proof'); now=datetime.now(timezone.utc)+timedelta(seconds=1)
    item=runtime.claim('owner',now=now,lease_seconds=1)
    with pytest.raises(PermissionError): runtime.fail(item,'owner',now=now+timedelta(seconds=2))
    assert not any(e['kind']=='failed' for e in runtime.snapshot()['events'])


def test_failure_audit_and_transition_are_atomic(runtime,monkeypatch):
    runtime.submit('proof'); item=runtime.claim('owner')
    before=runtime.snapshot()
    def broken_event(*args): raise RuntimeError('simulated journal failure')
    monkeypatch.setattr(runtime,'_event',broken_event)
    with pytest.raises(RuntimeError): runtime.fail(item,'owner')
    assert runtime.snapshot()==before
