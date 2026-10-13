from shared_buyer_graph import *

def test_overlap_is_not_opportunity():
 e=(("EICO","GUNES","e1"),("AZINFORGE","GUNES","e2"))
 r=shared_buyers(e)
 assert r[0]["state"]=="SHARED_BUYER_DISCOVERY_SIGNAL"
 assert opportunity_from_overlap(r[0]) is False

def test_single_producer_not_shared():
 assert shared_buyers((("EICO","GUNES","e1"),))==()
