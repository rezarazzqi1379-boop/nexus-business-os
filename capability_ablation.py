"""Capability ablation under comparable budget."""
from dataclasses import dataclass
@dataclass(frozen=True)
class AblationResult:
 name:str; accepted:int; cost_usd:float; latency_ms:int; evidence_coverage:float
def decision(base:AblationResult,cand:AblationResult,budget_tolerance=.1):
 if any(x<0 for x in (base.accepted,cand.accepted,base.cost_usd,cand.cost_usd,base.latency_ms,cand.latency_ms)):raise ValueError("invalid_ablation")
 if not 0<=base.evidence_coverage<=1 or not 0<=cand.evidence_coverage<=1:raise ValueError("invalid_coverage")
 if cand.cost_usd>base.cost_usd*(1+budget_tolerance):return "NOT_COMPARABLE_BUDGET"
 if cand.accepted>base.accepted and cand.evidence_coverage>=base.evidence_coverage:return "PROMOTE_CANDIDATE"
 if cand.accepted<base.accepted:return "ROLLBACK_CANDIDATE"
 return "KEEP_EXPERIMENTAL"
