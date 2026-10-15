from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .workflow_audit import ImprovementAction, WorkflowAuditResult


class ForgeStage(str, Enum):
    DISCOVERED = "discovered"
    RECONSTRUCTED = "reconstructed"
    BENCHMARKED = "benchmarked"
    ADVERSARIAL_TESTED = "adversarial_tested"
    EXPERIMENT = "experiment"
    PROMOTABLE = "promotable"
    REJECTED = "rejected"


@dataclass(frozen=True)
class InnovationCandidate:
    candidate_id: str
    source_refs: tuple[str, ...]
    problem_statement: str
    proposed_change: str
    baseline_metric: str
    safety_critical: bool = False

    def validate(self) -> None:
        if not self.candidate_id or self.candidate_id.strip() != self.candidate_id:
            raise ValueError("candidate_id must be canonical")
        if not self.source_refs or any(not ref or ref.strip() != ref for ref in self.source_refs):
            raise ValueError("source_refs must contain canonical references")
        if len(set(self.source_refs)) != len(self.source_refs):
            raise ValueError("source_refs must be unique")
        if not self.problem_statement.strip() or not self.proposed_change.strip():
            raise ValueError("problem_statement and proposed_change are required")
        if not self.baseline_metric.strip():
            raise ValueError("baseline_metric is required")


@dataclass(frozen=True)
class ExperimentEvidence:
    candidate_id: str
    projects_observed: int
    observations: int
    baseline_value: float | None
    candidate_value: float | None
    lower_is_better: bool
    safety_regression: bool
    reproducible: bool

    def validate(self) -> None:
        if self.projects_observed < 0 or self.observations < 0:
            raise ValueError("counts must be non-negative")
        if self.baseline_value is not None and self.baseline_value < 0:
            raise ValueError("baseline_value must be non-negative")
        if self.candidate_value is not None and self.candidate_value < 0:
            raise ValueError("candidate_value must be non-negative")


@dataclass(frozen=True)
class ForgeDecision:
    stage: ForgeStage
    reasons: tuple[str, ...]
    requires_human_approval: bool


def candidate_from_audit(
    audit: WorkflowAuditResult,
    *,
    candidate_id: str,
    source_refs: tuple[str, ...],
) -> InnovationCandidate | None:
    if audit.recommendation is ImprovementAction.KEEP:
        return None
    mapping = {
        ImprovementAction.RESEARCH: "Improve evidence acquisition before downstream work",
        ImprovementAction.ADD_GATE: "Add or strengthen a pre-action readiness/idempotency gate",
        ImprovementAction.AUTOMATE: "Automate the stable high-touch workflow with bounded execution",
        ImprovementAction.SIMPLIFY: "Split or simplify the workflow to reduce rework and ambiguity",
        ImprovementAction.RETIRE: "Retire the workflow and route work through a better alternative",
    }
    return InnovationCandidate(
        candidate_id=candidate_id,
        source_refs=source_refs,
        problem_statement="; ".join(audit.reasons),
        proposed_change=mapping[audit.recommendation],
        baseline_metric="workflow_outcome_quality_and_rework",
        safety_critical=audit.recommendation is ImprovementAction.ADD_GATE,
    )


def decide_candidate(candidate: InnovationCandidate, evidence: ExperimentEvidence | None) -> ForgeDecision:
    candidate.validate()
    if evidence is None:
        return ForgeDecision(
            stage=ForgeStage.EXPERIMENT,
            reasons=("no baseline-vs-candidate experiment evidence yet",),
            requires_human_approval=True,
        )
    evidence.validate()
    if evidence.candidate_id != candidate.candidate_id:
        raise ValueError("experiment evidence candidate_id mismatch")
    if evidence.safety_regression:
        return ForgeDecision(
            stage=ForgeStage.REJECTED,
            reasons=("safety regression observed",),
            requires_human_approval=False,
        )
    if evidence.baseline_value is None or evidence.candidate_value is None:
        return ForgeDecision(
            stage=ForgeStage.EXPERIMENT,
            reasons=("baseline or candidate metric is unobserved",),
            requires_human_approval=True,
        )
    if evidence.projects_observed < 3 or evidence.observations < 5 or not evidence.reproducible:
        return ForgeDecision(
            stage=ForgeStage.EXPERIMENT,
            reasons=("insufficient cross-project or reproducibility evidence",),
            requires_human_approval=True,
        )

    improved = (
        evidence.candidate_value < evidence.baseline_value
        if evidence.lower_is_better
        else evidence.candidate_value > evidence.baseline_value
    )
    if not improved:
        return ForgeDecision(
            stage=ForgeStage.REJECTED,
            reasons=("candidate did not improve the declared baseline metric",),
            requires_human_approval=False,
        )

    return ForgeDecision(
        stage=ForgeStage.PROMOTABLE,
        reasons=("measured reproducible improvement without safety regression",),
        requires_human_approval=True,
    )
