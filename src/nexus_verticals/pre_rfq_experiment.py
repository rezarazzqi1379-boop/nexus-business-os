"""Prospective shadow experiment contract for the Pre-RFQ Readiness Gate.

This module records paired baseline/candidate decisions and later observed rework.
It computes only observed rates with explicit denominators. It does not infer
counterfactual outcomes or authorize promotion.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class PreRfqExperimentObservation:
    observation_id: str
    project_id: str
    baseline_would_send: bool
    candidate_would_send: bool
    actual_sent: bool
    clarification_rework_observed: bool | None
    source_ref: str

    def __post_init__(self) -> None:
        if not self.observation_id.strip() or not self.project_id.strip() or not self.source_ref.strip():
            raise ValueError("observation_id, project_id, and source_ref are required")


@dataclass(frozen=True)
class PreRfqExperimentMetrics:
    observations: int
    observed_outcomes: int
    baseline_sent_observed: int
    baseline_rework_observed: int
    candidate_sent_observed: int
    candidate_rework_observed: int
    baseline_rework_rate: float | None
    candidate_rework_rate: float | None
    paired_rate_delta: float | None


def summarize_pre_rfq_experiment(
    observations: Iterable[PreRfqExperimentObservation],
) -> PreRfqExperimentMetrics:
    rows = tuple(observations)
    seen: dict[str, PreRfqExperimentObservation] = {}
    for row in rows:
        if not isinstance(row, PreRfqExperimentObservation):
            raise ValueError("observations must contain PreRfqExperimentObservation objects")
        existing = seen.get(row.observation_id)
        if existing is not None and existing != row:
            raise ValueError(f"conflicting duplicate observation_id: {row.observation_id}")
        seen[row.observation_id] = row

    rows = tuple(seen[k] for k in sorted(seen))
    observed = tuple(r for r in rows if r.clarification_rework_observed is not None)

    baseline_sent = tuple(r for r in observed if r.baseline_would_send)
    candidate_sent = tuple(r for r in observed if r.candidate_would_send)
    baseline_rework = sum(1 for r in baseline_sent if r.clarification_rework_observed is True)
    candidate_rework = sum(1 for r in candidate_sent if r.clarification_rework_observed is True)

    baseline_rate = baseline_rework / len(baseline_sent) if baseline_sent else None
    candidate_rate = candidate_rework / len(candidate_sent) if candidate_sent else None
    delta = None
    if baseline_rate is not None and candidate_rate is not None:
        delta = candidate_rate - baseline_rate

    return PreRfqExperimentMetrics(
        observations=len(rows),
        observed_outcomes=len(observed),
        baseline_sent_observed=len(baseline_sent),
        baseline_rework_observed=baseline_rework,
        candidate_sent_observed=len(candidate_sent),
        candidate_rework_observed=candidate_rework,
        baseline_rework_rate=baseline_rate,
        candidate_rework_rate=candidate_rate,
        paired_rate_delta=delta,
    )


def experiment_promotion_gaps(
    metrics: PreRfqExperimentMetrics,
    *,
    min_observed_outcomes: int = 20,
    min_candidate_sent: int = 10,
) -> tuple[str, ...]:
    gaps: list[str] = []
    if metrics.observed_outcomes < min_observed_outcomes:
        gaps.append("insufficient_observed_outcomes")
    if metrics.candidate_sent_observed < min_candidate_sent:
        gaps.append("insufficient_candidate_sent_cases")
    if metrics.baseline_rework_rate is None or metrics.candidate_rework_rate is None:
        gaps.append("missing_comparable_rework_rates")
    return tuple(gaps)
