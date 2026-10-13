from agent_economics import AgentEconomics,economics
from capability_ablation import AblationResult,decision
from query_evolution import variants
def test_agent_economics_uses_accepted_output_denominator():
 m=economics(AgentEconomics("x",10,2,5,1,1,0,100,token_cost_usd=4))
 assert m["cost_per_accepted"]==2
def test_zero_accepted_cost_is_unknown_not_zero():
 assert economics(AgentEconomics("x",2,0,2,0,0,0,1,api_cost_usd=3))["cost_per_accepted"] is None
def test_ablation_rejects_unfair_budget_comparison():
 b=AblationResult("base",5,10,100,.8); c=AblationResult("new",7,20,100,.9)
 assert decision(b,c)=="NOT_COMPARABLE_BUDGET"
def test_query_variants_are_candidates_not_evidence():
 xs=variants("gear","Turkey","20MnCr5")
 assert len(xs)>=4 and all(x["status"]=="CANDIDATE" for x in xs)
