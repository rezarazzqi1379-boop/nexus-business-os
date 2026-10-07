from project_continuity import *

def cp(**kw):
 d=dict(project_id="NEXUS-BUSINESS-OS",source_registry_ref="NEXUS_Source_Registry_v1.8",master_ref="NEXUS_Master_Context_v2.1",repo_head="abc",ci_state="GREEN",stage="SOURCE_ROI",maturity="TESTED",evidence_refs=("ev1",),blockers=(),next_safe_action="continue tested vertical")
 d.update(kw); return ProjectCheckpoint(**d)

def test_recovery_order_starts_with_authority_not_chat_memory():
 assert recovery_order()[:3]==("SOURCE_REGISTRY","CANONICAL_MASTER","PROJECT_CHECKPOINT")

def test_green_checkpoint_can_continue_without_reasking_state():
 assert may_continue_without_user_repetition(cp())

def test_red_ci_recovers_but_does_not_expand():
 assert validate_checkpoint(cp(ci_state="RED"))==ContinuityState.RECOVERABLE
 assert not may_continue_without_user_repetition(cp(ci_state="RED"))

def test_protected_next_action_stays_gated_across_sessions():
 assert validate_checkpoint(cp(protected_action=True))==ContinuityState.GATED

def test_missing_evidence_cannot_become_authoritative_checkpoint():
 assert validate_checkpoint(cp(evidence_refs=()))==ContinuityState.INVALID
