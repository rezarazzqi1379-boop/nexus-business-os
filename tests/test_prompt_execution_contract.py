import pytest
from prompt_compiler import compile_prompt
from prompt_evaluator import prompt_ready,missing_prompt_contracts

def test_compiled_prompt_is_self_evaluable_execution_contract():
 p=compile_prompt(project_id="PRJ-X",stage="CONVERSION",blocker="buyer_binding",adapters=("GitHub",),acceptance_test="verified_conversion_gain")
 assert prompt_ready(p)
 for token in ("INPUT_CONTRACT=","OUTPUT_CONTRACT=","STOP_CONDITION=","MEASURE=","RECORD_TARGET="):
  assert token in p

def test_incomplete_execution_contract_fails_closed():
 with pytest.raises(ValueError,match="execution_contract_incomplete"):
  compile_prompt(project_id="P",stage="RECOVERY",blocker="state",adapters=(),record_target="")

def test_evaluator_rejects_uncompiled_freeform_prompt():
 p="Research more and improve the system."
 assert not prompt_ready(p)
 assert "PROJECT=" in missing_prompt_contracts(p)
