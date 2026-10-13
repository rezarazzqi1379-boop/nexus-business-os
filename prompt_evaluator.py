"""Pre-execution evaluator for compiled NEXUS prompts."""
_REQUIRED=("PROJECT=","STAGE=","STAGE_CONTRACT=","BLOCKER=","EVIDENCE_AUTHORITY=","ACCEPTANCE_TEST=","CURRENT_MATURITY=","APPROVAL_BOUNDARY=","INPUT_CONTRACT=","OUTPUT_CONTRACT=","STOP_CONDITION=","MEASURE=","RECORD_TARGET=")

def prompt_ready(prompt:str)->bool:
 if not prompt or any(token not in prompt for token in _REQUIRED): return False
 if "Recover Source Registry/canonical master/live dynamic state first." not in prompt:return False
 if "stop at protected gates" not in prompt:return False
 return True

def missing_prompt_contracts(prompt:str)->tuple[str,...]:
 return tuple(token for token in _REQUIRED if token not in (prompt or ""))
