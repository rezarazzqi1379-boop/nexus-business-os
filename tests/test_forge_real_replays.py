from nexus_control_plane.forge import (
    BenchmarkResult,
    FailureDisposition,
    MetricPair,
    PromotionDecision,
    Reconstruction,
    ReverseEngineeringSnapshot,
    TargetKind,
    build_pr19_evolution_payload,
    classify_failure,
    evaluate_promotion,
)
from nexus_control_plane.workforce import EvidenceClass, catalog
from nexus_control_plane.workforce_orchestrator import WorkflowKind, compile_workflow


def test_public_pattern_reconstruction_replay_is_source_grounded_and_bounded():
    """Replay the real PR #35 public-pattern experiment through Forge contracts.

    This proves architecture/contract integration only. It does not claim access to
    paid/private Altari internals or business-performance superiority.
    """
    public = tuple(item for item in catalog() if item.evidence_class is EvidenceClass.OBSERVED_PUBLIC)
    assert public
    assert all(item.source_ref for item in public)

    snapshot = ReverseEngineeringSnapshot(
        snapshot_id="forge-replay-altari-public-v0-1",
        target_id="altari-skilltree-public-patterns",
        target_kind=TargetKind.SYSTEM,
        source_refs=(
            "https://altari.ai/",
            "https://skilltree.altari.ai/",
            "github:PR35",
        ),
        observed_mechanisms=(
            "department-oriented capability catalog",
            "reusable job/capability labels",
            "workflow composition from capability primitives",
        ),
        unknowns=(
            "paid/private workflow internals are not observable",
            "private prompts, credentials, routing and orchestration are unknown",
        ),
        constraints=(
            "reconstruct behavior only from public evidence",
            "do not claim exact clone or access to private implementation",
        ),
    )
    reconstruction = Reconstruction(
        reconstruction_id="nexus-workforce-public-pattern-reconstruction-v0-1",
        source_snapshot_id=snapshot.snapshot_id,
        reproduced_mechanisms=(
            "department-oriented capability catalog",
            "workflow composition from capability primitives",
        ),
        evidence_refs=("github:PR35:workforce.py", "github:PR35:workforce_orchestrator.py"),
    )
    assert reconstruction.source_snapshot_id == snapshot.snapshot_id
    assert set(reconstruction.reproduced_mechanisms).issubset(set(snapshot.observed_mechanisms))


def test_procurement_workflow_replay_proves_forge_adds_control_contract_not_business_roi():
    """Replay a real NEXUS procurement template and benchmark contract controls.

    Metrics are binary contract checks, not probabilities or commercial KPIs.
    """
    plan = compile_workflow(
        WorkflowKind.PROCUREMENT,
        available_inputs=("business_goal",),
    )
    assert plan.runnable
    assert plan.runnable[0].step.step_id == "discover"

    benchmark = BenchmarkResult(
        benchmark_id="procurement-forge-contract-v0-1",
        reconstruction_id="nexus-workforce-public-pattern-reconstruction-v0-1",
        metrics={
            "source_grounding_contract": MetricPair(0.0, 1.0),
            "strict_stage_transition_contract": MetricPair(0.0, 1.0),
            "promotion_human_gate_contract": MetricPair(0.0, 1.0),
        },
        evidence_refs=(
            "github:PR35:workforce_orchestrator.py",
            "github:PR36:forge.py",
            "github:PR36:test_forge.py",
        ),
    )
    decision = evaluate_promotion(benchmark, minimum_gain=1.0)
    assert decision.decision is PromotionDecision.PROMOTABLE
    assert decision.requires_human_approval is True


def test_failure_learning_replay_contains_risk_and_emits_existing_pr19_contract():
    """A risky local failure is contained and converted to the existing learning contract."""
    disposition = classify_failure(isolated=True, consequential_risk=True)
    assert disposition is FailureDisposition.CONTAIN_AFFECTED_ACTION

    payload = build_pr19_evolution_payload(
        proposal_id="forge-replay-duplicate-framework-v0-1",
        component="nexus_control_plane",
        hypothesis="reusing canonical capabilities reduces parallel-framework duplication",
        change_summary="route reconstruction output into existing capability primitives and PR19 evolution evaluation",
        source_observations=(
            "github:PR30:architecture-sprawl-checkpoint",
            "github:PR36:base-contamination-detected-and-corrected",
        ),
        expected_metric="parallel_framework_count",
        max_regression=0.0,
    )
    assert payload["component"] == "nexus_control_plane"
    assert payload["max_regression"] == 0.0
    assert set(payload) == {
        "proposal_id",
        "component",
        "hypothesis",
        "change_summary",
        "source_observations",
        "expected_metric",
        "max_regression",
    }
