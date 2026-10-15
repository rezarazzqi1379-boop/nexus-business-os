from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EventRecord:
    event_id: str
    project: str
    event_type: str
    payload: dict


class EventStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute(
                "CREATE TABLE IF NOT EXISTS events ("
                "event_id TEXT PRIMARY KEY, project TEXT NOT NULL, event_type TEXT NOT NULL, "
                "payload_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL, status TEXT NOT NULL)"
            )

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=5)
        db.execute("PRAGMA busy_timeout=5000")
        return db

    def add_once(self, event: EventRecord) -> bool:
        return self.begin(event) in {"new", "retry"}

    def begin(self, event: EventRecord) -> str:
        serialized = json.dumps(event.payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(serialized.encode()).hexdigest()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT project, event_type, payload_sha256, status FROM events WHERE event_id=?",
                (event.event_id,),
            ).fetchone()
            if row is None:
                db.execute(
                    "INSERT INTO events VALUES (?, ?, ?, ?, ?, 'processing')",
                    (event.event_id, event.project, event.event_type, serialized, digest),
                )
                return "new"
            existing_project, existing_event_type, existing_digest, status = row
            if existing_project != event.project:
                raise ValueError("event_id_project_mismatch")
            if existing_event_type != event.event_type:
                raise ValueError("event_id_type_mismatch")
            if existing_digest != digest:
                raise ValueError("event_id_payload_mismatch")
            if status == "retryable_error":
                db.execute("UPDATE events SET status='processing' WHERE event_id=?", (event.event_id,))
                return "retry"
            return "duplicate"

    def get_status(self, event_id: str) -> str:
        with self._connect() as db:
            row = db.execute("SELECT status FROM events WHERE event_id=?", (event_id,)).fetchone()
        if row is None:
            raise KeyError("unknown_event")
        return str(row[0])

    def set_status(self, event_id: str, status: str) -> None:
        with self._connect() as db:
            changed = db.execute("UPDATE events SET status=? WHERE event_id=?", (status, event_id)).rowcount
        if changed != 1:
            raise KeyError("unknown_event")
