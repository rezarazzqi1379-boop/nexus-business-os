from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from contracts import canonical_digest


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ApprovalRequest:
    project_id: str
    action: str
    target: str
    parameters: dict
    requested_by: str
    ttl_seconds: int = 3600

    @property
    def action_digest(self) -> str:
        return canonical_digest({"project_id": self.project_id, "action": self.action,
                                 "target": self.target, "parameters": self.parameters})


class ApprovalStore:
    """Single-use exact-scope approvals.

    ``decided_by`` is caller-claimed audit metadata.  This store does not
    authenticate actors, so values such as ``"human"`` are not identity proof.
    Approval never implies connector authority.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db:
            with db:
                db.execute("""
                CREATE TABLE IF NOT EXISTS approvals (
                    approval_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, action TEXT NOT NULL,
                    target TEXT NOT NULL, parameters_json TEXT NOT NULL, action_digest TEXT NOT NULL,
                    requested_by TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL, decided_at TEXT, decided_by TEXT, consumed_at TEXT,
                    UNIQUE(action_digest, status)
                )
            """)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    def request(self, item: ApprovalRequest, *, now: datetime | None = None) -> str:
        if not all((item.project_id.strip(), item.action.strip(), item.target.strip(), item.requested_by.strip())):
            raise ValueError("invalid_approval_request")
        if not 1 <= item.ttl_seconds <= 86_400:
            raise ValueError("invalid_approval_ttl")
        current = now or utc_now()
        approval_id = "apr_" + uuid.uuid4().hex
        with closing(self._connect()) as db:
            with db:
                db.execute("INSERT INTO approvals VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                approval_id, item.project_id, item.action, item.target,
                json.dumps(item.parameters, sort_keys=True, separators=(",", ":")), item.action_digest,
                item.requested_by, "pending", current.isoformat(),
                (current + timedelta(seconds=item.ttl_seconds)).isoformat(), None, None, None,
                ))
        return approval_id

    def decide(self, approval_id: str, *, approved: bool, decided_by: str,
               now: datetime | None = None) -> str:
        if not decided_by.strip():
            raise ValueError("invalid_decider")
        current = now or utc_now()
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status, expires_at FROM approvals WHERE approval_id=?", (approval_id,)).fetchone()
            if row is None:
                db.rollback()
                raise KeyError("unknown_approval")
            if row["status"] != "pending":
                db.rollback()
                raise ValueError("approval_not_pending")
            status = "expired" if datetime.fromisoformat(row["expires_at"]) <= current else ("approved" if approved else "denied")
            changed = db.execute(
                "UPDATE approvals SET status=?, decided_at=?, decided_by=? "
                "WHERE approval_id=? AND status='pending'",
                (status, current.isoformat(), decided_by, approval_id),
            ).rowcount
            if changed != 1:
                db.rollback()
                raise ValueError("approval_not_pending")
            db.commit()
        return status

    def consume(self, approval_id: str, *, action_digest: str, now: datetime | None = None) -> bool:
        current = now or utc_now()
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status, action_digest, expires_at FROM approvals WHERE approval_id=?", (approval_id,)).fetchone()
            if row is None:
                raise KeyError("unknown_approval")
            if row["status"] != "approved" or row["action_digest"] != action_digest:
                db.rollback()
                return False
            if datetime.fromisoformat(row["expires_at"]) <= current:
                db.execute("UPDATE approvals SET status='expired' WHERE approval_id=?", (approval_id,))
                db.commit()
                return False
            changed = db.execute("UPDATE approvals SET status='consumed', consumed_at=? WHERE approval_id=? AND status='approved'",
                                 (current.isoformat(), approval_id)).rowcount
            db.commit()
            return changed == 1

    def get(self, approval_id: str) -> dict | None:
        """Return an isolated read-only snapshot without changing approval state."""
        with closing(self._connect()) as db:
            row = db.execute("SELECT * FROM approvals WHERE approval_id=?", (approval_id,)).fetchone()
            return dict(row) if row is not None else None
