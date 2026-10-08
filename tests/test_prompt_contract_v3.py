from prompt_contract import *

def test_operator_v3_contract_is_complete():
 assert PROMPT_VERSION=="nexus.operator.v3"
 assert validate_prompt_contract()==()

def test_global_operator_prompt_contains_no_project_dynamic_facts():
 assert not prompt_contains_project_dynamic_facts()

def test_v3_uses_canonical_execution_loop_and_live_refresh():
 assert "RECOVER -> UNDERSTAND -> RETRIEVE -> RESOLVE -> VERIFY -> PLAN -> EXECUTE -> TEST -> CHECK" in INSTRUCTIONS
 assert "dynamic facts live" in INSTRUCTIONS

def test_v3_separates_measurement_and_hypothesis():
 assert "measurements" in REQUIRED_OUTPUT_KEYS
 assert "hypotheses" in REQUIRED_OUTPUT_KEYS
 assert "maturity_state" in REQUIRED_OUTPUT_KEYS

def test_v3_preserves_commercial_false_promotion_guards():
 for x in ("Historical demand is not current demand","Bidder is not winner","Repeated mirrors are not independent evidence","A score is not proof"):
  assert x in INSTRUCTIONS

def test_v3_keeps_external_actions_exactly_gated():
 assert "exact approval" in INSTRUCTIONS
 assert "Sending, publishing, paying, signing, ordering" in INSTRUCTIONS
