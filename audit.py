from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from contracts import canonical_digest


class AuditLog:
    """Append-only hash chain for tamper-evident operational records."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS audit_log (sequence INTEGER PRIMARY KEY AUTOINCREMENT, occurred_at TEXT NOT NULL, actor TEXT NOT NULL, kind TEXT NOT NULL, body_json TEXT NOT NULL, previous_hash TEXT NOT NULL, record_hash TEXT NOT NULL UNIQUE)")

    def append(self, actor: str, kind: str, body: dict, *, occurred_at: datetime | None = None) -> str:
        if not actor.strip() or not kind.strip():
            raise ValueError("invalid_audit_identity")
        at = (occurred_at or datetime.now(timezone.utc)).isoformat()
        body_json = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        with sqlite3.connect(self.path) as db:
            previous = db.execute("SELECT record_hash FROM audit_log ORDER BY sequence DESC LIMIT 1").fetchone()
            previous_hash = previous[0] if previous else "GENESIS"
            record_hash = canonical_digest({"occurred_at": at, "actor": actor, "kind": kind,
                                            "body_json": body_json, "previous_hash": previous_hash})
            db.execute("INSERT INTO audit_log(occurred_at,actor,kind,body_json,previous_hash,record_hash) VALUES (?,?,?,?,?,?)",
                       (at, actor, kind, body_json, previous_hash, record_hash))
        return record_hash

    def verify(self) -> bool:
        previous_hash = "GENESIS"
        with sqlite3.connect(self.path) as db:
            rows = db.execute("SELECT occurred_at,actor,kind,body_json,previous_hash,record_hash FROM audit_log ORDER BY sequence").fetchall()
        for at, actor, kind, body_json, stored_previous, stored_hash in rows:
            expected = canonical_digest({"occurred_at": at, "actor": actor, "kind": kind,
                                         "body_json": body_json, "previous_hash": previous_hash})
            if stored_previous != previous_hash or stored_hash != expected:
                return False
            previous_hash = stored_hash
        return True

