import pytest
from steel_trade_graph import *
def E(p,s,t,r,ref="E1"): return Edge(p,s,"COMPANY",t,"COMPANY",r,ref,"2026-10-07")
def test_cross_project_edges_do_not_leak():
 es=(E("CHAIN","buyer","supplier","BUYS_FROM"),E("HYD","buyer","wrong","BUYS_FROM","H1"))
 assert relationship_paths(es,"CHAIN","buyer","wrong")==()
def test_unbound_edge_rejected():
 with pytest.raises(ValueError): build_adjacency((Edge("P","a","C","b","C","R","","2026"),),"P")
def test_relationship_path_supports_reverse_buyer_discovery():
 es=(E("P","buyer","incumbent","BUYS_FROM"),E("P","incumbent","maker","SUPPLIED_BY","E2"))
 assert relationship_paths(es,"P","buyer","maker")==(("buyer","incumbent","maker"),)
def test_same_origin_not_double_corroboration():
 es=(E("P","a","b","BUYS_FROM","X"),E("P","c","d","BUYS_FROM","X"))
 assert independent_origins(es,"P","BUYS_FROM")==1
