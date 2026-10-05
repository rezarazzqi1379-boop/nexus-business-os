"""Measured discovery methods: outcomes, not search volume, determine promotion."""
from dataclasses import dataclass
STAGES={"EXPERIMENTAL","BENCHMARKED","APPROVED","ACTIVE","ROLLED_BACK"}
@dataclass(frozen=True)
class DiscoveryMethod:
 method_id:str; stage:str="EXPERIMENTAL"; source_types:tuple[str,...]=()
@dataclass(frozen=True)
class MethodRun:
 method_id:str; searched:int; accepted:int; false_positives:int; known_misses:int
 evidence_covered:int; cost_usd:float; latency_ms:int
def validate_run(x:MethodRun):
 e=[]
 if any(v<0 for v in (x.searched,x.accepted,x.false_positives,x.known_misses,x.evidence_covered,x.cost_usd,x.latency_ms)):e.append("negative_metric")
 if x.accepted>x.searched:e.append("accepted_exceeds_searched")
 if x.false_positives>x.searched:e.append("false_positive_exceeds_searched")
 return tuple(e)
def metrics(x:MethodRun):
 if validate_run(x):raise ValueError("invalid_method_run")
 precision=None if x.accepted+x.false_positives==0 else x.accepted/(x.accepted+x.false_positives)
 recall=None if x.accepted+x.known_misses==0 else x.accepted/(x.accepted+x.known_misses)
 cpa=None if x.accepted==0 else x.cost_usd/x.accepted
 return {"precision":precision,"recall_proxy":recall,"cost_per_accepted":cpa}
def compare(baseline:MethodRun,candidate:MethodRun):
 b,c=metrics(baseline),metrics(candidate)
 if c["precision"] is None or b["precision"] is None:return "INSUFFICIENT_EVIDENCE"
 if c["precision"]>b["precision"] and (b["cost_per_accepted"] is None or (c["cost_per_accepted"] is not None and c["cost_per_accepted"]<=b["cost_per_accepted"])):return "PROMOTE_CANDIDATE"
 return "KEEP_EXPERIMENTAL"
