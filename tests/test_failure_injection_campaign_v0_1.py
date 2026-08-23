from nexus_control_plane.live_telemetry import TelemetryEvent, TelemetryKind, summarize_telemetry
from nexus_control_plane.memory_lifecycle import MemoryRecord, MemoryStatus, MemoryUse, evaluate_memory_for_use
from nexus_control_plane.next_best_action import ActionCandidate, rank_next_best_actions
from nexus_control_plane.outcome_graph import OutcomeRecord, OutcomeStage, evaluate_outcome_transition
from nexus_control_plane.recovery_runtime import RecoveryAction, RecoveryCheckpoint, RecoveryInput, decide_recovery
from nexus_control_plane.source_authority import AuthorityDecision, AuthorityTier, SourceRecord, resolve_same_scope_candidates


def test_injection_stale_memory_is_excluded_from_decision_context():
    record = MemoryRecord("m1", "KCL", "quote:old", MemoryStatus.SUPERSEDED, "2026-01-01", superseded_by="quote:new")
    result = evaluate_memory_for_use(record, project_id="KCL", use=MemoryUse.DECISION_CONTEXT)
    assert result.include is False


def test_injection_two_active_tier_a_sources_stop_authority_resolution():
    a = SourceRecord("a", "HYDRO", "1", "active", AuthorityTier.A_CANONICAL, "throughput", "2026-08-20")
    b = SourceRecord("b", "HYDRO", "2", "active", AuthorityTier.A_CANONICAL, "throughput", "2026-08-21")
    result = resolve_same_scope_candidates((a, b), expected_project_id="HYDRO", consequential=True)
    assert result.decision is AuthorityDecision.BLOCK_CONFLICT


def test_injection_cross_project_outcome_is_contained():
    prior = OutcomeRecord("o1", "KCL", OutcomeStage.RFQ, ("gmail:kcl",))
    candidate = OutcomeRecord("o2", "HYDRO", OutcomeStage.QUOTE, ("file:hydro",))
    result = evaluate_outcome_transition(prior, candidate)
    assert result.allowed is False


def test_injection_duplicate_telemetry_event_is_rejected():
    events = (
        TelemetryEvent("dup", "KCL", TelemetryKind.TOOL, "one", 1),
        TelemetryEvent("dup", "KCL", TelemetryKind.TOOL, "two", 2),
    )
    try:
        summarize_telemetry(events)
        assert False, "expected duplicate telemetry rejection"
    except ValueError:
        pass


def test_injection_state_corruption_rewinds_to_verified_reversible_checkpoint():
    cp = RecoveryCheckpoint("cp1", "state:good", ("evidence:1",), verified=True, reversible=True)
    result = decide_recovery(RecoveryInput("state_corruption", False, True, 0, 1, False, (cp,)))
    assert result.action is RecoveryAction.REWIND
    assert result.checkpoint_id == "cp1"


def test_injection_epistemic_deadlock_is_avoided_without_authorizing_material_action():
    verify = ActionCandidate(
        action_id="verify",
        project_id="HTL",
        action_type="verification",
        evidence_readiness=0.8,
        expected_value=0.5,
        information_gain=1.0,
        urgency=0.5,
        reversibility=1.0,
        risk=0.1,
        cost=0.1,
        dependency_ready=True,
        source_authority_ok=False,
        unresolved_contradictions=2,
        prior_failures_consulted=True,
        epistemic_resolution=True,
    )
    material = ActionCandidate(
        action_id="commit",
        project_id="HTL",
        action_type="external_commitment",
        evidence_readiness=1.0,
        expected_value=1.0,
        information_gain=0.0,
        urgency=1.0,
        reversibility=0.0,
        risk=0.8,
        cost=0.8,
        dependency_ready=True,
        source_authority_ok=False,
        unresolved_contradictions=2,
        prior_failures_consulted=True,
        human_gate_required=True,
    )
    ranked = rank_next_best_actions((material, verify))
    by_id = {item.candidate.action_id: item for item in ranked}
    assert by_id["verify"].blocked is False
    assert by_id["commit"].blocked is True
