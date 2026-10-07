"""Machine-readable milestone records for autonomous NEXUS cycles."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from datetime import datetime,timezone
import json
VALID={"DONE","TESTED","FAILED","UNKNOWN","IMPROVED","BLOCKED","NEXT","APPROVAL_NEEDED"}
@dataclass(frozen=True)
class Milestone:
    status:str; lane:str; statement:str; evidence_refs:tuple[str,...]=(); created_at:str=""
    def normalized(self):
        if self.status not in VALID: raise ValueError("invalid_status")
        if not self.lane.strip() or not self.statement.strip(): raise ValueError("lane_and_statement_required")
        if self.status in {"DONE","TESTED","IMPROVED"} and not self.evidence_refs: raise ValueError("positive_status_requires_evidence")
        return Milestone(self.status,self.lane,self.statement,self.evidence_refs,self.created_at or datetime.now(timezone.utc).isoformat())
    def to_json(self): return json.dumps(asdict(self.normalized()),ensure_ascii=False,sort_keys=True)
