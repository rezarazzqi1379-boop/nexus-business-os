from stage_runner import *
def test_current_commercial_bottleneck_routes_primary_docs_first():
 assert next_stage(recovery_ok=True,primary_docs_ok=False,technical_ok=False,stock_ok=False,eligibility_ok=False,relationship_ok=False,evidence_ready=False)=="PRIMARY_DOCUMENT"
def test_stock_blocks_after_technical_truth():
 assert next_stage(recovery_ok=True,primary_docs_ok=True,technical_ok=True,stock_ok=False,eligibility_ok=False,relationship_ok=False,evidence_ready=False)=="STOCK"
def test_protected_action_only_after_evidence_ready():
 assert next_stage(recovery_ok=True,primary_docs_ok=True,technical_ok=True,stock_ok=True,eligibility_ok=True,relationship_ok=True,evidence_ready=True,protected_action_requested=True)=="ACTION_GATE"
