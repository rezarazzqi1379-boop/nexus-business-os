from opportunity_graph import GraphEdge,can_promote_verified
from evidence_triangulation import EvidenceRef
def test_graph_promotion_requires_independent_evidence():
 e=GraphEdge("Company","uses","20MnCr5","HYPOTHESIS",("a","b"),"2026-10-05")
 same=(EvidenceRef("a","OFFICIAL_COMPANY","x"),EvidenceRef("b","INDEPENDENT_SOURCE","x"))
 assert not can_promote_verified(e,same,today="2026-10-05")
 independent=(EvidenceRef("a","OFFICIAL_COMPANY","x"),EvidenceRef("b","TRADE_DATASET","trade-y"))
 assert can_promote_verified(e,independent,today="2026-10-05")
def test_graph_promotion_fails_on_contradiction():
 e=GraphEdge("Company","uses","20MnCr5","HYPOTHESIS",("a","b"),"2026-10-05")
 ev=(EvidenceRef("a","OFFICIAL_COMPANY","x"),EvidenceRef("b","TRADE_DATASET","trade-y"),EvidenceRef("c","REGULATOR","r",True,True))
 assert not can_promote_verified(e,ev,today="2026-10-05")
