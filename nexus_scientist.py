"""NEXUS Scientist: measured recommendation only; never deployment authority."""
from dataclasses import dataclass
@dataclass(frozen=True)
class Experiment:
 experiment_id:str; hypothesis:str; baseline_metric:float; candidate_metric:float
 cost_before:float; cost_after:float; evidence_refs:tuple[str,...]; held_out:bool=False
 sample_size:int=0; minimum_effect:float=0.0; metric_direction:str="HIGHER_IS_BETTER"
def decision(x):
 if not x.experiment_id.strip() or not x.hypothesis.strip():return "REJECT_INVALID_EXPERIMENT"
 if not (0<=x.baseline_metric<=1 and 0<=x.candidate_metric<=1):return "REJECT_INVALID_METRIC"
 if x.cost_before<0 or x.cost_after<0:return "REJECT_INVALID_COST"
 if x.sample_size<1:return "REJECT_INSUFFICIENT_SAMPLE"
 if x.minimum_effect<0:return "REJECT_INVALID_EFFECT"
 if x.metric_direction not in {"HIGHER_IS_BETTER","LOWER_IS_BETTER"}:return "REJECT_INVALID_DIRECTION"
 if not x.evidence_refs:return "REJECT_NO_EVIDENCE"
 if not x.held_out:return "HUMAN_REVIEW_NO_HELD_OUT"
 delta=(x.candidate_metric-x.baseline_metric) if x.metric_direction=="HIGHER_IS_BETTER" else (x.baseline_metric-x.candidate_metric)
 if delta>=x.minimum_effect and delta>0 and x.cost_after<=x.cost_before:return "PROMOTE_CANDIDATE"
 return "ROLLBACK_CANDIDATE"
