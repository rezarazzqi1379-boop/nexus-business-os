"""Tests for fal_trade_economics.py."""

import pytest

from fal_vertical import FALIsolationError, LANE_FAL_A, PROJECT_ID
from fal_trade_economics import (
    Shipment,
    breakeven_sale_price,
    evaluate_fal_lane_opportunity,
    fx_convert,
    landed_cost_per_ton,
    margin,
    spec_adjusted_price,
    weighted_average_price_per_ton,
)


def test_fx_convert_basic():
    assert fx_convert(100, 1.1) == pytest.approx(110)


def test_fx_convert_rejects_nonpositive_rate():
    with pytest.raises(ValueError):
        fx_convert(100, 0)


def test_landed_cost_matches_cif_plus_duty_build_up():
    result = landed_cost_per_ton(
        fob_price_per_ton=1000, freight_per_ton=50,
        insurance_rate=0.01, customs_duty_rate=0.05,
    )
    cfr = 1050
    insurance = cfr * 0.01
    cif = cfr + insurance
    duty = cif * 0.05
    expected = cif + duty
    assert result.landed_cost_per_ton == pytest.approx(expected)


def test_landed_cost_rejects_out_of_range_rate():
    with pytest.raises(ValueError):
        landed_cost_per_ton(fob_price_per_ton=1000, freight_per_ton=50, insurance_rate=1.5, customs_duty_rate=0.05)


def test_landed_cost_rejects_negative_freight():
    with pytest.raises(ValueError):
        landed_cost_per_ton(fob_price_per_ton=1000, freight_per_ton=-10, insurance_rate=0.01, customs_duty_rate=0.05)


def test_margin_positive_case():
    result = margin(landed_cost_per_ton=900, sale_price_per_ton=1000)
    assert result.gross_margin_per_ton == pytest.approx(100)
    assert result.gross_margin_pct == pytest.approx(0.10)


def test_margin_can_be_negative_when_underwater():
    result = margin(landed_cost_per_ton=1100, sale_price_per_ton=1000)
    assert result.gross_margin_per_ton == pytest.approx(-100)


def test_breakeven_sale_price_recovers_target_margin():
    landed = 900.0
    target = 0.10
    price = breakeven_sale_price(landed_cost_per_ton=landed, target_margin_pct=target)
    result = margin(landed_cost_per_ton=landed, sale_price_per_ton=price)
    assert result.gross_margin_pct == pytest.approx(target)


def test_breakeven_rejects_margin_of_one_or_more():
    with pytest.raises(ValueError):
        breakeven_sale_price(landed_cost_per_ton=900, target_margin_pct=1.0)


def test_spec_adjusted_price_higher_spec_gets_premium():
    price = spec_adjusted_price(
        base_price_per_ton=1000, base_spec_pct=75, actual_spec_pct=78, premium_per_point_per_ton=20
    )
    assert price == pytest.approx(1060)


def test_spec_adjusted_price_lower_spec_gets_discount():
    price = spec_adjusted_price(
        base_price_per_ton=1000, base_spec_pct=75, actual_spec_pct=72, premium_per_point_per_ton=20
    )
    assert price == pytest.approx(940)


def test_weighted_average_price_matches_manual_calc():
    shipments = [Shipment(10, 1000), Shipment(30, 900)]
    avg = weighted_average_price_per_ton(shipments)
    expected = (10 * 1000 + 30 * 900) / 40
    assert avg == pytest.approx(expected)


def test_weighted_average_price_rejects_empty_list():
    with pytest.raises(ValueError):
        weighted_average_price_per_ton([])


def test_evaluate_fal_lane_opportunity_rejects_unknown_lane():
    with pytest.raises(ValueError):
        evaluate_fal_lane_opportunity(
            project_id=PROJECT_ID, lane_id="NOT-A-LANE",
            fob_price_per_ton=1000, freight_per_ton=50, insurance_rate=0.01,
            customs_duty_rate=0.05, target_sale_price_per_ton=1200,
        )


def test_evaluate_fal_lane_opportunity_rejects_project_mismatch():
    with pytest.raises(FALIsolationError):
        evaluate_fal_lane_opportunity(
            project_id="SOME-OTHER-PROJECT", lane_id=LANE_FAL_A,
            fob_price_per_ton=1000, freight_per_ton=50, insurance_rate=0.01,
            customs_duty_rate=0.05, target_sale_price_per_ton=1200,
        )


def test_evaluate_fal_lane_opportunity_flags_viability_correctly():
    viable = evaluate_fal_lane_opportunity(
        project_id=PROJECT_ID, lane_id=LANE_FAL_A,
        fob_price_per_ton=1000, freight_per_ton=50, insurance_rate=0.01,
        customs_duty_rate=0.05, target_sale_price_per_ton=1500,
    )
    assert viable.viable is True

    not_viable = evaluate_fal_lane_opportunity(
        project_id=PROJECT_ID, lane_id=LANE_FAL_A,
        fob_price_per_ton=1000, freight_per_ton=50, insurance_rate=0.01,
        customs_duty_rate=0.05, target_sale_price_per_ton=1000,
    )
    assert not_viable.viable is False
