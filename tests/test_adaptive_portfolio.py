import pytest

from nexus_core.adaptive_portfolio import LaneOutcome, adaptive_allocations


def test_high_value_lane_gets_more_weight_without_monopoly():
    allocations = adaptive_allocations(
        (
            LaneOutcome("commercial", attempts=20, meaningful_outcomes=10, downstream_value=15.0),
            LaneOutcome("research", attempts=10, meaningful_outcomes=2, downstream_value=2.0),
            LaneOutcome("security", attempts=8, meaningful_outcomes=1, downstream_value=1.0),
        ),
        exploration_floor=0.08,
        max_lane_weight=0.45,
    )
    by_lane = {item.lane: item for item in allocations}
    assert by_lane["commercial"].weight > by_lane["research"].weight
    assert by_lane["commercial"].weight <= 0.45 + 1e-9
    assert all(item.weight > 0 for item in allocations)
    assert abs(sum(item.weight for item in allocations) - 1.0) < 1e-9


def test_zero_history_lane_keeps_exploration_floor():
    allocations = adaptive_allocations(
        (
            LaneOutcome("commercial", attempts=12, meaningful_outcomes=5, downstream_value=8.0),
            LaneOutcome("future_intelligence", attempts=0, meaningful_outcomes=0, downstream_value=0.0),
        ),
        exploration_floor=0.10,
        max_lane_weight=0.80,
    )
    by_lane = {item.lane: item for item in allocations}
    assert by_lane["future_intelligence"].weight >= 0.10
    assert by_lane["future_intelligence"].confidence == "insufficient"
    assert by_lane["future_intelligence"].reason == "protected_exploration"


def test_false_positive_penalty_reduces_weight():
    allocations = adaptive_allocations(
        (
            LaneOutcome("clean", attempts=10, meaningful_outcomes=3, downstream_value=3.0, false_positives=0),
            LaneOutcome("noisy", attempts=10, meaningful_outcomes=3, downstream_value=3.0, false_positives=8),
        ),
        exploration_floor=0.05,
        max_lane_weight=0.90,
    )
    by_lane = {item.lane: item for item in allocations}
    assert by_lane["clean"].weight > by_lane["noisy"].weight


def test_duplicate_lane_fails_closed():
    with pytest.raises(ValueError, match="duplicate_lane"):
        adaptive_allocations(
            (
                LaneOutcome("research", 1, 0, 0.0),
                LaneOutcome("research", 1, 0, 0.0),
            )
        )


def test_invalid_counts_fail_closed():
    with pytest.raises(ValueError, match="outcomes_exceed_attempts"):
        adaptive_allocations((LaneOutcome("commercial", 1, 2, 1.0),))
