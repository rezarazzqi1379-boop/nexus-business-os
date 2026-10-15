"""Bounded synthetic adapter over AutonomyStore; no providers or shell execution.

The event/checkpoint journal shares the existing queue database. All mutations
are fenced by project, lease owner, attempt and expiry. Not an external-effect
executor. A CLI process can drain persisted work without an interactive chat.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import sqlite3

from autonomy import AutonomyStore, WorkItem, utc_now
from contracts import canonical_digest
from project_control_plane import WorkRequest, build_coordination_plan
from nexus_agent_router_pilot import WorkRequest as PilotRequest, synthetic_worker
from agent_supervisor import AcceptanceContract, ArtifactClaim, Supervisor, TaskRecord

PROJECT = "PRJ-NEXUS-SANDBOX"
ACTION = "router.synthetic.v1"
ROLES = ("research", "reconciliation", "qa")


class SyntheticRuntime:
    def __init__(self, path: Path):
        self.store = AutonomyStore(path)
        with closing(self.store._connect()) as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS router_events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, project TEXT NOT NULL,
                    task TEXT NOT NULL, kind TEXT NOT NULL, body TEXT NOT NULL,
                    observed_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS router_control (
                    project TEXT PRIMARY KEY, stopped INTEGER NOT NULL);
            """)

    @staticmethod
    def _identity(value):
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value):
            raise ValueError("invalid_identity")

    @staticmethod
    def _event(db, task, kind, body, now):
        db.execute("INSERT INTO router_events(project,task,kind,body,observed_at) VALUES(?,?,?,?,?)",
                   (PROJECT, task, kind, json.dumps(body, sort_keys=True), now.isoformat()))

    def submit(self, task_id, *, project_id=PROJECT, thread_id="", action="SYNTHETIC_TEST",
               authority="SYNTHETIC_ONLY", budget_units=9, approval_id=None):
        self._identity(task_id)
        if thread_id:
            self._identity(thread_id)
        # An approval ID can never turn this sandbox into an external runner.
        if project_id != PROJECT or action != "SYNTHETIC_TEST" or authority != "SYNTHETIC_ONLY" or approval_id:
            raise PermissionError("scope_or_authority_blocked")
        if type(budget_units) is not int or not 3 <= budget_units <= 30:
            raise ValueError("budget_exhausted_or_unbounded")
        request = WorkRequest(task_id, PROJECT, "Synthetic research/reconciliation/QA",
                              ("agent-runtime",), ("agents",), lane="engineering", risk="read")
        plan = build_coordination_plan((request,), (), concurrency=3)
        if plan.blocked or plan.approval_required or len(plan.assignments) != 1:
            raise PermissionError("no_qualified_agent")
        # Catalog recommendation is provenance; implementation is the fixed
        # local synthetic worker, not an installed or healthy external agent.
        manifest = {"task_id": task_id, "thread_id": thread_id, "project_id": PROJECT,
                    "lane": "engineering", "risk": "read", "budget_units": budget_units,
                    "catalog": plan.assignments[0].agent_id, "authority": authority}
        digest = canonical_digest(manifest)
        now = utc_now()
        with closing(self.store._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                prior = db.execute("SELECT body FROM router_events WHERE project=? AND task=? AND kind='submitted'",
                                   (PROJECT, task_id)).fetchone()
                if prior:
                    if json.loads(prior[0])["digest"] != digest:
                        raise ValueError("duplicate_task_conflict")
                    db.commit()
                    return False
                self._event(db, task_id, "submitted", {"digest": digest, **manifest}, now)
                for role in ROLES:
                    payload = json.dumps({**manifest, "role": role}, sort_keys=True)
                    db.execute("INSERT INTO work_items VALUES(?,?,?,?,?,'queued',0,?,?,NULL,NULL,NULL)",
                               (f"router:{task_id}:{role}", PROJECT, ACTION, payload, 50,
                                min(3, budget_units // 3), now.isoformat()))
                db.commit()
            except Exception:
                db.rollback()
                raise
        return True

    def claim(self, owner, *, now=None, lease_seconds=30):
        self._identity(owner)
        current = now or utc_now()
        with closing(self.store._connect()) as db:
            stopped = db.execute("SELECT stopped FROM router_control WHERE project=?", (PROJECT,)).fetchone()
            if stopped and stopped[0]:
                return None
            # Exhausted crashed leases must become visible terminal failures.
            db.execute("UPDATE work_items SET status='dead_letter' WHERE project=? AND action=? "
                       "AND status='leased' AND lease_until<? AND attempts>=max_attempts",
                       (PROJECT, ACTION, current.isoformat()))
        return self.store.claim_next(owner, project=PROJECT, action=ACTION,
                                     lease_seconds=lease_seconds, now=current)

    def _fence(self, db, item, owner, now):
        row = db.execute("SELECT * FROM work_items WHERE work_id=? AND project=? AND action=? "
                         "AND status='leased' AND lease_owner=? AND attempts=? AND lease_until>?",
                         (item.work_id, PROJECT, ACTION, owner, item.attempt, now.isoformat())).fetchone()
        stopped = db.execute("SELECT stopped FROM router_control WHERE project=?", (PROJECT,)).fetchone()
        if row is None or (stopped and stopped[0]) or item.project != PROJECT:
            raise PermissionError("stale_lease_or_stopped")
        return json.loads(row["payload_json"])

    def renew(self, item, owner, *, now=None, seconds=30):
        if type(seconds) is not int or not 1 <= seconds <= 300:
            raise ValueError("invalid_renewal")
        current = now or utc_now()
        with closing(self.store._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                self._fence(db, item, owner, current)
                db.execute("UPDATE work_items SET lease_until=? WHERE work_id=?",
                           ((current + timedelta(seconds=seconds)).isoformat(), item.work_id))
                db.commit()
            except Exception:
                db.rollback()
                raise

    def finish(self, item, owner, result, *, now=None):
        current = now or utc_now()
        with closing(self.store._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                payload = self._fence(db, item, owner, current)
                expected = asdict(synthetic_worker(payload["role"])(
                    PilotRequest(PROJECT, payload["task_id"], "Synthetic proof")))
                # Full output binding; untrusted provider data is never accepted.
                if result != expected:
                    raise ValueError("malformed_or_cross_scope_evidence")
                self._event(db, payload["task_id"], "checkpoint", result, current)
                db.execute("UPDATE work_items SET status='completed',lease_owner=NULL,lease_until=NULL WHERE work_id=?",
                           (item.work_id,))
                db.commit()
            except Exception:
                db.rollback()
                raise

    def cancel(self, task_id):
        self._identity(task_id)
        with closing(self.store._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE work_items SET status='cancelled',lease_owner=NULL,lease_until=NULL "
                       "WHERE project=? AND action=? AND json_extract(payload_json,'$.task_id')=? "
                       "AND status IN ('queued','leased')", (PROJECT, ACTION, task_id))
            self._event(db, task_id, "cancelled", {}, utc_now())
            db.commit()

    def stop(self):
        with closing(self.store._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT OR REPLACE INTO router_control VALUES(?,1)", (PROJECT,))
            self._event(db, "control", "emergency_stop", {}, utc_now())
            db.commit()

    def drain(self, concurrency=3):
        if type(concurrency) is not int or not 1 <= concurrency <= 3:
            raise ValueError("invalid_concurrency")
        def worker(index):
            # Unique owner per process/thread; persisted attempts are fencing tokens.
            import uuid
            owner = f"worker_{index}_{uuid.uuid4().hex}"
            count = 0
            while (item := self.claim(owner)) is not None:
                payload = item.payload
                result = synthetic_worker(payload["role"])(PilotRequest(PROJECT, payload["task_id"], "Synthetic proof"))
                self.finish(item, owner, asdict(result))
                count += 1
            return count
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            return sum(pool.map(worker, range(concurrency)))

    def snapshot(self):
        return self.read_snapshot(self.store.path)

    @staticmethod
    def read_snapshot(path):
        # Console reads do not create databases, tables, leases or work.
        with closing(sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT work_id,status,attempts,lease_owner,lease_until FROM work_items "
                              "WHERE project=? AND action=? ORDER BY work_id LIMIT 300", (PROJECT, ACTION)).fetchall()
            events = db.execute("SELECT seq,task,kind,body,observed_at FROM router_events WHERE project=? "
                                "ORDER BY seq DESC LIMIT 300", (PROJECT,)).fetchall()
            stopped = db.execute("SELECT stopped FROM router_control WHERE project=?", (PROJECT,)).fetchone()
        return {"project_id": PROJECT, "maturity": "SYNTHETIC_NOT_PRODUCTION",
                "tasks": [dict(row) for row in rows], "events": [dict(row) for row in events],
                "stopped": bool(stopped and stopped[0]), "api_cost_usd": 0, "model_tokens": 0,
                "approval_policy": "DENY_EXTERNAL", "connector_health": "NOT_USED"}

    def review(self, task_id):
        self._identity(task_id)
        with closing(self.store._connect()) as db:
            rows = db.execute("SELECT body FROM router_events WHERE project=? AND task=? AND kind='checkpoint'",
                              (PROJECT, task_id)).fetchall()
        evidence = tuple(sorted(ref for row in rows for ref in json.loads(row[0])["evidence"]))
        required = tuple(sorted(f"synthetic://{PROJECT}/{task_id}/{role}" for role in ROLES))
        digest = canonical_digest({"project": PROJECT, "task": task_id})
        task = TaskRecord(task_id, AcceptanceContract(PROJECT, digest, (), required))
        supervisor = Supervisor()
        supervisor.observe(task, observation_id="aggregation", runner_state="done")
        # Zero required test claims: runtime completion is not test-suite proof.
        return supervisor.verify(task, ArtifactClaim(PROJECT, digest,
            json.dumps(evidence).encode(), evidence, ())).value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--submit")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--drain", action="store_true")
    args = parser.parse_args()
    runtime = SyntheticRuntime(args.db)
    if args.submit:
        runtime.submit(args.submit)
    if args.drain:
        runtime.drain(args.workers)
    print(json.dumps(runtime.snapshot(), sort_keys=True))


if __name__ == "__main__":
    main()
