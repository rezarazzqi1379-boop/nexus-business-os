from __future__ import annotations

import json
import sqlite3
from contextlib import closing
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
    """Durable queue, approval inbox, budget ledger, and circuit breakers."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db:
            with db:
                db.executescript(
                """
                CREATE TABLE IF NOT EXISTS work_items (
                    work_id TEXT PRIMARY KEY, project TEXT NOT NULL, action TEXT NOT NULL,
                    payload_json TEXT NOT NULL, priority INTEGER NOT NULL, status TEXT NOT NULL,
                    attempts INTEGER NOT NULL, max_attempts INTEGER NOT NULL,
                    not_before TEXT NOT NULL, lease_owner TEXT, lease_until TEXT, last_error TEXT
                );
                CREATE TABLE IF NOT EXISTS approval_inbox (
                    approval_id TEXT PRIMARY KEY, work_id TEXT NOT NULL, action_digest TEXT NOT NULL,
                    summary TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
                    decided_at TEXT, UNIQUE(work_id, action_digest)
                );
                CREATE TABLE IF NOT EXISTS usage_ledger (
                    usage_id TEXT PRIMARY KEY, project TEXT NOT NULL, cost_usd REAL NOT NULL,
                    occurred_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS circuit_breakers (
                    capability TEXT PRIMARY KEY, failures INTEGER NOT NULL, state TEXT NOT NULL,
                    opened_at TEXT
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.execute("PRAGMA busy_timeout=5000")
        db.row_factory = sqlite3.Row
        return db

    def enqueue(self, item: WorkItem, *, now: datetime | None = None) -> bool:
        current = (now or utc_now()).isoformat()
        try:
            with closing(self._connect()) as db:
                with db:
                    db.execute(
                        "INSERT INTO work_items VALUES (?, ?, ?, ?, ?, 'queued', 0, ?, ?, NULL, NULL, NULL)",
                        (item.work_id, item.project, item.action, json.dumps(item.payload, sort_keys=True),
                         item.priority, item.max_attempts, current),
                    )
            return True
        except sqlite3.IntegrityError:
            return False

    def claim_next(self, worker_id: str, *, lease_seconds: int = 60, now: datetime | None = None) -> ClaimedWork | None:
        if not worker_id.strip() or lease_seconds <= 0:
            raise ValueError("invalid_lease")
        current_dt = now or utc_now()
        current, lease_until = current_dt.isoformat(), (current_dt + timedelta(seconds=lease_seconds)).isoformat()
        with closing(self._connect()) as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute(
                    "SELECT * FROM work_items WHERE attempts < max_attempts AND not_before <= ? "
                    "AND (status='queued' OR (status='leased' AND lease_until < ?)) "
                    "ORDER BY priority DESC, not_before ASC LIMIT 1", (current, current),
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

    def complete(self, work_id: str, worker_id: str) -> None:
        with closing(self._connect()) as db:
            with db:
                changed = db.execute(
                    "UPDATE work_items SET status='completed', lease_owner=NULL, lease_until=NULL "
                    "WHERE work_id=? AND status='leased' AND lease_owner=?", (work_id, worker_id),
                ).rowcount
        if changed != 1:
            raise PermissionError("lease_owner_mismatch")

    def fail(self, work_id: str, worker_id: str, error: str, *, now: datetime | None = None) -> str:
        current = now or utc_now()
        with closing(self._connect()) as db:
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

    def monthly_spend(self, *, year: int, month: int) -> float:
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        end = datetime(year + (month == 12), 1 if month == 12 else month + 1, 1, tzinfo=timezone.utc)
        with closing(self._connect()) as db:
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
        with closing(self._connect()) as db:
            with db:
                db.execute("INSERT INTO usage_ledger VALUES (?, ?, ?, ?)",
                           (usage_id, project, cost_usd, (now or utc_now()).isoformat()))

    def record_capability_failure(self, capability: str, *, threshold: int = 3, now: datetime | None = None) -> str:
        if threshold <= 0:
            raise ValueError("invalid_threshold")
        with closing(self._connect()) as db:
            with db:
                row = db.execute("SELECT failures FROM circuit_breakers WHERE capability=?", (capability,)).fetchone()
                failures = (row[0] if row else 0) + 1
                state = "open" if failures >= threshold else "closed"
                db.execute(
                "INSERT INTO circuit_breakers VALUES (?, ?, ?, ?) "
                "ON CONFLICT(capability) DO UPDATE SET failures=excluded.failures, state=excluded.state, opened_at=excluded.opened_at",
                (capability, failures, state, (now or utc_now()).isoformat() if state == "open" else None),
            )
        return state

