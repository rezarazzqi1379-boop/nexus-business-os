from opportunity_graph import GraphEdge,validate_edge
def test_company_material_fact_requires_evidence():
 assert "verified_edge_requires_evidence" in validate_edge(GraphEdge("company:x","USES","grade:20MnCr5","FACT"))
def test_hypothesis_is_not_promoted_to_fact():
 assert validate_edge(GraphEdge("company:x","MAY_NEED","grade:20MnCr5","HYPOTHESIS"))==()
def test_verified_edge_rejects_stale_evidence():
 e=GraphEdge("company:x","USES","grade:20MnCr5","FACT",("official:1",),"2025-01-01")
 assert "verified_edge_requires_fresh_evidence" in validate_edge(e,today="2026-10-05")
