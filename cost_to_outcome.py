"""Cost-to-accepted-outcome metrics with explicit zero-denominator handling."""
from dataclasses import dataclass
@dataclass(frozen=True)
class OutcomeCosts:
 total_cost_usd:float; qualified_leads:int=0; verified_decision_makers:int=0; rfqs:int=0; accepted_opportunities:int=0; orders:int=0
def metrics(x:OutcomeCosts):
 if x.total_cost_usd<0 or any(v<0 for v in (x.qualified_leads,x.verified_decision_makers,x.rfqs,x.accepted_opportunities,x.orders)):raise ValueError("invalid_cost_outcome")
 def c(n):return None if n==0 else round(x.total_cost_usd/n,4)
 return {"cost_per_qualified_lead":c(x.qualified_leads),"cost_per_verified_decision_maker":c(x.verified_decision_makers),"cost_per_rfq":c(x.rfqs),"cost_per_accepted_opportunity":c(x.accepted_opportunities),"cost_per_order":c(x.orders)}
