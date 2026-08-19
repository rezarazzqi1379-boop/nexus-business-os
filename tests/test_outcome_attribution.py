import pytest

from nexus_core.outcome_attribution import Contribution, summarize_attribution


def test_direct_high_confidence_contribution_ranks_above_contextual():
    items = [
        Contribution("msg-a", "message", "quote-1", "direct", ("gmail:1",), 0.9, 1.0),
        Contribution("paper-a", "paper", "quote-1", "contextual", ("paper:1",), 0.9, 1.0),
    ]
    result = summarize_attribution(items)
    assert result[0].contributor_id == "msg-a"


def test_low_sample_attribution_does_not_claim_usable_confidence():
    result = summarize_attribution([
        Contribution("route-a", "network_path", "reply-1", "direct", ("gmail:2",), 0.95, 1.0),
    ])
    assert result[0].confidence_band == "insufficient"


def test_negative_observed_effect_is_preserved():
    result = summarize_attribution([
        Contribution("tool-a", "tool", "failure-1", "direct", ("trace:1",), 0.8, -1.0),
    ])
    assert result[0].weighted_effect < 0


def test_duplicate_contribution_identity_fails_closed():
    item = Contribution("msg-a", "message", "reply-1", "direct", ("gmail:3",), 0.8, 1.0)
    with pytest.raises(ValueError, match="duplicate_contribution_identity"):
        summarize_attribution([item, item])


def test_missing_evidence_fails_closed():
    with pytest.raises(ValueError, match="missing_evidence_refs"):
        summarize_attribution([
            Contribution("msg-a", "message", "reply-1", "direct", (), 0.8, 1.0),
        ])


def test_repeated_supported_outcomes_can_reach_usable_band():
    items = [
        Contribution("source-a", "source", f"outcome-{i}", "supporting", (f"evidence:{i}",), 0.8, 0.7)
        for i in range(5)
    ]
    result = summarize_attribution(items)
    assert result[0].confidence_band == "usable"
    assert result[0].evidence_count == 5
