from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class LaneOutcome:
    lane: str
    attempts: int
    meaningful_outcomes: int
    downstream_value: float
    false_positives: int = 0


@dataclass(frozen=True)
class LaneAllocation:
    lane: str
    weight: float
    confidence: str
    reason: str


def _validate(outcome: LaneOutcome) -> tuple[str, ...]:
    errors: list[str] = []
    if not outcome.lane.strip():
        errors.append("invalid_lane")
    if outcome.attempts < 0 or outcome.meaningful_outcomes < 0 or outcome.false_positives < 0:
        errors.append("negative_counts")
    if outcome.meaningful_outcomes > outcome.attempts:
        errors.append("outcomes_exceed_attempts")
    if outcome.false_positives > outcome.attempts:
        errors.append("false_positives_exceed_attempts")
    if outcome.downstream_value < 0:
        errors.append("negative_downstream_value")
    return tuple(errors)


def adaptive_allocations(
    outcomes: tuple[LaneOutcome, ...],
    *,
    exploration_floor: float = 0.08,
    max_lane_weight: float = 0.45,
    min_samples: int = 5,
) -> tuple[LaneAllocation, ...]:
    """Allocate portfolio attention without collapsing exploration.

    The allocator rewards observed downstream value but uses conservative shrinkage
    and an explicit exploration floor so a temporarily quiet lane cannot disappear.
    A hard cap prevents one noisy or lucky lane from monopolizing the portfolio.
    """
    if not 0 < exploration_floor < 1:
        raise ValueError("invalid_exploration_floor")
    if not exploration_floor <= max_lane_weight <= 1:
        raise ValueError("invalid_max_lane_weight")
    if min_samples < 1:
        raise ValueError("invalid_min_samples")
    if not outcomes:
        return ()
    seen: set[str] = set()
    for outcome in outcomes:
        errors = _validate(outcome)
        if errors:
            raise ValueError(",".join(errors))
        if outcome.lane in seen:
            raise ValueError("duplicate_lane")
        seen.add(outcome.lane)

    raw: dict[str, float] = {}
    confidence: dict[str, str] = {}
    for outcome in outcomes:
        if outcome.attempts == 0:
            evidence_score = 0.0
            confidence[outcome.lane] = "insufficient"
        else:
            success_rate = outcome.meaningful_outcomes / outcome.attempts
            false_positive_rate = outcome.false_positives / outcome.attempts
            shrinkage = outcome.attempts / (outcome.attempts + min_samples)
            uncertainty_bonus = 1 / sqrt(outcome.attempts + 1)
            value_signal = success_rate + min(outcome.downstream_value / max(outcome.attempts, 1), 1.0)
            evidence_score = max(0.0, shrinkage * value_signal - 0.5 * false_positive_rate + 0.15 * uncertainty_bonus)
            confidence[outcome.lane] = "usable" if outcome.attempts >= min_samples else "emerging"
        raw[outcome.lane] = evidence_score

    lane_count = len(outcomes)
    floor_total = exploration_floor * lane_count
    if floor_total >= 1:
        floor = 1 / lane_count
        return tuple(LaneAllocation(o.lane, floor, confidence[o.lane], "exploration_floor_only") for o in outcomes)

    remaining = 1 - floor_total
    total_signal = sum(raw.values())
    provisional: dict[str, float] = {}
    for lane, score in raw.items():
        share = (score / total_signal) if total_signal > 0 else (1 / lane_count)
        provisional[lane] = exploration_floor + remaining * share

    # Cap concentration and redistribute excess iteratively among uncapped lanes.
    weights = dict(provisional)
    for _ in range(lane_count + 2):
        excess = sum(max(0.0, w - max_lane_weight) for w in weights.values())
        if excess <= 1e-12:
            break
        uncapped = [lane for lane, w in weights.items() if w < max_lane_weight - 1e-12]
        for lane in list(weights):
            if weights[lane] > max_lane_weight:
                weights[lane] = max_lane_weight
        if not uncapped:
            break
        increment = excess / len(uncapped)
        for lane in uncapped:
            weights[lane] += increment

    total = sum(weights.values())
    if total <= 0:
        raise RuntimeError("allocation_total_zero")
    normalized = {lane: weight / total for lane, weight in weights.items()}

    allocations = []
    for outcome in outcomes:
        lane = outcome.lane
        reason = "outcome_weighted"
        if confidence[lane] == "insufficient":
            reason = "protected_exploration"
        allocations.append(LaneAllocation(lane, normalized[lane], confidence[lane], reason))
    return tuple(sorted(allocations, key=lambda item: (-item.weight, item.lane)))
