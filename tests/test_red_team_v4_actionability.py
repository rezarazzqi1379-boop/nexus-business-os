from country_opportunity_queue import OpportunityCandidate,queue_score,actionable

def test_high_rank_is_not_actionable_without_compliance():
    x=OpportunityCandidate("x","RU","Buyer",100,100,100,False)
    assert queue_score(x)==100
    assert actionable(x) is False

def test_compliance_ready_is_separate_execution_gate():
    x=OpportunityCandidate("x","OM","Buyer",50,50,50,True)
    assert actionable(x) is True
