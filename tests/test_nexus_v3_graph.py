from opportunity_graph import GraphEdge,validate_edge
from demand_signal import DemandSignal,validate_signal,signal_to_opportunity_state
def test_verified_graph_edge_requires_evidence():
 assert "verified_edge_requires_evidence" in validate_edge(GraphEdge("company","uses","20MnCr5","FACT"))
def test_hypothesis_edge_can_exist_without_fake_proof():
 assert validate_edge(GraphEdge("company","may_need","20MnCr5","HYPOTHESIS"))==()
def test_signal_is_not_a_verified_opportunity():
 s=DemandSignal("GearCo","Turkey","PLANT_EXPANSION","2026-10-05",("official:1",),"20MnCr5")
 assert validate_signal(s)==()
 assert signal_to_opportunity_state(s)=="HYPOTHESIS"
