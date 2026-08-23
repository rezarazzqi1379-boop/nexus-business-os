import pytest

from nexus_control_plane.forge import (
    BenchmarkResult,
    FailureDisposition,
    ForgeStage,
    MetricPair,
    PromotionDecision,
    Reconstruction,
    ReverseEngineeringSnapshot,
    TargetKind,
    build_pr19_evolution_payload,
    classify_failure,
    evaluate_promotion,
    next_stage,
    validate_transition,
)


def test_forge_lifecycle_is_strict_and_cycles_only_after_evolve():
    assert next_stage(ForgeStage.OBSERVE) is ForgeStage.REVERSE_ENGINEER
    validate_transition(ForgeStage.REVERSE_ENGINEER, ForgeStage.RECONSTRUCT)
    with pytest.raises(ValueError):
        validate_transition(ForgeStage.REVERSE_ENGINEER, ForgeStage.IMPROVE)
    assert next_stage(ForgeStage.EVOLVE) is ForgeStage.OBSERVE


def test_reverse_engineering_requires_sources_and_mechanisms():
    with pytest.raises(ValueError):
        ReverseEngineeringSnapshot(
            snapshot_id="snap-1",
            target_id="agent-1",
            target_kind=TargetKind.AGENT,
            source_refs=(),
            observed_mechanisms=("retrieval",),
        )
    with pytest.raises(ValueError):
        ReverseEngineeringSnapshot(
            snapshot_id="snap-1",
            target_id="agent-1",
            target_kind=TargetKind.AGENT,
            source_refs=("https://example.com/source",),
            observed_mechanisms=(),
        )


def test_reconstruction_requires_reproduced_mechanism_and_evidence():
    with pytest.raises(ValueError):
        Reconstruction("recon-1", "snap-1", (), ("evidence:1",))
    with pytest.raises(ValueError):
        Reconstruction("recon-1", "snap-1", ("retrieval",), ())


def test_safety_regression_can_never_be_promotable():
    result = BenchmarkResult(
        benchmark_id="bench-1",
        reconstruction_id="recon-1",
        metrics={"quality": MetricPair(0.60, 0.90)},
        evidence_refs=("eval:1",),
        safety_regressions=("cross_project_contamination",),
    )
    decision = evaluate_promotion(result)
    assert decision.decision is PromotionDecision.REJECT
    assert decision.requires_human_approval is False


def test_all_required_metrics_must_clear_threshold_before_promotion():
    result = BenchmarkResult(
        benchmark_id="bench-1",
        reconstruction_id="recon-1",
        metrics={
            "quality": MetricPair(0.60, 0.80),
            "unsupported_claim_rate": MetricPair(0.05, 0.05, higher_is_better=False),
        },
        evidence_refs=("eval:1",),
    )
    decision = evaluate_promotion(result, minimum_gain=0.01)
    assert decision.decision is PromotionDecision.EXPERIMENT
    assert decision.requires_human_approval is False


def test_promotable_still_requires_human_approval():
    result = BenchmarkResult(
        benchmark_id="bench-1",
        reconstruction_id="recon-1",
        metrics={
            "quality": MetricPair(0.60, 0.80),
            "unsupported_claim_rate": MetricPair(0.08, 0.03, higher_is_better=False),
        },
        evidence_refs=("eval:1", "eval:2"),
    )
    decision = evaluate_promotion(result, minimum_gain=0.01)
    assert decision.decision is PromotionDecision.PROMOTABLE
    assert decision.requires_human_approval is True


def test_local_recoverable_failure_does_not_stop_unrelated_work():
    assert classify_failure(isolated=True, consequential_risk=False) is FailureDisposition.CONTINUE_ISOLATED
    assert classify_failure(isolated=True, consequential_risk=True) is FailureDisposition.CONTAIN_AFFECTED_ACTION
    assert classify_failure(isolated=False, consequential_risk=False) is FailureDisposition.CONTAIN_AFFECTED_ACTION


def test_learning_bridge_matches_pr19_evolution_contract_exactly():
    payload = build_pr19_evolution_payload(
        proposal_id="proposal-1",
        component="nexus_control_plane.workforce",
        hypothesis="candidate routing reduces duplicate work",
        change_summary="reuse canonical capability before creating a new agent",
        source_observations=("failure:duplicate-agent",),
        expected_metric="duplicate_agent_rate",
        max_regression=0.0,
    )
    assert set(payload) == {
        "proposal_id",
        "component",
        "hypothesis",
        "change_summary",
        "source_observations",
        "expected_metric",
        "max_regression",
    }
    assert payload["source_observations"] == ("failure:duplicate-agent",)
