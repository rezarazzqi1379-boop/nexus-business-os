from continuous_cycle import *
def c(**kw):
 d=dict(project_id="P",repo_head="H",ci_head="H",ci_state="GREEN",checkpoint_fresh=True); d.update(kw); return CycleContext(**d)
def test_stale_ci_or_head_forces_recovery(): assert next_cycle_state(c(ci_head="OLD"))==CycleState.RECOVER
def test_stale_checkpoint_forces_recovery(): assert next_cycle_state(c(checkpoint_fresh=False))==CycleState.RECOVER
def test_protected_action_is_gated(): assert next_cycle_state(c(protected_action=True))==CycleState.GATED
def test_incomplete_evidence_continues_research(): assert next_cycle_state(c())==CycleState.RESEARCH
def test_defect_routes_build_after_evidence(): assert next_cycle_state(c(evidence_ready=True,defect_found=True))==CycleState.BUILD
def test_safe_state_can_continue_but_gate_cannot():
 assert may_auto_continue(CycleState.RESEARCH)
 assert not may_auto_continue(CycleState.GATED)
