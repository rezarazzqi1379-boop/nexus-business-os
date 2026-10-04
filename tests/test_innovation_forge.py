import pytest

from nexus_control_plane.innovation_forge import (
    ExperimentEvidence,
    ForgeStage,
    InnovationCandidate,
    candidate_from_audit,
    decide_candidate,
)
from nexus_control_plane.workflow_audit import ImprovementAction, WorkflowAuditResult


def audit(action: ImprovementAction) -> WorkflowAuditResult:
    return WorkflowAuditResult(
        workflow_id="procurement.rfq",
        projects_observed=3,
        observations=5,
        mean_duration_minutes=20,
        mean_manual_touches=5,
        rework_rate=0.6,
        duplicate_rate=0.0,
        late_blocker_rate=0.4,
        evidence_gap_rate=0.0,
        recommendation=action,
        reasons=("measured recurring pattern",),
    )


def test_keep_audit_does_not_create_cosmetic_innovation():
    assert candidate_from_audit(audit(ImprovementAction.KEEP), candidate_id="x", source_refs=("e:1",)) is None


def test_gate_candidate_is_safety_critical():
    candidate = candidate_from_audit(audit(ImprovementAction.ADD_GATE), candidate_id="gate:v1", source_refs=("e:1",))
    assert candidate is not None
    assert candidate.safety_critical is True


def test_missing_experiment_stays_experiment():
    candidate = InnovationCandidate("c:v1", ("e:1",), "problem", "change", "metric")
    decision = decide_candidate(candidate, None)
    assert decision.stage is ForgeStage.EXPERIMENT
    assert decision.requires_human_approval is True


def test_safety_regression_rejects_even_with_better_metric():
    candidate = InnovationCandidate("c:v1", ("e:1",), "problem", "change", "metric", True)
    evidence = ExperimentEvidence("c:v1", 4, 8, 0.5, 0.1, True, True, True)
    assert decide_candidate(candidate, evidence).stage is ForgeStage.REJECTED


def test_reproducible_cross_project_improvement_is_only_promotable_not_auto_promoted():
    candidate = InnovationCandidate("c:v1", ("e:1",), "problem", "change", "metric")
    evidence = ExperimentEvidence("c:v1", 3, 6, 0.5, 0.2, True, False, True)
    decision = decide_candidate(candidate, evidence)
    assert decision.stage is ForgeStage.PROMOTABLE
    assert decision.requires_human_approval is True


def test_candidate_mismatch_fails_closed():
    candidate = InnovationCandidate("c:v1", ("e:1",), "problem", "change", "metric")
    evidence = ExperimentEvidence("other", 3, 6, 1, 0, True, False, True)
    with pytest.raises(ValueError, match="mismatch"):
        decide_candidate(candidate, evidence)
