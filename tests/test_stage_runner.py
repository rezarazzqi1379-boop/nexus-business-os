from stage_runner import *
def test_current_commercial_bottleneck_routes_primary_docs_first():
 assert next_stage(recovery_ok=True,primary_docs_ok=False,technical_ok=False,stock_ok=False,eligibility_ok=False,relationship_ok=False,evidence_ready=False)=="PRIMARY_DOCUMENT"
def test_stock_blocks_after_technical_truth():
 assert next_stage(recovery_ok=True,primary_docs_ok=True,technical_ok=True,stock_ok=False,eligibility_ok=False,relationship_ok=False,evidence_ready=False)=="STOCK"
def test_protected_action_only_after_evidence_ready():
 assert next_stage(recovery_ok=True,primary_docs_ok=True,technical_ok=True,stock_ok=True,eligibility_ok=True,relationship_ok=True,evidence_ready=True,protected_action_requested=True)=="ACTION_GATE"

def test_capability_growth_is_not_a_parallel_commercial_stage():
 assert capability_review_stage(measured_repeated_bottleneck=False,acceptance_test_defined=False)=="NO_CAPABILITY_EXPANSION"

def test_measured_bottleneck_without_acceptance_test_routes_learning():
 assert capability_review_stage(measured_repeated_bottleneck=True,acceptance_test_defined=False)=="LEARNING"

def test_capability_candidate_with_measurement_and_acceptance_routes_source_roi():
 assert capability_review_stage(measured_repeated_bottleneck=True,acceptance_test_defined=True)=="SOURCE_ROI"

def test_commercial_conversion_route_remains_canonical_after_capability_integration():
 assert next_stage(recovery_ok=True,primary_docs_ok=True,technical_ok=True,stock_ok=True,eligibility_ok=True,relationship_ok=True,evidence_ready=False)=="CONVERSION"
