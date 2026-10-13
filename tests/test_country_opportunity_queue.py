from country_opportunity_queue import OpportunityCandidate,build_country_queue,queue_score
def test_queue_is_deterministic_and_does_not_hide_compliance():
 a=OpportunityCandidate("A","Turkey","GearCo",90,80,90,False)
 b=OpportunityCandidate("B","Turkey","Stockist",60,90,80,True)
 q=build_country_queue([b,a])
 assert q[0].opportunity_id=="A"
 assert q[0].compliance_ready is False
 assert queue_score(a)==87
