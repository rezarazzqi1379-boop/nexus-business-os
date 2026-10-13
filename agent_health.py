"""Agent observability and deterministic health scoring."""
from dataclasses import dataclass
@dataclass(frozen=True)
class AgentTrace:
 agent:str; success:bool; evidence_refs:tuple[str,...]; latency_ms:int; cost_usd:float
 retries:int=0; silent_failure:bool=False
def health_score(traces)->int:
 xs=tuple(traces)
 if not xs:return 0
 if any(t.latency_ms<0 or t.cost_usd<0 or t.retries<0 for t in xs):raise ValueError("invalid_trace")
 success=sum(t.success for t in xs)/len(xs)
 evidenced=sum(bool(t.evidence_refs) for t in xs)/len(xs)
 silent=sum(t.silent_failure for t in xs)/len(xs)
 retry_penalty=min(sum(t.retries for t in xs)/(len(xs)*3),1)
 return max(0,min(100,round(55*success+30*evidenced+15*(1-silent)-10*retry_penalty)))
