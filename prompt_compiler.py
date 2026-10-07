"""Compile a minimal governed NEXUS execution contract."""
_ALLOWED_MATURITY={"DESIGNED","IMPLEMENTED","TESTED","BENCHMARKED","INTEGRATED","ACTIVE","DEPLOYED","PRODUCTION"}

def compile_prompt(*,project_id:str,stage:str,blocker:str,adapters:tuple[str,...],evidence_authority:str="CANONICAL_PROJECT_EVIDENCE",acceptance_test:str="REQUIRED_BEFORE_PROMOTION",maturity:str="TESTED",capability_policy:str="NO_EXPANSION_WITHOUT_MEASURED_BOTTLENECK",approval_boundary:str="STOP_BEFORE_PROTECTED_ACTION",input_contract:str="RECOVERED_CANONICAL_AND_LIVE_EVIDENCE",output_contract:str="REVIEWABLE_EVIDENCE_BOUND_RESULT",stop_condition:str="BLOCKER_OR_PROTECTED_GATE",measure:str="ACCEPTANCE_TEST_RESULT",record_target:str="VERSIONED_PROJECT_STATE")->str:
 if not project_id or not stage or not blocker: raise ValueError("incomplete_execution_context")
 if not evidence_authority or not acceptance_test: raise ValueError("evidence_and_acceptance_contract_required")\n if not all((input_contract,output_contract,stop_condition,measure,record_target)): raise ValueError("execution_contract_incomplete")
 if maturity not in _ALLOWED_MATURITY: raise ValueError("invalid_maturity_state")
 stage_contracts={
  "RECOVERY":"READ_ONLY; recover Registry/Master/live state; no promotion",
  "TECHNICAL":"PRIMARY_EVIDENCE; exact spec/edition; ambiguity fail-closed",
  "COMMERCIAL_GRAPH":"CURRENT_EVIDENCE; relationship/demand are separate claims",
  "CONVERSION":"NO_VOLUME_PROXY; require canonical conversion/readiness/stock gates",
  "SOURCE_ROI":"SANDBOX_ONLY; measure unique qualified evidence/cost/latency",
  "LEARNING":"VERSIONED_CHANGE; acceptance test + rollback required",
  "ACTION_GATE":"PROTECTED; exact target/payload/version approval required",
 }
 contract=stage_contracts.get(stage,"GOVERNED_STAGE; smallest measured reversible action")
 a=", ".join(adapters) if adapters else "NONE"
 return (
  "LOAD NEXUS_GLOBAL_KERNEL_V1.\n"
  f"PROJECT={project_id}\nSTAGE={stage}\nSTAGE_CONTRACT={contract}\nBLOCKER={blocker}\nALLOWED_ADAPTERS={a}\n"
  f"EVIDENCE_AUTHORITY={evidence_authority}\nACCEPTANCE_TEST={acceptance_test}\n"
  f"CURRENT_MATURITY={maturity}\nCAPABILITY_POLICY={capability_policy}\n"
  f"APPROVAL_BOUNDARY={approval_boundary}\n"\n  f"INPUT_CONTRACT={input_contract}\nOUTPUT_CONTRACT={output_contract}\n"\n  f"STOP_CONDITION={stop_condition}\nMEASURE={measure}\nRECORD_TARGET={record_target}\n"
  "Recover Source Registry/canonical master/live dynamic state first. "
  "Treat adapters and external GitHub systems as non-authoritative. "
  "Reverse-engineer useful mechanisms; do not duplicate orchestration. "
  "Execute only the smallest measured stage. Preserve provenance/project isolation/contradictions. "
  "On red test stop expansion, apply minimal fix, add regression, rerun. "
  "Promote maturity only from evidence. Test, read-back, measure, persist, and stop at protected gates."
 )
