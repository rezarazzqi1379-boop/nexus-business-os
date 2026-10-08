from commercial_source_registry import *

def test_seed_sources_are_valid_and_unique():
 s=seed_sources()
 assert all(valid_source(x) for x in s)
 assert len({x.source_id for x in s})==len(s)

def test_procurement_authority_can_support_current_only_with_live_refresh():
 s=source_by_id("KZ-UNIFIED-PROC")
 assert may_support_current_procurement(s)
 assert not may_support_current_procurement(CommercialSource("x","KZ","mirror.example",SourceRole.DISCOVERY,SourceAuthority.DISCOVERY_ONLY))

def test_award_authority_can_support_verified_winner():
 assert may_support_verified_winner(source_by_id("TJ-EPROC"))

def test_supplier_registration_route_does_not_equal_current_demand():
 s=source_by_id("OM-JSRS")
 assert s.registration
 assert not may_support_current_procurement(s)
 assert not may_support_verified_winner(s)

def test_trade_statistics_cannot_become_company_procurement_proof():
 s=source_by_id("GLOBAL-COMTRADE")
 assert s.role==SourceRole.TRADE_STATISTICS
 assert not may_support_current_procurement(s)
 assert not may_support_verified_winner(s)

def test_discovery_source_never_promotes():
 s=CommercialSource("D","RU","aggregator.example",SourceRole.DISCOVERY,SourceAuthority.DISCOVERY_ONLY)
 assert discovery_only(s)
 assert not may_support_current_procurement(s)
 assert not may_support_verified_winner(s)
