"""NEXUS Scientist experiment contract: proposes/measures; cannot self-deploy."""
from dataclasses import dataclass
@dataclass(frozen=True)
class Experiment:
 experiment_id:str; hypothesis:str; baseline_metric:float; candidate_metric:float
 cost_before:float; cost_after:float; evidence_refs:tuple[str,...]; held_out:bool=False
def decision(x:Experiment)->str:
 if not x.experiment_id.strip() or not x.hypothesis.strip():return "REJECT_INVALID_EXPERIMENT"
 if not (0<=x.baseline_metric<=1 and 0<=x.candidate_metric<=1):return "REJECT_INVALID_METRIC"
 if x.cost_before<0 or x.cost_after<0:return "REJECT_INVALID_COST"
 if not x.evidence_refs:return "REJECT_NO_EVIDENCE"
 if not x.held_out:return "HUMAN_REVIEW_NO_HELD_OUT"
 if x.candidate_metric>x.baseline_metric and x.cost_after<=x.cost_before:return "PROMOTE_CANDIDATE"
 return "ROLLBACK_CANDIDATE"
