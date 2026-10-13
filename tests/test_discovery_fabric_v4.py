from discovery_method_registry import MethodRun,metrics,compare
from discovery_coverage import CoverageCell,blind_cells,evidence_state
from contradiction_engine import claim_state
from discovery_failure import DiscoveryFailure,validate_failure
def test_discovery_method_optimizes_accepted_outcome_not_volume():
 b=MethodRun("b",100,10,10,5,10,10,1000)
 c=MethodRun("c",30,10,2,3,10,8,800)
 assert compare(b,c)=="PROMOTE_CANDIDATE"
def test_zero_accepted_does_not_fake_zero_cost():
 assert metrics(MethodRun("x",10,0,3,2,0,5,10))["cost_per_accepted"] is None
def test_unsearched_cell_is_not_negative_evidence():
 c=CoverageCell("Turkey","gears","gear","20MnCr5","END_USER","OFFICIAL_COMPANY","application-first")
 assert blind_cells([c])==(c,) and evidence_state(c)=="NOT_CHECKED"
def test_contradiction_beats_support_for_review():
 assert claim_state(checked=True,support_refs=("a",),contradiction_refs=("b",))=="CONTRADICTORY_EVIDENCE"
def test_specific_discovery_failure_requires_evidence():
 assert "specific_failure_requires_evidence" in validate_failure(DiscoveryFailure("case-1","QUERY_GAP"))
