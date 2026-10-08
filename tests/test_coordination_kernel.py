from coordination_kernel import *

def s(**kw):
 d=dict(project_id="P",source_registry_version="1.8",master_id="M",master_version="2.1",repo_head="abc",ci_head="abc",ci_state="GREEN",decision_version="D1",ci_run="1270"); d.update(kw); return CoordinationState(**d)
def c(**kw):
 d=dict(project_id="P",objective="x",last_verified_head="abc",ci_run="1270",evidence_refs=("E1",),decisions=("D1",),unknowns=(),next_safe_action="research",decision_version="D1"); d.update(kw); return HandoffCapsule(**d)

def test_memory_never_authority_even_if_scope_named_canonical():
 for scope in StateScope: assert not memory_may_authorize(scope)
def test_cross_project_context_rejected():
 assert direction_guard(s(),"OTHER","D1")== (False,"PROJECT_ISOLATION")
def test_stale_ci_rejected():
 assert direction_guard(s(ci_head="old"),"P","D1")== (False,"REFRESH_EXACT_HEAD_CI")
def test_pivot_requires_reconciliation():
 assert direction_guard(s(),"P","D2")== (False,"PIVOT_RECONCILIATION_REQUIRED")
def test_valid_handoff_resumes():
 assert validate_handoff(c(),s())==(True,"RESUMABLE")
def test_stale_handoff_rejected():
 assert validate_handoff(c(last_verified_head="old"),s())==(False,"STALE_HANDOFF")
def test_forged_or_stale_ci_run_rejected():
 assert validate_handoff(c(ci_run="1269"),s())==(False,"CI_RUN_MISMATCH")
def test_missing_state_ci_run_rejected():
 assert validate_handoff(c(),s(ci_run=""))==(False,"CI_RUN_MISMATCH")
def test_missing_evidence_rejected():
 assert validate_handoff(c(evidence_refs=()),s())==(False,"MISSING_EVIDENCE")
def test_decision_drift_rejected():
 assert validate_handoff(c(decision_version="D0"),s())==(False,"DECISION_DRIFT")
def test_protected_handoff_stops_at_gate():
 assert validate_handoff(c(protected_action=True),s())==(False,"ACTION_GATE")
