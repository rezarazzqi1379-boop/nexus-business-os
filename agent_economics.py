"""Agent/provider economics: accepted outputs matter more than raw success."""
from dataclasses import dataclass
@dataclass(frozen=True)
class AgentEconomics:
 agent:str; tasks:int; accepted:int; rejected:int; false_positives:int; failures:int; retries:int
 latency_ms:int; token_cost_usd:float=0; api_cost_usd:float=0; credit_cost_usd:float=0
def validate(x):
 vals=(x.tasks,x.accepted,x.rejected,x.false_positives,x.failures,x.retries,x.latency_ms,x.token_cost_usd,x.api_cost_usd,x.credit_cost_usd)
 if any(v<0 for v in vals):return ("negative_metric",)
 if x.accepted+x.rejected>x.tasks:return ("outcomes_exceed_tasks",)
 return ()
def economics(x):
 if validate(x):raise ValueError("invalid_agent_economics")
 cost=x.token_cost_usd+x.api_cost_usd+x.credit_cost_usd
 return {"acceptance_rate":None if x.tasks==0 else x.accepted/x.tasks,
 "cost_per_accepted":None if x.accepted==0 else cost/x.accepted,
 "failure_rate":None if x.tasks==0 else x.failures/x.tasks}
