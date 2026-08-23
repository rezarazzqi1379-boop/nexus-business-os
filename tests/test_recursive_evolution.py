import pytest

from nexus_control_plane.recursive_evolution import (
    EvolutionBudget,
    GenerationAudit,
    GenerationDecision,
    GenerationTelemetry,
    StopReason,
    evaluate_generation,
    finalize_stopped_generation,
)


def _budget():
    return EvolutionBudget(max_actions=100, max_cost_units=50.0, max_runtime_seconds=600.0, max_retries=5)


def _telemetry(**overrides):
    base = dict(
        generation_id="G1",
        actions_used=10,
        cost_units_used=5.0,
        runtime_seconds=60.0,
        retries_used=1,
        failures=1,
        evaluations=10,
        minimum_gain=0.05,
        safety_regressions=0,
        architecture_sprawl_events=0,
        contradiction_events=0,
    )
    base.update(overrides)
    return GenerationTelemetry(**base)


def test_healthy_generation_continues_without_authorizing_execution():
    audit = evaluate_generation(_telemetry(), _budget())
    assert audit.decision is GenerationDecision.CONTINUE
    assert audit.stop_reason is StopReason.NONE
    assert audit.requires_human_approval is False


def test_action_budget_forces_self_stop():
    audit = evaluate_generation(_telemetry(actions_used=100), _budget())
    assert audit.decision is GenerationDecision.SELF_STOP_AUDIT
    assert audit.stop_reason is StopReason.ACTION_BUDGET


def test_cost_budget_forces_self_stop():
    audit = evaluate_generation(_telemetry(cost_units_used=50.0), _budget())
    assert audit.stop_reason is StopReason.COST_BUDGET


def test_time_budget_forces_self_stop():
    audit = evaluate_generation(_telemetry(runtime_seconds=600.0), _budget())
    assert audit.stop_reason is StopReason.TIME_BUDGET


def test_retry_budget_forces_self_stop():
    audit = evaluate_generation(_telemetry(retries_used=5), _budget())
    assert audit.stop_reason is StopReason.RETRY_BUDGET


def test_safety_regression_has_priority_and_requires_rollback():
    audit = evaluate_generation(
        _telemetry(actions_used=100, safety_regressions=1),
        _budget(),
    )
    assert audit.stop_reason is StopReason.SAFETY_REGRESSION
    assert audit.decision is GenerationDecision.ROLLBACK_RESTART
    assert audit.rollback_required is True
    assert audit.requires_human_approval is False


def test_high_failure_rate_self_stops_generation():
    audit = evaluate_generation(_telemetry(failures=3, evaluations=10), _budget())
    assert audit.stop_reason is StopReason.FAILURE_RATE
    assert audit.decision is GenerationDecision.SELF_STOP_AUDIT


def test_architecture_sprawl_self_stops_before_budget_exhaustion():
    audit = evaluate_generation(_telemetry(architecture_sprawl_events=1), _budget())
    assert audit.stop_reason is StopReason.ARCHITECTURE_SPRAWL
    assert audit.decision is GenerationDecision.SELF_STOP_AUDIT


def test_contradiction_overload_stops_and_requires_research_refresh():
    audit = evaluate_generation(_telemetry(contradiction_events=1), _budget())
    assert audit.stop_reason is StopReason.CONTRADICTION_LOAD
    assert audit.research_refresh_required is True


def test_plateau_requires_research_refresh_instead_of_promotion():
    audit = evaluate_generation(_telemetry(minimum_gain=0.0), _budget())
    assert audit.stop_reason is StopReason.MARGINAL_GAIN
    assert audit.decision is GenerationDecision.PLATEAU_RESEARCH_RESTART
    assert audit.research_refresh_required is True


def test_successful_independent_audit_can_only_make_generation_promotable_with_human_gate():
    stopped = evaluate_generation(_telemetry(actions_used=100), _budget())
    final = finalize_stopped_generation(
        stopped,
        independent_audit_passed=True,
        candidate_beats_baseline=True,
    )
    assert final.decision is GenerationDecision.PROMOTE_RESTART
    assert final.requires_human_approval is True
    assert final.rollback_required is False


def test_failed_independent_audit_rolls_back_even_without_recorded_safety_regression():
    stopped = evaluate_generation(_telemetry(actions_used=100), _budget())
    final = finalize_stopped_generation(
        stopped,
        independent_audit_passed=False,
        candidate_beats_baseline=True,
    )
    assert final.decision is GenerationDecision.ROLLBACK_RESTART
    assert final.rollback_required is True


def test_candidate_that_does_not_beat_baseline_researches_and_restarts():
    stopped = evaluate_generation(_telemetry(actions_used=100), _budget())
    final = finalize_stopped_generation(
        stopped,
        independent_audit_passed=True,
        candidate_beats_baseline=False,
    )
    assert final.decision is GenerationDecision.PLATEAU_RESEARCH_RESTART
    assert final.research_refresh_required is True


def test_running_generation_cannot_be_finalized():
    running = evaluate_generation(_telemetry(), _budget())
    with pytest.raises(ValueError):
        finalize_stopped_generation(running, independent_audit_passed=True, candidate_beats_baseline=True)


def test_invalid_budget_is_rejected():
    with pytest.raises(ValueError):
        EvolutionBudget(max_actions=0, max_cost_units=1.0, max_runtime_seconds=1.0, max_retries=0)
