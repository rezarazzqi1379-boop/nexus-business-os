import pytest
from prompt_compiler import compile_prompt

def test_compiled_prompt_is_execution_contract():
 p=compile_prompt(project_id="PRJ-X",stage="SOURCE_ROI",blocker="qualified_evidence_yield",adapters=("GitHub","Search"),acceptance_test="unique qualified evidence improves")
 for required in ("PROJECT=PRJ-X","STAGE=SOURCE_ROI","EVIDENCE_AUTHORITY=","ACCEPTANCE_TEST=unique qualified evidence improves","CURRENT_MATURITY=TESTED","CAPABILITY_POLICY=","APPROVAL_BOUNDARY="):
  assert required in p

def test_external_systems_are_non_authoritative():
 p=compile_prompt(project_id="PRJ-X",stage="SOURCE_ROI",blocker="x",adapters=("Browser4","Strands"))
 assert "external GitHub systems as non-authoritative" in p
 assert "do not duplicate orchestration" in p

def test_invalid_maturity_fails_closed():
 with pytest.raises(ValueError,match="invalid_maturity"):
  compile_prompt(project_id="P",stage="S",blocker="B",adapters=(),maturity="MAGIC")

def test_missing_evidence_or_acceptance_contract_fails_closed():
 with pytest.raises(ValueError,match="evidence_and_acceptance"):
  compile_prompt(project_id="P",stage="S",blocker="B",adapters=(),evidence_authority="")
