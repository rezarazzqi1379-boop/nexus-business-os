from nexus_control_plane.intelligence_benchmark import IntelligenceMetrics, compare_intelligence


def baseline() -> IntelligenceMetrics:
    return IntelligenceMetrics(
        accepted_decisions=10,
        stale_memory_rejections=1,
        source_authority_violations=1,
        cross_project_contamination=1,
        contradictions_detected=2,
        recoverable_failures=4,
        recovered_failures=2,
        human_overrides=2,
        duplicate_actions=2,
        tool_calls=50,
        context_units=1000,
    )


def candidate() -> IntelligenceMetrics:
    return IntelligenceMetrics(
        accepted_decisions=10,
        stale_memory_rejections=4,
        source_authority_violations=0,
        cross_project_contamination=0,
        contradictions_detected=4,
        recoverable_failures=4,
        recovered_failures=4,
        human_overrides=1,
        duplicate_actions=0,
        tool_calls=36,
        context_units=620,
    )


def test_candidate_can_be_replay_promotable_when_it_improves_without_regression():
    delta = compare_intelligence(baseline(), candidate())
    assert delta.promotable is True
    assert delta.recovery_rate_delta == 0.5
    assert delta.source_authority_violation_delta == -1
    assert delta.cross_project_contamination_delta == -1
    assert delta.duplicate_action_delta == -2
    assert delta.tool_calls_per_decision_delta < 0
    assert delta.context_units_per_decision_delta < 0


def test_any_authority_regression_blocks_replay_promotion():
    bad = IntelligenceMetrics(**{**candidate().__dict__, "source_authority_violations": 2})
    delta = compare_intelligence(baseline(), bad)
    assert delta.promotable is False
    assert "source-authority violations regressed" in delta.reasons


def test_no_improvement_is_not_promotable():
    delta = compare_intelligence(baseline(), baseline())
    assert delta.promotable is False
    assert "no measurable replay improvement" in delta.reasons
