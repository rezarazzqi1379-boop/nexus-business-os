from project_continuity import *

def cp(**kw):
 d=dict(project_id="NEXUS-BUSINESS-OS",source_registry_ref="NEXUS_Source_Registry_v1.8",master_ref="NEXUS_Master_Context_v2.1",repo_head="abc",ci_state="GREEN",ci_head="abc",stage="SOURCE_ROI",maturity="TESTED",evidence_refs=("ev1",),evidence_project_ids=("NEXUS-BUSINESS-OS",),blockers=(),next_safe_action="continue tested vertical")
 d.update(kw); return ProjectCheckpoint(**d)

def test_recovery_order_starts_with_authority_not_chat_memory():
 assert recovery_order()[:3]==("SOURCE_REGISTRY","CANONICAL_MASTER","PROJECT_CHECKPOINT")

def test_green_checkpoint_can_continue_without_reasking_state():
 assert may_continue_without_user_repetition(cp())

def test_red_ci_recovers_but_does_not_expand():
 assert validate_checkpoint(cp(ci_state="RED"))==ContinuityState.RECOVERABLE

def test_green_ci_for_old_commit_cannot_authorize_new_head():
 assert validate_checkpoint(cp(repo_head="new",ci_head="old"))==ContinuityState.RECOVERABLE

def test_missing_ci_head_binding_fails_closed():
 assert validate_checkpoint(cp(ci_head=""))==ContinuityState.RECOVERABLE

def test_stale_checkpoint_requires_recovery():
 assert validate_checkpoint(cp(checkpoint_fresh=False))==ContinuityState.RECOVERABLE

def test_cross_project_evidence_is_invalid():
 assert validate_checkpoint(cp(evidence_project_ids=("PRJ-HYD-01",)))==ContinuityState.INVALID

def test_protected_next_action_stays_gated_across_sessions():
 assert validate_checkpoint(cp(protected_action=True))==ContinuityState.GATED

def test_missing_evidence_cannot_become_authoritative_checkpoint():
 assert validate_checkpoint(cp(evidence_refs=()))==ContinuityState.INVALID
