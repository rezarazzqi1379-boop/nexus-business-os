from cost_to_outcome import OutcomeCosts,metrics
def test_cost_metrics_never_fake_zero_when_no_outcome():
 m=metrics(OutcomeCosts(100,qualified_leads=10,rfqs=2))
 assert m["cost_per_qualified_lead"]==10
 assert m["cost_per_rfq"]==50
 assert m["cost_per_order"] is None
