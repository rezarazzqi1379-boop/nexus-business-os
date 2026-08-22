"""Bounded, evidence-driven evolution for NEXUS agent/tool configurations.

This module deliberately does not let an agent rewrite or deploy itself. It turns
observed failures into versioned proposals that must beat a baseline in evaluation
before they can be considered promotable. Consequential promotion remains an
external approval-gated action.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Literal


Decision = Literal["reject", "experiment", "promotable"]


@dataclass(frozen=True)
class FailureObservation:
    observation_id: str
    component: str
    failure_mode: str
    evidence_refs: tuple[str, ...]
    severity: int = 1
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.observation_id or not self.component or not self.failure_mode:
            raise ValueError("observation id, component, and failure mode are required")
        if not self.evidence_refs or any(not isinstance(ref, str) or not ref.strip() for ref in self.evidence_refs):
            raise ValueError("retrievable evidence is required")
        if not isinstance(self.severity, int) or isinstance(self.severity, bool) or not 1 <= self.severity <= 5:
            raise ValueError("severity must be an integer between 1 and 5")
        if not isinstance(self.observed_at, datetime) or self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("observed_at must be a timezone-aware datetime")


@dataclass(frozen=True)
class EvolutionProposal:
    proposal_id: str
    component: str
    hypothesis: str
    change_summary: str
    source_observations: tuple[str, ...]
    expected_metric: str
    max_regression: float = 0.0

    def __post_init__(self) -> None:
        required = (self.proposal_id, self.component, self.hypothesis, self.change_summary, self.expected_metric)
        if any(not isinstance(value, str) or not value.strip() for value in required):
            raise ValueError("proposal fields must be non-empty strings")
        if not self.source_observations or any(
            not isinstance(ref, str) or not ref.strip() for ref in self.source_observations
        ):
            raise ValueError("proposal must be traceable to observations")
        if not isinstance(self.max_regression, (int, float)) or isinstance(self.max_regression, bool):
            raise ValueError("max_regression must be numeric")
        if not math.isfinite(float(self.max_regression)) or self.max_regression < 0:
            raise ValueError("max_regression must be finite and non-negative")


@dataclass(frozen=True)
class EvaluationResult:
    proposal_id: str
    baseline_score: float
    candidate_score: float
    safety_regressions: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.proposal_id, str) or not self.proposal_id.strip():
            raise ValueError("proposal_id is required")
        for name, value in (("baseline_score", self.baseline_score), ("candidate_score", self.candidate_score)):
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
                raise ValueError(f"{name} must be a finite number")
        if any(not isinstance(item, str) or not item.strip() for item in self.safety_regressions):
            raise ValueError("safety regression labels must be non-empty strings")
        if any(not isinstance(ref, str) or not ref.strip() for ref in self.evidence_refs):
            raise ValueError("evaluation evidence refs must be non-empty strings")

    @property
    def delta(self) -> float:
        return self.candidate_score - self.baseline_score


@dataclass(frozen=True)
class EvolutionDecision:
    proposal_id: str
    decision: Decision
    reason: str
    requires_human_approval: bool


def propose_from_failure(observation: FailureObservation, *, proposal_id: str, hypothesis: str, change_summary: str, expected_metric: str) -> EvolutionProposal:
    return EvolutionProposal(
        proposal_id=proposal_id,
        component=observation.component,
        hypothesis=hypothesis,
        change_summary=change_summary,
        source_observations=(observation.observation_id,),
        expected_metric=expected_metric,
    )


def decide_evolution(proposal: EvolutionProposal, evaluation: EvaluationResult, *, minimum_gain: float = 0.01) -> EvolutionDecision:
    if not isinstance(minimum_gain, (int, float)) or isinstance(minimum_gain, bool) or not math.isfinite(float(minimum_gain)) or minimum_gain < 0:
        raise ValueError("minimum_gain must be a finite non-negative number")
    if evaluation.proposal_id != proposal.proposal_id:
        return EvolutionDecision(proposal.proposal_id, "reject", "evaluation/proposal mismatch", False)
    if not evaluation.evidence_refs:
        return EvolutionDecision(proposal.proposal_id, "reject", "evaluation has no retrievable evidence", False)
    if evaluation.safety_regressions:
        return EvolutionDecision(proposal.proposal_id, "reject", "safety regression detected", False)
    if evaluation.delta < minimum_gain:
        return EvolutionDecision(proposal.proposal_id, "experiment", "gain is below promotion threshold", False)
    return EvolutionDecision(
        proposal.proposal_id,
        "promotable",
        f"candidate improved score by {evaluation.delta:.4f} without recorded safety regression",
        True,
    )


def deduplicate_observations(observations: Iterable[FailureObservation]) -> list[FailureObservation]:
    best: dict[tuple[str, str], FailureObservation] = {}
    for item in observations:
        if not isinstance(item, FailureObservation):
            raise ValueError("observations must contain FailureObservation objects")
        key = (item.component.strip().lower(), item.failure_mode.strip().lower())
        current = best.get(key)
        if current is None or item.severity > current.severity or (
            item.severity == current.severity and item.observed_at > current.observed_at
        ):
            best[key] = item
    return sorted(
        best.values(),
        key=lambda item: (-item.severity, -item.observed_at.timestamp(), item.component, item.failure_mode),
    )
