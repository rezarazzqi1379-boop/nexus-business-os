from source_intelligence import *
def test_many_hits_without_qualified_evidence_is_downgraded():
 assert source_state(SourceScore(3,3,3,0,100,1))=="DOWNGRADE_ZERO_QUALIFIED_YIELD"
def test_low_authority_never_becomes_primary_from_volume():
 assert source_state(SourceScore(1,3,3,20,25,1))=="DISCOVERY_ONLY_LOW_AUTHORITY"
def test_stale_primary_source_is_historical_for_dynamic_claims():
 assert source_state(SourceScore(3,1,3,5,5,1))=="HISTORICAL_ONLY"
def test_good_source_can_promote():
 assert source_state(SourceScore(3,3,3,4,5,2))=="PRIMARY_OR_VERIFIED_DISCOVERY"
