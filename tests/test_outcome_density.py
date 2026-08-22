import pytest

from nexus_verticals.outcome_density import OutcomeFunnel


def test_empty_funnel_returns_unknown_rates_not_zero_precision():
    rates = OutcomeFunnel().rates()
    assert all(value is None for value in rates.values())


def test_measured_funnel_derives_only_observed_ratios():
    funnel = OutcomeFunnel(
        signals=100,
        valid_problems=30,
        qualified_opportunities=12,
        approved_actions=6,
        replies=3,
        rfqs=2,
        quotes=1,
        orders=0,
    )
    rates = funnel.rates()
    assert rates["problem_per_signal"] == 0.30
    assert rates["reply_per_action"] == 0.50
    assert rates["order_per_quote"] == 0.0


def test_impossible_funnel_fails_closed():
    funnel = OutcomeFunnel(signals=1, valid_problems=2)
    assert funnel.validate()
    with pytest.raises(ValueError):
        funnel.rates()


def test_bool_is_not_accepted_as_count():
    funnel = OutcomeFunnel(signals=True)
    assert "signals must be a non-negative integer" in funnel.validate()
