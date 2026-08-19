from nexus_core.commercial_learning import SegmentOutcome, learn_segment_score, rank_segments


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
