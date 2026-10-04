from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    project_id: str
    topic: str
    value: str
    source_ref: str
    classification: str
    supersedes_claim_id: str | None = None


class ClaimStateStore:
    """Minimal operational claim state with explicit same-scope supersession."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute(
                "CREATE TABLE IF NOT EXISTS claims ("
                "claim_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, topic TEXT NOT NULL, "
                "value TEXT NOT NULL, source_ref TEXT NOT NULL, classification TEXT NOT NULL, "
                "supersedes_claim_id TEXT, status TEXT NOT NULL)"
            )

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=5000")
        return db

    def add(self, claim: ClaimRecord) -> None:
        if not all((claim.claim_id.strip(), claim.project_id.strip(), claim.topic.strip(),
                    claim.value.strip(), claim.source_ref.strip(), claim.classification.strip())):
            raise ValueError("invalid_claim")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM claims WHERE claim_id=?", (claim.claim_id,)).fetchone():
                raise ValueError("duplicate_claim_id")
            if claim.supersedes_claim_id:
                prior = db.execute(
                    "SELECT project_id, topic, status FROM claims WHERE claim_id=?",
                    (claim.supersedes_claim_id,),
                ).fetchone()
                if prior is None:
                    raise KeyError("superseded_claim_missing")
                if prior["project_id"] != claim.project_id:
                    raise ValueError("cross_project_supersession_rejected")
                if prior["topic"] != claim.topic:
                    raise ValueError("cross_topic_supersession_rejected")
                if prior["status"] != "active":
                    raise ValueError("superseded_claim_not_active")
                db.execute("UPDATE claims SET status='superseded' WHERE claim_id=?", (claim.supersedes_claim_id,))
            db.execute(
                "INSERT INTO claims VALUES (?,?,?,?,?,?,?, 'active')",
                (claim.claim_id, claim.project_id, claim.topic, claim.value, claim.source_ref,
                 claim.classification, claim.supersedes_claim_id),
            )

    def active_for(self, project_id: str, topic: str) -> tuple[sqlite3.Row, ...]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM claims WHERE project_id=? AND topic=? AND status='active' ORDER BY claim_id",
                (project_id, topic),
            ).fetchall()
        return tuple(rows)
