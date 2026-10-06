from steel_merchant_discovery import *

def test_discovery_priority_is_not_relationship_verification():
 c=SteelDiscoveryCandidate("x","TRADER",("CATALOG",),1,1,1,.3,1)
 assert c.priority()>0 and "SHIPMENT_REVERSE" in discovery_routes()

def test_unknown_signal_rejected():
 try:
  SteelDiscoveryCandidate("x","TRADER",("RUMOR",),1,1,1,1,1).priority()
  assert False
 except ValueError:
  assert True

def test_cost_penalizes_priority():
 a=SteelDiscoveryCandidate("a","END_USER",("PROCUREMENT",),1,1,1,1,1,1)
 b=SteelDiscoveryCandidate("b","END_USER",("PROCUREMENT",),1,1,1,1,1,2)
 assert a.priority()>b.priority()
