"""Small durable project-state store for NEXUS.

Local SQLite only. This fills the repository's previously missing
ProjectMemoryStore contract without introducing a framework or network dependency.
"""
from __future__ import annotations
import json, sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

def _now(): return datetime.now(timezone.utc).isoformat()

@dataclass(frozen=True)
class ProjectCheckpoint:
    project_id: str
    lane: str
    status: str
    last_done: str
    next_action: str
    blockers: tuple[str,...]=()
    evidence_refs: tuple[str,...]=()

class ProjectMemoryStore:
    def __init__(self,path:Path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS checkpoints(
              project_id TEXT NOT NULL,lane TEXT NOT NULL,status TEXT NOT NULL,
              last_done TEXT NOT NULL,next_action TEXT NOT NULL,blockers TEXT NOT NULL,
              evidence_refs TEXT NOT NULL,updated_at TEXT NOT NULL,
              PRIMARY KEY(project_id,lane))""")
    def save(self,c:ProjectCheckpoint)->None:
        if not c.project_id.strip() or not c.lane.strip() or not c.next_action.strip():
            raise ValueError("invalid_checkpoint")
        with sqlite3.connect(self.path) as db:
            db.execute("""INSERT INTO checkpoints VALUES(?,?,?,?,?,?,?,?)
              ON CONFLICT(project_id,lane) DO UPDATE SET status=excluded.status,
              last_done=excluded.last_done,next_action=excluded.next_action,
              blockers=excluded.blockers,evidence_refs=excluded.evidence_refs,
              updated_at=excluded.updated_at""",
              (c.project_id,c.lane,c.status,c.last_done,c.next_action,
               json.dumps(c.blockers),json.dumps(c.evidence_refs),_now()))
    def load(self,project_id:str)->tuple[ProjectCheckpoint,...]:
        with sqlite3.connect(self.path) as db:
            rows=db.execute("""SELECT project_id,lane,status,last_done,next_action,
              blockers,evidence_refs FROM checkpoints WHERE project_id=? ORDER BY lane""",
              (project_id,)).fetchall()
        return tuple(ProjectCheckpoint(*r[:5],tuple(json.loads(r[5])),tuple(json.loads(r[6]))) for r in rows)
