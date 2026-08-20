from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal, Sequence


OutcomeStage = Literal["sent", "reply", "qualified_reply", "quote", "negotiation", "deal"]


@dataclass(frozen=True)
class SegmentOutcome:
    segment_key: str
    stage: OutcomeStage
    success: bool


@dataclass(frozen=True)
class LearnedSegmentScore:
    segment_key: str
    observations: int
    posterior_success_rate: float
    confidence: Literal["insufficient", "emerging", "usable"]


_STAGE_WEIGHTS: dict[OutcomeStage, float] = {
    "sent": 0.05,
    "reply": 0.20,
    "qualified_reply": 0.35,
    "quote": 0.55,
    "negotiation": 0.75,
    "deal": 1.00,
}


def _valid_segment_key(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip() and len(value) <= 256


def validate_segment_outcome(outcome: object) -> tuple[str, ...]:
    """Reject malformed commercial-learning observations before they affect rankings."""
    if not isinstance(outcome, SegmentOutcome):
        return ("outcome must be a SegmentOutcome",)
    errors: list[str] = []
    if not _valid_segment_key(outcome.segment_key):
        errors.append("segment_key is invalid")
    if not isinstance(outcome.stage, str) or outcome.stage not in _STAGE_WEIGHTS:
        errors.append("stage is invalid")
    if not isinstance(outcome.success, bool):
        errors.append("success must be a boolean")
    return tuple(errors)


def _valid_prior(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) >= 0.0
    )


def learn_segment_score(
    outcomes: Sequence[SegmentOutcome],
    *,
    segment_key: str,
    prior_successes: float = 1.0,
    prior_failures: float = 3.0,
) -> LearnedSegmentScore:
    """Estimate segment quality from valid real outcomes with conservative shrinkage.

    Invalid runtime observations are excluded rather than crashing or contaminating a
    commercial ranking. Later funnel stages carry more evidence weight, while the
    beta-style prior shrinks small samples toward a conservative baseline until enough
    observations accumulate.
    """
    if not _valid_segment_key(segment_key):
        raise ValueError("segment_key is invalid")
    if not _valid_prior(prior_successes) or not _valid_prior(prior_failures):
        raise ValueError("priors must be finite non-negative numbers")
    if float(prior_successes) + float(prior_failures) <= 0:
        raise ValueError("prior mass must be positive")

    relevant = [
        outcome
        for outcome in outcomes
        if not validate_segment_outcome(outcome) and outcome.segment_key == segment_key
    ]
    weighted_success = 0.0
    weighted_failure = 0.0
    for outcome in relevant:
        weight = _STAGE_WEIGHTS[outcome.stage]
        if outcome.success:
            weighted_success += weight
        else:
            weighted_failure += weight

    posterior = (float(prior_successes) + weighted_success) / (
        float(prior_successes) + float(prior_failures) + weighted_success + weighted_failure
    )
    observations = len(relevant)
    confidence: Literal["insufficient", "emerging", "usable"]
    if observations < 5:
        confidence = "insufficient"
    elif observations < 15:
        confidence = "emerging"
    else:
        confidence = "usable"
    return LearnedSegmentScore(segment_key, observations, round(posterior, 4), confidence)


def rank_segments(outcomes: Sequence[SegmentOutcome], segment_keys: Sequence[str]) -> tuple[LearnedSegmentScore, ...]:
    """Rank valid segment keys by evidence-backed posterior score."""
    unique_keys: list[str] = []
    seen: set[str] = set()
    for key in segment_keys:
        if not _valid_segment_key(key) or key in seen:
            continue
        seen.add(key)
        unique_keys.append(key)
    scores = [learn_segment_score(outcomes, segment_key=key) for key in unique_keys]
    return tuple(sorted(scores, key=lambda score: (-score.posterior_success_rate, -score.observations, score.segment_key)))
