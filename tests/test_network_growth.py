from network_growth import *
def test_verified_node_requires_evidence():
 assert not admissible_node(NetworkNode("P","x","COMPANY","X",NodeState.VERIFIED))
def test_clue_can_be_preserved_without_promotion():
 assert admissible_node(NetworkNode("P","x","ROLE","procurement role",NodeState.CLUE))
def test_edge_requires_provenance_and_time():
 assert not admissible_edge(NetworkEdge("P","a","BUYS","b","","2026-10-07"))
def test_cross_project_frontier_does_not_leak():
 ns=(NetworkNode("A","b","BUYER","B",NodeState.VERIFIED,("R",)),NetworkNode("B","x","BUYER","X",NodeState.VERIFIED,("X",)))
 es=(NetworkEdge("A","seed","BUYS","b","R","2026"),NetworkEdge("B","seed","BUYS","x","X","2026"))
 assert expand_frontier(ns,es,"A",("seed",))==("b",)
def test_duplicate_origin_not_relationship_strength():
 es=(NetworkEdge("P","a","BUYS","b","R1","2026"),NetworkEdge("P","b","SUPPLIES","a","R1","2026"))
 assert relationship_strength(es,"P","a","b")==1
