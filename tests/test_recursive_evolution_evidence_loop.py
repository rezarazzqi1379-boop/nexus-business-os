import pytest

from nexus_control_plane.contradiction_graph import (
    ContradictionRecord,
    ContradictionStatus,
    evaluate_contradictions,
)
from nexus_control_plane.generation_decision_gate import finalize_generation_with_evidence
from nexus_control_plane.generation_ledger import GenerationLedgerEntry, validate_generation_chain
from nexus_control_plane.outcome_gate import OutcomeDecision, OutcomeSignal, evaluate_outcomes
from nexus_control_plane.recursive_evolution import (
    EvolutionBudget,
    GenerationDecision,
    GenerationTelemetry,
    evaluate_generation,
)


def stopped_audit(generation_id: str = "g1"):
    telemetry = GenerationTelemetry(
        generation_id=generation_id,
        actions_used=10,
        cost_units_used=1.0,
        runtime_seconds=1.0,
        retries_used=0,
        failures=0,
        evaluations=5,
        minimum_gain=0.10,
    )
    return evaluate_generation(
        telemetry,
        EvolutionBudget(max_actions=10, max_cost_units=100, max_runtime_seconds=100, max_retries=2),
    )


def improved_signal() -> OutcomeSignal:
    return OutcomeSignal(
        signal_id="outcome:1",
        decision_id="decision:1",
        metric_name="verified_outcome_rate",
        baseline=0.20,
        candidate=0.30,
        evidence_refs=("evidence:baseline", "evidence:candidate"),
        terminal_outcome_observed=True,
    )


def test_open_contradiction_blocks_promotion_and_forces_research_refresh():
    gate = evaluate_contradictions((
        ContradictionRecord(
            contradiction_id="cx:1",
            subject="pipe thickness",
            claim_refs=("claim:old", "claim:new"),
            evidence_refs=("source:old", "source:new"),
        ),
    ))
    result = finalize_generation_with_evidence(
        stopped_audit(),
        contradiction_gate=gate,
        outcome_gate=evaluate_outcomes((improved_signal(),), require_terminal_outcome=True),
        outcome_required=True,
        independent_audit_passed=True,
        candidate_beats_baseline=True,
    )
    assert result.audit.decision is GenerationDecision.PLATEAU_RESEARCH_RESTART
    assert result.audit.research_refresh_required is True
    assert result.contradiction_refs == ("cx:1",)


def test_resolved_contradiction_does_not_block():
    gate = evaluate_contradictions((
        ContradictionRecord(
            contradiction_id="cx:1",
            subject="pipe thickness",
            claim_refs=("claim:old", "claim:new"),
            evidence_refs=("source:old", "source:new"),
            status=ContradictionStatus.RESOLVED,
            resolution_ref="decision:resolution",
        ),
    ))
    assert gate.promotion_blocked is False
    assert gate.open_count == 0


def test_outcome_regression_forces_rollback():
    signal = OutcomeSignal(
        signal_id="outcome:bad",
        decision_id="decision:1",
        metric_name="verified_outcome_rate",
        baseline=0.30,
        candidate=0.20,
        evidence_refs=("evidence:a", "evidence:b"),
        terminal_outcome_observed=True,
    )
    result = finalize_generation_with_evidence(
        stopped_audit(),
        contradiction_gate=evaluate_contradictions(()),
        outcome_gate=evaluate_outcomes((signal,), require_terminal_outcome=True),
        outcome_required=True,
        independent_audit_passed=True,
        candidate_beats_baseline=True,
    )
    assert result.audit.decision is GenerationDecision.ROLLBACK_RESTART
    assert result.audit.rollback_required is True


def test_missing_required_outcome_forces_plateau():
    result = finalize_generation_with_evidence(
        stopped_audit(),
        contradiction_gate=evaluate_contradictions(()),
        outcome_gate=None,
        outcome_required=True,
        independent_audit_passed=True,
        candidate_beats_baseline=True,
    )
    assert result.audit.decision is GenerationDecision.PLATEAU_RESEARCH_RESTART


def test_improved_outcome_plus_independent_audit_can_reach_human_gated_promotion():
    outcome = evaluate_outcomes((improved_signal(),), require_terminal_outcome=True, minimum_gain=0.01)
    assert outcome.decision is OutcomeDecision.IMPROVED
    result = finalize_generation_with_evidence(
        stopped_audit(),
        contradiction_gate=evaluate_contradictions(()),
        outcome_gate=outcome,
        outcome_required=True,
        independent_audit_passed=True,
        candidate_beats_baseline=True,
    )
    assert result.audit.decision is GenerationDecision.PROMOTE_RESTART
    assert result.audit.requires_human_approval is True


def test_non_business_generation_can_finalize_without_outcomes():
    result = finalize_generation_with_evidence(
        stopped_audit(),
        contradiction_gate=evaluate_contradictions(()),
        outcome_gate=None,
        outcome_required=False,
        independent_audit_passed=True,
        candidate_beats_baseline=True,
    )
    assert result.audit.decision is GenerationDecision.PROMOTE_RESTART


def test_generation_ledger_preserves_lineage_and_evidence_refs():
    a1 = stopped_audit("g1")
    e1 = GenerationLedgerEntry(
        generation_id="g1",
        baseline_version="v0",
        candidate_version="v1",
        audit=a1,
        evidence_refs=("ci:1",),
        decision_refs=("decision:1",),
        outcome_refs=("outcome:1",),
    )
    a2 = stopped_audit("g2")
    e2 = GenerationLedgerEntry(
        generation_id="g2",
        baseline_version="v1",
        candidate_version="v2",
        audit=a2,
        evidence_refs=("ci:2",),
        parent_generation_id="g1",
    )
    assert validate_generation_chain((e1, e2)) == ()


def test_generation_ledger_detects_missing_parent():
    entry = GenerationLedgerEntry(
        generation_id="g2",
        baseline_version="v1",
        candidate_version="v2",
        audit=stopped_audit("g2"),
        evidence_refs=("ci:2",),
        parent_generation_id="g1",
    )
    assert "missing or out-of-order parent: g1" in validate_generation_chain((entry,))


def test_generation_ledger_rejects_same_baseline_and_candidate():
    with pytest.raises(ValueError, match="candidate_version"):
        GenerationLedgerEntry(
            generation_id="g1",
            baseline_version="v1",
            candidate_version="v1",
            audit=stopped_audit(),
            evidence_refs=("ci:1",),
        )


def test_outcome_gate_does_not_invent_terminal_evidence():
    signal = OutcomeSignal(
        signal_id="outcome:reply",
        decision_id="decision:1",
        metric_name="reply_rate",
        baseline=0.1,
        candidate=0.2,
        evidence_refs=("evidence:a", "evidence:b"),
        terminal_outcome_observed=False,
    )
    result = evaluate_outcomes((signal,), require_terminal_outcome=True)
    assert result.decision is OutcomeDecision.INSUFFICIENT
    assert result.promotion_support is False


def test_contradiction_record_requires_real_resolution_reference():
    with pytest.raises(ValueError, match="resolution_ref"):
        ContradictionRecord(
            contradiction_id="cx:1",
            subject="requirement",
            claim_refs=("claim:a", "claim:b"),
            evidence_refs=("source:a", "source:b"),
            status=ContradictionStatus.RESOLVED,
        )
