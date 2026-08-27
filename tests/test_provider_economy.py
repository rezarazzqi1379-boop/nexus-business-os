from datetime import datetime, timezone

import pytest

from nexus_brain.provider_economy import (
    EconomyPolicy,
    ProviderObservation,
    select_economic_provider,
)


NOW = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


def observation(provider_id: str, **overrides):
    values = {
        "provider_id": provider_id,
        "observed_at": "2026-08-27T11:55:00+00:00",
        "healthy": True,
        "latency_ms": 1000,
        "success_rate": 0.99,
        "eval_score": 0.90,
        "estimated_cost_usd": 0.005,
        "sample_count": 10,
    }
    values.update(overrides)
    return ProviderObservation(**values)


def test_unpermitted_provider_can_never_win():
    decision = select_economic_provider(
        [observation("unapproved", eval_score=1.0)],
        policy=EconomyPolicy(),
        permitted_provider_ids={"approved"},
        now=NOW,
    )
    assert decision.allowed is False
    assert decision.provider_id is None
    assert "unapproved:not_policy_permitted" in decision.rejected


def test_stale_observation_fails_closed():
    decision = select_economic_provider(
        [observation("approved", observed_at="2026-08-27T09:00:00+00:00")],
        policy=EconomyPolicy(max_observation_age_seconds=3600),
        permitted_provider_ids={"approved"},
        now=NOW,
    )
    assert decision.allowed is False
    assert "approved:stale_observation" in decision.rejected


def test_low_quality_low_reliability_and_budget_fail_closed():
    items = [
        observation("quality", eval_score=0.2),
        observation("reliability", success_rate=0.5),
        observation("cost", estimated_cost_usd=1.0),
    ]
    decision = select_economic_provider(
        items,
        policy=EconomyPolicy(),
        permitted_provider_ids={"quality", "reliability", "cost"},
        now=NOW,
    )
    assert decision.allowed is False
    assert len(decision.rejected) == 3


def test_quality_and_reliability_dominate_cost():
    cheaper_weaker = observation(
        "cheap", eval_score=0.80, success_rate=0.96, estimated_cost_usd=0.0, latency_ms=500
    )
    stronger = observation(
        "strong", eval_score=0.96, success_rate=0.995, estimated_cost_usd=0.01, latency_ms=1500
    )
    decision = select_economic_provider(
        [cheaper_weaker, stronger],
        policy=EconomyPolicy(),
        permitted_provider_ids={"cheap", "strong"},
        now=NOW,
    )
    assert decision.allowed is True
    assert decision.provider_id == "strong"


def test_duplicate_observations_are_rejected():
    with pytest.raises(ValueError, match="duplicate_provider_observation"):
        select_economic_provider(
            [observation("same"), observation("same")],
            policy=EconomyPolicy(),
            permitted_provider_ids={"same"},
            now=NOW,
        )


def test_future_observation_is_not_trusted():
    decision = select_economic_provider(
        [observation("approved", observed_at="2026-08-27T12:05:00+00:00")],
        policy=EconomyPolicy(),
        permitted_provider_ids={"approved"},
        now=NOW,
    )
    assert decision.allowed is False
    assert "approved:observation_from_future" in decision.rejected
