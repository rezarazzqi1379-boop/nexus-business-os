from nexus_control_plane.live_telemetry import TelemetryEvent, TelemetryKind, summarize_telemetry
from nexus_control_plane.next_best_action import ActionCandidate, rank_next_best_actions
from nexus_control_plane.outcome_graph import OutcomeRecord, OutcomeStage, evaluate_outcome_transition


def test_live_telemetry_summarizes_observed_events_without_inference():
    events = (
        TelemetryEvent("e1", "KCL", TelemetryKind.DECISION, "qualify supplier", 120, tool_calls=2, context_units=20, accepted_decision=True),
        TelemetryEvent("e2", "KCL", TelemetryKind.RECOVERY, "recover connector", 80, recoverable_failure=True, recovered_failure=True),
        TelemetryEvent("e3", "KCL", TelemetryKind.HUMAN_OVERRIDE, "override draft", 20, human_override=True, success=False),
    )
    s = summarize_telemetry(events)
    assert s.event_count == 3
    assert s.accepted_decisions == 1
    assert s.mean_latency_ms == 220 / 3
    assert s.recovery_rate == 1.0
    assert s.human_overrides == 1
    assert s.tool_calls_per_accepted_decision == 2.0


def test_telemetry_rejects_recovered_failure_without_recoverable_failure():
    events = (TelemetryEvent("e1", "KCL", TelemetryKind.RECOVERY, "bad event", 1, recovered_failure=True),)
    try:
        summarize_telemetry(events)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_telemetry_rejects_duplicate_event_ids():
    events = (
        TelemetryEvent("dup", "KCL", TelemetryKind.TOOL, "a", 1),
        TelemetryEvent("dup", "KCL", TelemetryKind.TOOL, "b", 1),
    )
    try:
        summarize_telemetry(events)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_outcome_graph_allows_evidence_linked_same_project_progress():
    prior = OutcomeRecord("o1", "KCL", OutcomeStage.RFQ, ("gmail:rfq",), decision_ref="d1")
    candidate = OutcomeRecord("o2", "KCL", OutcomeStage.QUOTE, ("file:quote",), decision_ref="d2")
    result = evaluate_outcome_transition(prior, candidate)
    assert result.allowed is True


def test_outcome_graph_blocks_cross_project_contamination():
    prior = OutcomeRecord("o1", "KCL", OutcomeStage.RFQ, ("gmail:rfq",))
    candidate = OutcomeRecord("o2", "HYDRO", OutcomeStage.QUOTE, ("file:quote",))
    result = evaluate_outcome_transition(prior, candidate)
    assert result.allowed is False
    assert "cross-project" in " ".join(result.reasons)


def test_outcome_graph_requires_decision_ref_for_order_or_later():
    prior = OutcomeRecord("o1", "KCL", OutcomeStage.NEGOTIATION, ("gmail:neg",))
    candidate = OutcomeRecord("o2", "KCL", OutcomeStage.ORDER, ("file:po",))
    result = evaluate_outcome_transition(prior, candidate)
    assert result.allowed is False
    assert "decision reference" in " ".join(result.reasons)


def _candidate(action_id, **overrides):
    data = dict(
        action_id=action_id,
        project_id="KCL",
        action_type="research",
        evidence_readiness=0.8,
        expected_value=0.7,
        information_gain=0.7,
        urgency=0.5,
        reversibility=0.9,
        risk=0.2,
        cost=0.2,
        dependency_ready=True,
        source_authority_ok=True,
        unresolved_contradictions=0,
        prior_failures_consulted=True,
        human_gate_required=False,
    )
    data.update(overrides)
    return ActionCandidate(**data)


def test_nba_prefers_high_information_low_risk_ready_action():
    a = _candidate("a", information_gain=0.95, risk=0.1, cost=0.1)
    b = _candidate("b", information_gain=0.2, risk=0.7, cost=0.8)
    ranked = rank_next_best_actions((b, a))
    assert ranked[0].candidate.action_id == "a"
    assert ranked[0].blocked is False
    assert ranked[0].ranking_is_advisory is True


def test_nba_blocks_high_score_when_source_authority_is_bad():
    blocked = _candidate("blocked", expected_value=1.0, information_gain=1.0, source_authority_ok=False)
    safe = _candidate("safe", expected_value=0.4, information_gain=0.4)
    ranked = rank_next_best_actions((blocked, safe))
    assert ranked[0].candidate.action_id == "safe"
    assert ranked[1].candidate.action_id == "blocked"
    assert ranked[1].blocked is True


def test_nba_blocks_unresolved_contradiction_and_unconsulted_failure():
    x = _candidate("x", unresolved_contradictions=1)
    y = _candidate("y", prior_failures_consulted=False)
    ranked = rank_next_best_actions((x, y))
    assert all(item.blocked for item in ranked)


def test_nba_human_gate_does_not_block_ranking_but_never_authorizes_execution():
    x = _candidate("x", human_gate_required=True)
    ranked = rank_next_best_actions((x,))
    assert ranked[0].blocked is False
    assert "human gate" in " ".join(ranked[0].reasons)
    assert ranked[0].ranking_is_advisory is True


def test_nba_allows_epistemic_resolution_to_break_contradiction_deadlock():
    verify = _candidate(
        "verify",
        action_type="verification",
        source_authority_ok=False,
        unresolved_contradictions=2,
        information_gain=1.0,
        epistemic_resolution=True,
    )
    ranked = rank_next_best_actions((verify,))
    assert ranked[0].blocked is False
    joined = " ".join(ranked[0].reasons)
    assert "limited to resolving" in joined or "limited to verification" in joined
    assert "does not establish the missing fact" in joined


def test_epistemic_resolution_does_not_bypass_dependencies_or_failure_memory():
    verify = _candidate(
        "verify",
        action_type="verification",
        source_authority_ok=False,
        unresolved_contradictions=1,
        epistemic_resolution=True,
        dependency_ready=False,
        prior_failures_consulted=False,
    )
    ranked = rank_next_best_actions((verify,))
    assert ranked[0].blocked is True
    joined = " ".join(ranked[0].reasons)
    assert "dependency is not ready" in joined
    assert "prior failures" in joined
