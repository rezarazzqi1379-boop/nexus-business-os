from reverse_buyer_discovery import ReverseDiscovery,validate_reverse_discovery,candidate_state
def test_trade_discovery_never_becomes_verified_buyer():
 x=ReverseDiscovery("TRADE","Turkey","gear manufacturing","GearCo",("trade:q1",),"2026-10-05","722840")
 assert validate_reverse_discovery(x)==()
 assert candidate_state(x)=="HYPOTHESIS"
def test_trade_route_requires_hs_candidate():
 x=ReverseDiscovery("TRADE","Turkey","gear manufacturing","GearCo",("trade:q1",),"2026-10-05")
 assert "trade_route_hs_candidate_required" in validate_reverse_discovery(x)
