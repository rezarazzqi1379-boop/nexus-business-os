from two_hop_commercial_graph import *

def test_two_hop_never_becomes_direct_relationship():
 a=RelationshipEdge("EICO","SOLD_TO","GUNES",("shipment:eico-gunes",))
 b=RelationshipEdge("GUNES","SOLD_TO","ENDUSER",("shipment:gunes-enduser",))
 r=expand_two_hop((a,),(b,))
 assert r[0]["state"]=="CANDIDATE_TWO_HOP"
 assert r[0]["origin"]=="EICO" and r[0]["target"]=="ENDUSER"

def test_unconnected_edges_do_not_expand():
 a=RelationshipEdge("EICO","SOLD_TO","GUNES",("e1",))
 b=RelationshipEdge("OTHER","SOLD_TO","X",("e2",))
 assert expand_two_hop((a,),(b,))==()
