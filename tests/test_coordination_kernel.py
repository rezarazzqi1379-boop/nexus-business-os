from coordination_kernel import *

def s(**kw):
 d=dict(project_id="P",source_registry_version="1.8",master_id="M",master_version="2.1",repo_head="abc",ci_head="abc",ci_state="GREEN",decision_version="D1"); d.update(kw); return CoordinationState(**d)
def c(**kw):
 d=dict(project_id="P",objective="x",last_verified_head="abc",ci_run="1250",evidence_refs=("E1",),decisions=("D1",),unknowns=(),next_safe_action="research"); d.update(kw); return HandoffCapsule(**d)

def test_session_memory_never_authority():
 assert not memory_may_authorize(StateScope.SESSION)
 assert memory_may_authorize(StateScope.CANONICAL)
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
def test_protected_handoff_stops_at_gate():
 assert validate_handoff(c(protected_action=True),s())==(False,"ACTION_GATE")
