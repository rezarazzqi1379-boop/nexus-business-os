"""Shadow evaluation for NEXUS Business Genome recommendations.

This module does not tune scoring weights or authorize promotion. It records
what NEXUS recommended, what a human decided, and what eventually happened.
Metrics remain undefined until their required observations exist.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .business_genome import Decision


@dataclass(frozen=True)
class ShadowDecisionObservation:
    observation_id: str
    project_id: str
    case_type: str
    recommendation: Decision
    human_decision: Decision | None = None
    outcome_success: bool | None = None
    safety_violation: bool = False
    source_ref: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name, value in (
            ("observation_id", self.observation_id),
            ("project_id", self.project_id),
            ("case_type", self.case_type),
            ("source_ref", self.source_ref),
        ):
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{name} is required")
        if not isinstance(self.recommendation, Decision):
            errors.append("recommendation must be Decision")
        if self.human_decision is not None and not isinstance(self.human_decision, Decision):
            errors.append("human_decision must be Decision or None")
        if self.outcome_success not in {True, False, None}:
            errors.append("outcome_success must be bool or None")
        if not isinstance(self.safety_violation, bool):
            errors.append("safety_violation must be bool")
        return errors


@dataclass(frozen=True)
class CalibrationReport:
    total_observations: int
    distinct_case_types: int
    human_labeled: int
    outcome_labeled: int
    recommendation_human_agreement: float | None
    pursue_outcome_precision: float | None
    pursue_false_positives: int
    safety_violations: int


def evaluate_shadow(observations: Iterable[ShadowDecisionObservation]) -> CalibrationReport:
    rows = [row for row in observations if not row.validate()]
    human_rows = [row for row in rows if row.human_decision is not None]
    outcome_rows = [row for row in rows if row.outcome_success is not None]
    pursue_outcomes = [
        row for row in outcome_rows if row.recommendation == Decision.PURSUE
    ]

    agreement = None
    if human_rows:
        agreement = sum(
            1 for row in human_rows if row.recommendation == row.human_decision
        ) / len(human_rows)

    pursue_precision = None
    if pursue_outcomes:
        pursue_precision = sum(1 for row in pursue_outcomes if row.outcome_success) / len(pursue_outcomes)

    return CalibrationReport(
        total_observations=len(rows),
        distinct_case_types=len({row.case_type for row in rows}),
        human_labeled=len(human_rows),
        outcome_labeled=len(outcome_rows),
        recommendation_human_agreement=agreement,
        pursue_outcome_precision=pursue_precision,
        pursue_false_positives=sum(
            1
            for row in pursue_outcomes
            if row.outcome_success is False
        ),
        safety_violations=sum(1 for row in rows if row.safety_violation),
    )


@dataclass(frozen=True)
class PromotionEvidencePolicy:
    min_observations: int = 5
    min_case_types: int = 2
    min_human_labeled: int = 3
    min_outcome_labeled: int = 3


def promotion_evidence_gaps(
    report: CalibrationReport, policy: PromotionEvidencePolicy = PromotionEvidencePolicy()
) -> tuple[str, ...]:
    """Return evidence gaps only; empty gaps do not authorize production promotion."""
    gaps: list[str] = []
    if report.total_observations < policy.min_observations:
        gaps.append("insufficient_observations")
    if report.distinct_case_types < policy.min_case_types:
        gaps.append("insufficient_case_diversity")
    if report.human_labeled < policy.min_human_labeled:
        gaps.append("insufficient_human_decisions")
    if report.outcome_labeled < policy.min_outcome_labeled:
        gaps.append("insufficient_real_outcomes")
    if report.safety_violations:
        gaps.append("safety_violation_present")
    return tuple(gaps)
