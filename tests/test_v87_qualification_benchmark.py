from opportunity_qualification import *
from search_strategy_benchmark import *

def test_pursue_blocks_hidden_critical_unknown():
 x=OpportunityAssessment("zvezda","POTENTIAL_FIT",evidence_quality=.9,recency=.9,buyer_value=.8)
 d,reasons=qualify(x)
 assert d=="INVESTIGATE" and "unknown:compliance" in reasons

def test_no_fit_rejects():
 assert qualify(OpportunityAssessment("x","NO_FIT"))[0]=="REJECT"

def test_equal_budget_required():
 a=SearchStrategyResult("A",3,3,0,1,0,1,0,1,0,1,0)
 b=SearchStrategyResult("B",4,3,1,2,0,2,1,2,0,1,1)
 assert not compare_equal_budget((a,b))["comparable"]

def test_resolution_yield():
 a=SearchStrategyResult("A",4,4,1,2,1,1,1,4,0,2,2)
 r=compare_equal_budget((a,))
 assert r["results"]["A"]["resolution_yield"]==.5
