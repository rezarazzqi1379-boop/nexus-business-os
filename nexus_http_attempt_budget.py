"""Crash-conservative HTTP attempt reservation for bounded monitor experiments.

Reservations are durable before the caller initiates HTTP. Unknown outcomes consume
budget; there is deliberately no refund or automatic retry of a reservation.
This module does not activate any provider or schedule network requests.
"""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import uuid


class AttemptBudgetExceeded(RuntimeError):
    pass


class AttemptBudget:
    """SQLite-backed atomic reservation with a fixed scope and immutable cap."""

    def __init__(self, path: str | Path, *, scope: str, max_attempts: int = 6):
        if not scope or len(scope) > 160 or not all(c.isalnum() or c in "-_:." for c in scope):
            raise ValueError("invalid_budget_scope")
        if type(max_attempts) is not int or not 1 <= max_attempts <= 6:
            raise ValueError("invalid_attempt_cap")
        self.path = str(path)
        self.scope = scope
        self.max_attempts = max_attempts
        # Missing budget after queue creation requires explicit recovery.
        if self.path.endswith(".http-attempts.sqlite"):
            queue_path = self.path.removesuffix(".http-attempts.sqlite")
            if Path(queue_path).exists() and not Path(self.path).exists():
                raise RuntimeError("missing_durable_http_budget_requires_recovery")
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""CREATE TABLE IF NOT EXISTS http_budget_scope
                (scope TEXT PRIMARY KEY, max_attempts INTEGER NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS http_budget_reservation
                (reservation_id TEXT PRIMARY KEY, scope TEXT NOT NULL,
                 tick_id TEXT NOT NULL, reserved_at TEXT NOT NULL,
                 FOREIGN KEY(scope) REFERENCES http_budget_scope(scope))""")
            db.execute("INSERT OR IGNORE INTO http_budget_scope VALUES (?,?)",
                       (self.scope, self.max_attempts))
            cap = db.execute("SELECT max_attempts FROM http_budget_scope WHERE scope=?",
                             (self.scope,)).fetchone()[0]
            if cap != self.max_attempts:
                raise ValueError("budget_cap_immutable")
            db.commit()

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        db.execute("PRAGMA busy_timeout=15000")
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def reserve(self, tick_id: str) -> str:
        """Commit one irreversible attempt before performing HTTP."""
        if not tick_id or len(tick_id) > 160:
            raise ValueError("invalid_tick_id")
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            used = db.execute("SELECT COUNT(*) FROM http_budget_reservation WHERE scope=?",
                              (self.scope,)).fetchone()[0]
            if used >= self.max_attempts:
                db.rollback()
                raise AttemptBudgetExceeded("http_attempt_budget_exhausted")
            per_tick = db.execute(
                "SELECT COUNT(*) FROM http_budget_reservation WHERE scope=? AND tick_id=?",
                (self.scope, tick_id)).fetchone()[0]
            distinct_ticks = db.execute(
                "SELECT COUNT(DISTINCT tick_id) FROM http_budget_reservation WHERE scope=?",
                (self.scope,)).fetchone()[0]
            if per_tick >= 2 or (per_tick == 0 and distinct_ticks >= 3):
                db.rollback()
                raise AttemptBudgetExceeded("http_tick_budget_exhausted")
            token = uuid.uuid4().hex
            db.execute("INSERT INTO http_budget_reservation VALUES (?,?,?,?)",
                       (token, self.scope, tick_id, datetime.now(timezone.utc).isoformat()))
            db.commit()
            return token

    def count(self) -> int:
        with closing(self._connect()) as db:
            return db.execute("SELECT COUNT(*) FROM http_budget_reservation WHERE scope=?",
                              (self.scope,)).fetchone()[0]

    def read(self, tick_id: str, transport, url: str):
        """Reserve first; a failed or interrupted transport still consumes a slot."""
        self.reserve(tick_id)
        return transport(url)


def budgeted_transport(budget: AttemptBudget, *, tick_id: str, transport):
    """Explicit opt-in transport wrapper for a single bounded source request.

    Callers must bind the returned callable to their existing allowlisted
    transport. This does not enable a source or alter the runtime mode.
    """
    if not callable(transport):
        raise TypeError("transport_must_be_callable")
    def guarded(url: str):
        return budget.read(tick_id, transport, url)
    return guarded
