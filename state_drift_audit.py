"""Deterministic historical-decision and state-drift audit primitives."""
from __future__ import annotations
from dataclasses import dataclass

VOLATILE_FIELDS=frozenset({"stock","price","employment","compliance","availability","provider_health","ci_status","opportunity_stage","procurement_status","award_winner","decision_authority","sales_readiness","relationship_state"})
DRIFT_STATES=frozenset({"CONSISTENT","DRIFTED","STALE","CONTRADICTED","UNKNOWN"})

def audit_state(*,stored,observed,field:str,stale:bool=False,contradicted:bool=False)->str:
    if contradicted:return "CONTRADICTED"
    if observed is None:return "UNKNOWN"
    if stale:return "STALE"
    return "CONSISTENT" if stored==observed else "DRIFTED"

@dataclass(frozen=True)
class DecisionAutopsy:
    decision_id:str
    original_claim:str
    original_evidence:tuple[str,...]
    original_time:str
    current_evidence:tuple[str,...]=()
    contradicted:bool=False
    stale:bool=False
    outcome:str="UNKNOWN"
    failure_mode:str="UNKNOWN"
    commercial_cost:float|None=None

    @property
    def supersession_required(self)->bool:
        return self.contradicted or self.stale

    @property
    def regression_candidate(self)->bool:
        return self.contradicted or self.failure_mode not in {"","UNKNOWN","NONE"}

def supersession_record(a:DecisionAutopsy,new_claim:str)->dict:
    if not a.supersession_required:
        raise ValueError("supersession_not_required")
    return {
      "supersedes":a.decision_id,
      "original_claim":a.original_claim,
      "new_claim":new_claim,
      "current_evidence":a.current_evidence,
      "reason":"CONTRADICTED" if a.contradicted else "STALE",
    }
