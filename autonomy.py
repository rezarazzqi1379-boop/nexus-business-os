from __future__ import annotations

from contextlib import closing

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


@dataclass(frozen=True)
class WorkItem:
    work_id: str
    project: str
    action: str
    payload: dict
    priority: int = 50
    max_attempts: int = 3


@dataclass(frozen=True)
class ClaimedWork:
    work_id: str
    project: str
    action: str
    payload: dict
    attempt: int
    lease_until: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AutonomyStore:
    """Durable work queue, budget ledger, and circuit breakers.

    Approval authority deliberately lives in the canonical ApprovalStore. This
    execution-state store must not create or interpret a second approval system.
    Existing legacy SQLite files may still contain an unused approval_inbox table;
    this code neither reads nor drops it.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db, db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS work_items (
                    work_id TEXT PRIMARY KEY, project TEXT NOT NULL, action TEXT NOT NULL,
                    payload_json TEXT NOT NULL, priority INTEGER NOT NULL, status TEXT NOT NULL,
                    attempts INTEGER NOT NULL, max_attempts INTEGER NOT NULL,
                    not_before TEXT NOT NULL, lease_owner TEXT, lease_until TEXT, last_error TEXT
                );
                CREATE TABLE IF NOT EXISTS usage_ledger (
                    usage_id TEXT PRIMARY KEY, project TEXT NOT NULL, cost_usd REAL NOT NULL,
                    occurred_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS circuit_breakers (
                    capability TEXT PRIMARY KEY, failures INTEGER NOT NULL, state TEXT NOT NULL,
                    opened_at TEXT
                );
                CREATE TABLE IF NOT EXISTS http_trials (
                    trial_id TEXT PRIMARY KEY, project TEXT NOT NULL, plan_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS http_attempts (
                    attempt_id TEXT PRIMARY KEY, trial_id TEXT NOT NULL,
                    tick INTEGER NOT NULL, source TEXT NOT NULL, reserved_at TEXT NOT NULL,
                    outcome TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS http_trial_evidence (
                    attempt_id TEXT PRIMARY KEY, evidence_json TEXT NOT NULL
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.execute("PRAGMA busy_timeout=5000")
        db.row_factory = sqlite3.Row
        return db

    def configure_http_trial(self, trial_id: str, project: str, *, sources: tuple[str, ...],
                             starts_at: datetime, interval_seconds: int = 300,
                             source_mode: str = "FROZEN_TEST_FIXTURE") -> None:
        """Freeze one three-tick/six-attempt experiment in the existing ledger."""
        if (not trial_id.strip() or not project.strip() or len(sources) != 2
                or len(set(sources)) != 2 or any(not s.strip() for s in sources)
                or starts_at.tzinfo is None or type(interval_seconds) is not int
                or not 300 <= interval_seconds <= 86400
                or source_mode not in {"FROZEN_TEST_FIXTURE", "REAL_PUBLIC_HTTP"}):
            raise ValueError("invalid_http_trial")
        plan = json.dumps(dict(sources=sorted(sources), starts_at=starts_at.astimezone(timezone.utc).isoformat(),
                               interval_seconds=interval_seconds, ticks=3, max_attempts=6,
                               source_mode=source_mode), sort_keys=True)
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT project,plan_json FROM http_trials WHERE trial_id=?", (trial_id,)).fetchone()
            if row and (row[0], row[1]) != (project, plan):
                raise ValueError("immutable_http_trial_conflict")
            if not row:
                db.execute("INSERT INTO http_trials VALUES (?,?,?)", (trial_id, project, plan))
            db.commit()

    def reserve_http_attempt(self, trial_id: str, project: str, *, tick: int,
                             source: str, now: datetime | None = None) -> str:
        """Commit before transport. A crash consumes its reservation; never refund."""
        import uuid
        current = now or utc_now()
        if current.tzinfo is None or type(tick) is not int or not 0 <= tick < 3:
            raise ValueError("invalid_http_tick")
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT project,plan_json FROM http_trials WHERE trial_id=?", (trial_id,)).fetchone()
            if not row or row[0] != project:
                raise PermissionError("http_trial_scope_denied")
            plan = json.loads(row[1])
            start = datetime.fromisoformat(plan["starts_at"]) + timedelta(seconds=tick * plan["interval_seconds"])
            if source not in plan["sources"] or not start <= current < start + timedelta(seconds=plan["interval_seconds"]):
                raise PermissionError("http_trial_source_or_window_denied")
            count = db.execute("SELECT COUNT(*) FROM http_attempts WHERE trial_id=?", (trial_id,)).fetchone()[0]
            if count >= plan["max_attempts"]:
                raise PermissionError("http_trial_budget_exhausted")
            identity = uuid.uuid4().hex
            db.execute("INSERT INTO http_attempts VALUES (?,?,?,?,?,'RESERVED_UNKNOWN')",
                       (identity, trial_id, tick, source, current.astimezone(timezone.utc).isoformat()))
            db.commit()
            return identity

    def finish_http_attempt(self, attempt_id: str, *, success: bool) -> None:
        if type(success) is not bool:
            raise ValueError("invalid_http_outcome")
        with closing(self._connect()) as db:
            db.execute("UPDATE http_attempts SET outcome=? WHERE attempt_id=? AND outcome='RESERVED_UNKNOWN'",
                       ("RESPONSE_RECEIVED" if success else "TRANSPORT_FAILED", attempt_id))

    def http_trial_attempts(self, trial_id: str, project: str) -> tuple[dict, ...]:
        with closing(self._connect()) as db:
            row = db.execute("SELECT project FROM http_trials WHERE trial_id=?", (trial_id,)).fetchone()
            if not row or row[0] != project:
                raise PermissionError("http_trial_scope_denied")
            return tuple(dict(r) for r in db.execute(
                "SELECT * FROM http_attempts WHERE trial_id=? ORDER BY reserved_at,attempt_id", (trial_id,)))

    def record_http_evidence(self, attempt_id: str, evidence: dict) -> None:
        payload = json.dumps(evidence, ensure_ascii=False, sort_keys=True)
        if len(payload.encode()) > 65536:
            raise ValueError("http_evidence_bounds")
        with closing(self._connect()) as db:
            row = db.execute("SELECT outcome FROM http_attempts WHERE attempt_id=?", (attempt_id,)).fetchone()
            if row is None or row[0] != "RESPONSE_RECEIVED":
                raise ValueError("http_evidence_without_response")
            db.execute("INSERT INTO http_trial_evidence VALUES (?,?)", (attempt_id, payload))

    def http_trial_evidence(self, trial_id: str, project: str) -> tuple[dict, ...]:
        self.http_trial_attempts(trial_id, project)  # Apply the same project binding.
        with closing(self._connect()) as db:
            return tuple(json.loads(r[0]) for r in db.execute(
                "SELECT e.evidence_json FROM http_trial_evidence e JOIN http_attempts a USING(attempt_id) "
                "WHERE a.trial_id=? ORDER BY a.reserved_at,a.attempt_id", (trial_id,)))

    def http_trial_plan(self, trial_id: str, project: str) -> dict:
        with closing(self._connect()) as db:
            row = db.execute("SELECT project,plan_json FROM http_trials WHERE trial_id=?", (trial_id,)).fetchone()
            if not row or row[0] != project:
                raise PermissionError("http_trial_scope_denied")
            return json.loads(row[1])

    def enqueue(self, item: WorkItem, *, now: datetime | None = None) -> bool:
        current = (now or utc_now()).isoformat()
        try:
            with closing(self._connect()) as db, db:
                db.execute(
                    "INSERT INTO work_items VALUES (?, ?, ?, ?, ?, 'queued', 0, ?, ?, NULL, NULL, NULL)",
                    (item.work_id, item.project, item.action, json.dumps(item.payload, sort_keys=True),
                     item.priority, item.max_attempts, current),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def claim_next(self, worker_id: str, *, lease_seconds: int = 60, now: datetime | None = None,
                   project: str | None = None, action: str | None = None) -> ClaimedWork | None:
        if not worker_id.strip() or lease_seconds <= 0:
            raise ValueError("invalid_lease")
        current_dt = now or utc_now()
        current, lease_until = current_dt.isoformat(), (current_dt + timedelta(seconds=lease_seconds)).isoformat()
        db = self._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM work_items WHERE attempts < max_attempts AND not_before <= ? "
                "AND (status='queued' OR (status='leased' AND lease_until < ?)) "
                "AND (? IS NULL OR project=?) AND (? IS NULL OR action=?) "
                "ORDER BY priority DESC, not_before ASC LIMIT 1", (current, current, project, project, action, action),
            ).fetchone()
            if row is None:
                db.execute("COMMIT")
                return None
            attempt = row["attempts"] + 1
            db.execute(
                "UPDATE work_items SET status='leased', attempts=?, lease_owner=?, lease_until=? WHERE work_id=?",
                (attempt, worker_id, lease_until, row["work_id"]),
            )
            db.execute("COMMIT")
            return ClaimedWork(row["work_id"], row["project"], row["action"],
                               json.loads(row["payload_json"]), attempt, lease_until)
        except Exception:
            db.execute("ROLLBACK")
            raise
        finally:
            db.close()

    def complete(self, work_id: str, worker_id: str) -> None:
        with closing(self._connect()) as db, db:
            changed = db.execute(
                "UPDATE work_items SET status='completed', lease_owner=NULL, lease_until=NULL "
                "WHERE work_id=? AND status='leased' AND lease_owner=?", (work_id, worker_id),
            ).rowcount
        if changed != 1:
            raise PermissionError("lease_owner_mismatch")

    def defer(self, work_id: str, worker_id: str, reason: str, *, delay_seconds: int = 60, now: datetime | None = None) -> str:
        """Release a lease for a non-failure wait without consuming execution retry budget."""
        if delay_seconds <= 0:
            raise ValueError("invalid_defer_delay")
        current = now or utc_now()
        not_before = (current + timedelta(seconds=delay_seconds)).isoformat()
        db = self._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT attempts FROM work_items WHERE work_id=? AND lease_owner=? AND status='leased'",
                (work_id, worker_id),
            ).fetchone()
            if row is None:
                raise PermissionError("lease_owner_mismatch")
            restored_attempts = max(0, row["attempts"] - 1)
            changed = db.execute(
                "UPDATE work_items SET status='queued', attempts=?, not_before=?, lease_owner=NULL, "
                "lease_until=NULL, last_error=? WHERE work_id=? AND status='leased' AND lease_owner=?",
                (restored_attempts, not_before, f"deferred:{reason}"[:500], work_id, worker_id),
            ).rowcount
            if changed != 1:
                raise PermissionError("lease_owner_mismatch")
            db.execute("COMMIT")
            return "queued"
        except Exception:
            db.execute("ROLLBACK")
            raise
        finally:
            db.close()

    def fail(self, work_id: str, worker_id: str, error: str, *, now: datetime | None = None) -> str:
        current = now or utc_now()
        db = self._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT attempts, max_attempts FROM work_items WHERE work_id=? AND lease_owner=? AND status='leased'",
                (work_id, worker_id),
            ).fetchone()
            if row is None:
                raise PermissionError("lease_owner_mismatch")
            if row["attempts"] >= row["max_attempts"]:
                status, not_before = "dead_letter", current.isoformat()
            else:
                status = "queued"
                delay = min(3600, 30 * (2 ** (row["attempts"] - 1)))
                not_before = (current + timedelta(seconds=delay)).isoformat()
            db.execute(
                "UPDATE work_items SET status=?, not_before=?, lease_owner=NULL, lease_until=NULL, last_error=? WHERE work_id=?",
                (status, not_before, error[:500], work_id),
            )
            db.execute("COMMIT")
            return status
        except Exception:
            db.execute("ROLLBACK")
            raise
        finally:
            db.close()

    def monthly_spend(self, *, year: int, month: int) -> float:
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        end = datetime(year + (month == 12), 1 if month == 12 else month + 1, 1, tzinfo=timezone.utc)
        with closing(self._connect()) as db, db:
            value = db.execute(
                "SELECT COALESCE(SUM(cost_usd),0) FROM usage_ledger WHERE occurred_at>=? AND occurred_at<?",
                (start.isoformat(), end.isoformat()),
            ).fetchone()[0]
        return float(value)

    def budget_allows(self, estimated_cost_usd: float, monthly_limit_usd: float, *, now: datetime | None = None) -> bool:
        if estimated_cost_usd < 0 or monthly_limit_usd < 0:
            raise ValueError("invalid_budget")
        current = now or utc_now()
        return self.monthly_spend(year=current.year, month=current.month) + estimated_cost_usd <= monthly_limit_usd

    def record_usage(self, usage_id: str, project: str, cost_usd: float, *, now: datetime | None = None) -> None:
        if cost_usd < 0:
            raise ValueError("invalid_cost")
        with closing(self._connect()) as db, db:
            db.execute("INSERT INTO usage_ledger VALUES (?, ?, ?, ?)",
                       (usage_id, project, cost_usd, (now or utc_now()).isoformat()))

    def record_capability_failure(self, capability: str, *, threshold: int = 3, now: datetime | None = None) -> str:
        if threshold <= 0:
            raise ValueError("invalid_threshold")
        with closing(self._connect()) as db, db:
            row = db.execute("SELECT failures FROM circuit_breakers WHERE capability=?", (capability,)).fetchone()
            failures = (row[0] if row else 0) + 1
            state = "open" if failures >= threshold else "closed"
            db.execute(
                "INSERT INTO circuit_breakers VALUES (?, ?, ?, ?) "
                "ON CONFLICT(capability) DO UPDATE SET failures=excluded.failures, state=excluded.state, opened_at=excluded.opened_at",
                (capability, failures, state, (now or utc_now()).isoformat() if state == "open" else None),
            )
        return state
