import pytest

from nexus_core.commercial_learning import (
    SegmentOutcome,
    learn_segment_score,
    rank_segments,
    validate_segment_outcome,
)


def test_small_sample_remains_insufficient_even_after_one_deal() -> None:
    score = learn_segment_score((SegmentOutcome("segment-a", "deal", True),), segment_key="segment-a")
    assert score.observations == 1
    assert score.confidence == "insufficient"
    assert score.posterior_success_rate < 0.5


def test_later_funnel_success_outweighs_early_reply_success() -> None:
    outcomes = (
        SegmentOutcome("reply-heavy", "reply", True),
        SegmentOutcome("quote-heavy", "quote", True),
    )
    ranked = rank_segments(outcomes, ("reply-heavy", "quote-heavy"))
    assert ranked[0].segment_key == "quote-heavy"


def test_repeated_failures_lower_posterior() -> None:
    good = tuple(SegmentOutcome("good", "quote", True) for _ in range(6))
    bad = tuple(SegmentOutcome("bad", "quote", False) for _ in range(6))
    ranked = rank_segments(good + bad, ("good", "bad"))
    assert ranked[0].segment_key == "good"
    assert ranked[0].posterior_success_rate > ranked[1].posterior_success_rate


def test_confidence_requires_enough_observations() -> None:
    emerging = tuple(SegmentOutcome("x", "reply", True) for _ in range(5))
    usable = tuple(SegmentOutcome("y", "reply", True) for _ in range(15))
    assert learn_segment_score(emerging, segment_key="x").confidence == "emerging"
    assert learn_segment_score(usable, segment_key="y").confidence == "usable"


def test_malformed_stage_is_rejected_and_does_not_crash_learning() -> None:
    malformed = SegmentOutcome("segment-a", "not-a-stage", True)  # type: ignore[arg-type]
    assert "stage is invalid" in validate_segment_outcome(malformed)
    score = learn_segment_score((malformed,), segment_key="segment-a")
    assert score.observations == 0
    assert score.posterior_success_rate == 0.25


def test_non_boolean_success_is_rejected_and_does_not_contaminate_score() -> None:
    malformed = SegmentOutcome("segment-a", "deal", 1)  # type: ignore[arg-type]
    assert "success must be a boolean" in validate_segment_outcome(malformed)
    score = learn_segment_score((malformed,), segment_key="segment-a")
    assert score.observations == 0


def test_rank_segments_ignores_malformed_and_duplicate_keys() -> None:
    ranked = rank_segments((), ("valid", "valid", "", ["unhashable"]))  # type: ignore[arg-type,list-item]
    assert tuple(score.segment_key for score in ranked) == ("valid",)


def test_invalid_segment_key_and_priors_fail_closed() -> None:
    with pytest.raises(ValueError, match="segment_key"):
        learn_segment_score((), segment_key=" ")
    with pytest.raises(ValueError, match="priors"):
        learn_segment_score((), segment_key="x", prior_successes=float("nan"))
    with pytest.raises(ValueError, match="prior mass"):
        learn_segment_score((), segment_key="x", prior_successes=0, prior_failures=0)
