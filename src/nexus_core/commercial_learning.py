from __future__ import annotations

from dataclasses import dataclass
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


def learn_segment_score(
    outcomes: Sequence[SegmentOutcome],
    *,
    segment_key: str,
    prior_successes: float = 1.0,
    prior_failures: float = 3.0,
) -> LearnedSegmentScore:
    """Estimate segment quality from real outcomes with conservative shrinkage.

    We deliberately avoid treating a tiny sample as a stable conversion rate. Later
    funnel stages carry more evidence weight, while the beta-style prior shrinks small
    samples toward a conservative baseline until enough observations accumulate.
    """
    relevant = [o for o in outcomes if isinstance(o, SegmentOutcome) and o.segment_key == segment_key]
    weighted_success = 0.0
    weighted_failure = 0.0
    for outcome in relevant:
        weight = _STAGE_WEIGHTS[outcome.stage]
        if outcome.success:
            weighted_success += weight
        else:
            weighted_failure += weight

    posterior = (prior_successes + weighted_success) / (
        prior_successes + prior_failures + weighted_success + weighted_failure
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
    """Rank only by evidence-backed posterior score, breaking ties by sample size/key."""
    scores = [learn_segment_score(outcomes, segment_key=key) for key in set(segment_keys) if key]
    return tuple(sorted(scores, key=lambda s: (-s.posterior_success_rate, -s.observations, s.segment_key)))
