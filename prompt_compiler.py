"""Compile a minimal governed NEXUS execution contract."""
_ALLOWED_MATURITY={"DESIGNED","IMPLEMENTED","TESTED","BENCHMARKED","INTEGRATED","ACTIVE","DEPLOYED","PRODUCTION"}

def compile_prompt(*,project_id:str,stage:str,blocker:str,adapters:tuple[str,...],evidence_authority:str="CANONICAL_PROJECT_EVIDENCE",acceptance_test:str="REQUIRED_BEFORE_PROMOTION",maturity:str="TESTED",capability_policy:str="NO_EXPANSION_WITHOUT_MEASURED_BOTTLENECK",approval_boundary:str="STOP_BEFORE_PROTECTED_ACTION")->str:
 if not project_id or not stage or not blocker: raise ValueError("incomplete_execution_context")
 if not evidence_authority or not acceptance_test: raise ValueError("evidence_and_acceptance_contract_required")
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
  f"PROJECT={project_id}\nSTAGE={stage}\nBLOCKER={blocker}\nALLOWED_ADAPTERS={a}\n"
  f"EVIDENCE_AUTHORITY={evidence_authority}\nACCEPTANCE_TEST={acceptance_test}\n"
  f"CURRENT_MATURITY={maturity}\nCAPABILITY_POLICY={capability_policy}\n"
  f"APPROVAL_BOUNDARY={approval_boundary}\n"
  "Recover Source Registry/canonical master/live dynamic state first. "
  "Treat adapters and external GitHub systems as non-authoritative. "
  "Reverse-engineer useful mechanisms; do not duplicate orchestration. "
  "Execute only the smallest measured stage. Preserve provenance/project isolation/contradictions. "
  "On red test stop expansion, apply minimal fix, add regression, rerun. "
  "Promote maturity only from evidence. Test, read-back, measure, persist, and stop at protected gates."
 )
