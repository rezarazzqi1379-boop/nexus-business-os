"""NEXUS Scientist experiment contract: proposes/measures; cannot self-deploy."""
from dataclasses import dataclass
@dataclass(frozen=True)
class Experiment:
 experiment_id:str; hypothesis:str; baseline_metric:float; candidate_metric:float
 cost_before:float; cost_after:float; evidence_refs:tuple[str,...]; held_out:bool=False
def decision(x:Experiment)->str:
 if not x.evidence_refs:return "REJECT_NO_EVIDENCE"
 if not x.held_out:return "HUMAN_REVIEW_NO_HELD_OUT"
 if x.candidate_metric>x.baseline_metric and x.cost_after<=x.cost_before:return "PROMOTE_CANDIDATE"
 return "ROLLBACK_CANDIDATE"
