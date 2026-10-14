"""Real local process/SQLite fixtures; no network or external side effects."""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest

from autonomy import AutonomyStore, WorkItem
from approvals import ApprovalRequest, ApprovalStore
from src.nexus_core.project_memory import ProjectMemoryStore

NOW = datetime(2026, 10, 14, tzinfo=timezone.utc)


def test_memory_parallel_processes_keep_unique_ids_and_all_records(tmp_path):
    script = """
import sys,time
from pathlib import Path
from src.nexus_core.project_memory import ProjectMemoryStore
root=Path(sys.argv[1]); marker=Path(sys.argv[2]); store=ProjectMemoryStore(root)
deadline=time.monotonic()+15
while not marker.exists():
    if time.monotonic()>deadline: raise RuntimeError('start_timeout')
    time.sleep(.01)
for i in range(25):
    store.record('context',sys.argv[3]+':'+str(i),decided_by='fixture',project_id='SANDBOX')
"""
    marker = tmp_path / "start"
    workers = [subprocess.Popen([sys.executable, "-c", script, str(tmp_path / "memory"), str(marker), str(i)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE) for i in range(6)]
    marker.touch()
    for worker in workers:
        out, err = worker.communicate(timeout=30)
        assert worker.returncode == 0, err.decode(errors="replace")
    entries = ProjectMemoryStore(tmp_path / "memory").query()
    assert len(entries) == 150
    assert len({e.entry_id for e in entries}) == 150
    assert len({e.statement for e in entries}) == 150


def test_memory_supersession_preserves_source_bytes_and_project_scope(tmp_path):
    store = ProjectMemoryStore(tmp_path)
    first = store.record("decision", "old", decided_by="fixture", project_id="A")
    second = store.record("decision", "new", decided_by="fixture", project_id="A")
    before = (tmp_path / "decision.jsonl").read_bytes()
    store.supersede("decision", first.entry_id, superseded_by=second.entry_id)
    assert (tmp_path / "decision.jsonl").read_bytes() == before
    assert [e.statement for e in store.query(project_id="A", include_superseded=False)] == ["new"]
    other = store.record("decision", "other", decided_by="fixture", project_id="B")
    with pytest.raises(ValueError, match="cross_project"):
        store.supersede("decision", second.entry_id, superseded_by=other.entry_id)


def test_memory_duplicate_id_is_exclusive_across_store_instances(tmp_path):
    def record_once(_):
        try:
            ProjectMemoryStore(tmp_path).record("context", "one", decided_by="fixture", entry_id="same")
            return True
        except ValueError as exc:
            assert str(exc) == "duplicate_entry_id"
            return False
    with ThreadPoolExecutor(max_workers=6) as pool:
        outcomes = list(pool.map(record_once, range(6)))
    assert sum(outcomes) == 1
    assert len(ProjectMemoryStore(tmp_path).query()) == 1


def test_memory_crash_before_atomic_commit_recovers_previous_record(tmp_path):
    store = ProjectMemoryStore(tmp_path)
    store.record("context", "committed", decided_by="fixture")
    script = """
import os,sys
from pathlib import Path
from src.nexus_core.project_memory import ProjectMemoryStore
os.replace=lambda *a,**k: os._exit(23)
ProjectMemoryStore(Path(sys.argv[1])).record('context','uncommitted',decided_by='fixture')
"""
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path)], timeout=15)
    assert result.returncode == 23
    restarted = ProjectMemoryStore(tmp_path)
    assert [e.statement for e in restarted.query()] == ["committed"]
    restarted.record("context", "after restart", decided_by="fixture")
    assert len(restarted.query()) == 2


def test_queue_duplicate_replay_and_parallel_claim(tmp_path):
    store = AutonomyStore(tmp_path / "queue.db")
    item = WorkItem("one", "A", "read", {})
    assert store.enqueue(item, now=NOW)
    assert not store.enqueue(item, now=NOW)
    with ThreadPoolExecutor(max_workers=6) as pool:
        claimed = list(pool.map(lambda i: store.claim_next(str(i), now=NOW), range(6)))
    assert sum(x is not None for x in claimed) == 1
    owner = str(next(i for i, x in enumerate(claimed) if x is not None))
    store.complete("one", owner)
    assert AutonomyStore(store.path).claim_next("restart", now=NOW) is None
    assert not store.enqueue(item, now=NOW)


