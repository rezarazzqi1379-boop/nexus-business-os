from procurement_adapter_gate import *
def test_popular_github_project_is_not_reason_to_integrate_without_coverage():
 assert adapter_decision(AdapterEvidence(10,0,5,2,1))=="HOLD_NO_DATA_COVERAGE"
def test_adapter_needs_incremental_qualified_hits():
 assert adapter_decision(AdapterEvidence(10,5,2,2,1))=="HOLD_NO_INCREMENTAL_VALUE"
def test_small_pilot_requires_coverage_gain_and_cost_case():
 assert adapter_decision(AdapterEvidence(10,5,6,2,2))=="PILOT_JUSTIFIED"
