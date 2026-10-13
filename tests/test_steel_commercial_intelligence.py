from steel_commercial_intelligence import *
def E(l,r,rel,ref="E1",kind=EvidenceKind.OBSERVED,current=True,p="P"): return IntelEdge(p,l,rel,r,ref,"2026-10-07",kind,current)
def test_hypothesis_cannot_be_current():
 assert not validate_edge(E("plant","chain","CURRENT_PROCUREMENT_NEED",kind=EvidenceKind.HYPOTHESIS))
def test_benchmark_failure_does_not_create_demand():
 es=failure_to_part_hypothesis("P","mill","stand","bearing","bearing","BENCH","2026")
 assert not current_demand_ready(es,"P","mill","bearing")
def test_two_bound_current_origins_can_support_demand():
 es=(E("buyer","chain","CURRENT_RFQ","R1"),E("chain","buyer","CURRENT_PROCUREMENT_NEED","R2"))
 assert current_demand_ready(es,"P","buyer","chain")
def test_same_origin_is_not_independent():
 es=(E("buyer","chain","CURRENT_RFQ","R1"),E("chain","buyer","CURRENT_PROCUREMENT_NEED","R1"))
 assert not current_demand_ready(es,"P","buyer","chain")
def test_cross_project_does_not_leak():
 es=(E("buyer","chain","CURRENT_RFQ","R1",p="A"),E("chain","buyer","CURRENT_PROCUREMENT_NEED","R2",p="B"))
 assert not current_demand_ready(es,"A","buyer","chain")
