from datetime import datetime,timezone
import pytest
from steel_commercial_network import *
T=datetime(2026,10,7,tzinfo=timezone.utc)
def e(**kw):
 d=dict(edge_id="E1",project_id="P",source_node="C",target_node="X",relation="HAS_PROCUREMENT_SIGNAL",source_type=NodeType.COMPANY,target_type=NodeType.PROCUREMENT_EVENT,source_origin="official",source_locator="u",observed_at=T,authority="OFFICIAL_PRIMARY",confidence=.9,lineage_id="L"); d.update(kw); return CommercialEdge(**d)
def test_unknown_authority_not_verified_neighbor():
 assert verified_neighbors(add_edge((),e(authority="UNKNOWN")),"C")==()
def test_contradicted_edge_not_verified():
 assert verified_neighbors(add_edge((),e(contradicted=True)),"C")==()
def test_relationship_path_requires_more_than_demand():
 g=add_edge((),e()); assert not relationship_path_ready(g,"C")
 g=add_edge(g,e(edge_id="E2",target_node="S",relation="HAS_INCUMBENT",target_type=NodeType.SUPPLIER)); assert relationship_path_ready(g,"C")
def test_cross_project_graph_rejected():
 g=add_edge((),e())
 with pytest.raises(ValueError): add_edge(g,e(edge_id="E2",project_id="OTHER"))

def test_relationship_path_is_company_scoped():
 g=add_edge((),e())
 g=add_edge(g,e(edge_id="E2",target_node="S",relation="HAS_INCUMBENT",target_type=NodeType.SUPPLIER))
 assert relationship_path_ready(g,"C")
 assert not relationship_path_ready(g,"OTHER")