def test_queue_crashed_worker_lease_is_reclaimed_and_stale_owner_rejected(tmp_path):
    path = tmp_path / "queue.db"
    store = AutonomyStore(path)
    store.enqueue(WorkItem("one", "A", "read", {}), now=NOW)
    script = """
import os,sys
from pathlib import Path
from datetime import datetime,timezone
from autonomy import AutonomyStore
x=AutonomyStore(Path(sys.argv[1])).claim_next('dead',lease_seconds=1,now=datetime(2026,10,14,tzinfo=timezone.utc))
os._exit(23 if x else 24)
"""
    assert subprocess.run([sys.executable, "-c", script, str(path)], timeout=15).returncode == 23
    assert store.claim_next("early", now=NOW) is None
    recovered = AutonomyStore(path).claim_next("new", now=NOW + timedelta(seconds=2))
    assert recovered.work_id == "one" and recovered.attempt == 2
    with pytest.raises(PermissionError):
        store.complete("one", "dead")
    store.complete("one", "new")


def test_approval_is_exact_single_use_and_project_bound(tmp_path):
    store = ApprovalStore(tmp_path / "approvals.db")
    request = ApprovalRequest("A", "send", "fixture", {"text": "first"}, "fixture")
    approval = store.request(request, now=NOW)
    assert not store.consume(approval, action_digest=request.action_digest, now=NOW)
    store.decide(approval, approved=True, decided_by="fixture", now=NOW)
    wrong = ApprovalRequest("B", "send", "fixture", {"text": "first"}, "fixture")
    assert not store.consume(approval, action_digest=wrong.action_digest, now=NOW)
    changed = ApprovalRequest("A", "send", "fixture", {"text": "changed"}, "fixture")
    assert not store.consume(approval, action_digest=changed.action_digest, now=NOW)
    with ThreadPoolExecutor(max_workers=6) as pool:
        consumed = list(pool.map(lambda _: store.consume(approval, action_digest=request.action_digest, now=NOW), range(6)))
    assert sum(consumed) == 1


def test_crash_after_guarded_local_effect_does_not_replay_effect(tmp_path):
    queue_path, approval_path, effect = tmp_path / "queue.db", tmp_path / "approval.db", tmp_path / "effect.txt"
    queue = AutonomyStore(queue_path)
    queue.enqueue(WorkItem("one", "A", "fixture_effect", {}), now=NOW)
    approvals = ApprovalStore(approval_path)
    request = ApprovalRequest("A", "fixture_effect", str(effect), {}, "fixture")
    approval = approvals.request(request, now=NOW)
    approvals.decide(approval, approved=True, decided_by="fixture", now=NOW)
    script = """
import os,sys
from pathlib import Path
from datetime import datetime,timezone
from autonomy import AutonomyStore
from approvals import ApprovalStore
now=datetime(2026,10,14,tzinfo=timezone.utc)
assert AutonomyStore(Path(sys.argv[1])).claim_next('dead',lease_seconds=1,now=now)
assert ApprovalStore(Path(sys.argv[2])).consume(sys.argv[4],action_digest=sys.argv[5],now=now)
with Path(sys.argv[3]).open('a') as f:
    f.write('effect\\n'); f.flush(); os.fsync(f.fileno())
os._exit(23)
"""
    child = subprocess.run([sys.executable, "-c", script, str(queue_path), str(approval_path),
                            str(effect), approval, request.action_digest], timeout=15)
    assert child.returncode == 23
    assert queue.claim_next("restart", now=NOW + timedelta(seconds=2))
    assert not ApprovalStore(approval_path).consume(approval, action_digest=request.action_digest, now=NOW)
    queue.complete("one", "restart")
    assert effect.read_text().splitlines() == ["effect"]


def test_missing_registry_and_master_blocks_consequential_bootstrap():
    from nexus_chat_bootstrap import ChatIntent, bootstrap_chat
    result = bootstrap_chat(intent=ChatIntent("fixture", "SANDBOX"), manifests=(),
                            snapshots=(), evidence=(), required_connectors=(), now=NOW.isoformat())
    assert result["gate"] == "BLOCK"
    assert not result["external_action_authorized"]
