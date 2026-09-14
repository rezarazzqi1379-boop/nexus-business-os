"""Landed-cost and margin economics for the FAL-A/FAL-B ferroalloys vertical.

Scope: pure arithmetic that is exact once you supply real numbers -- currency
conversion, landed cost build-up, margin, breakeven price, spec-based price
adjustment, and weighted-average cost across shipments. It does NOT embed any
fabricated freight rate, customs duty rate, spec-premium schedule, or FX rate --
every real-world rate is a required argument, never a shipped default. This mirrors
the same discipline as rolling_mill_mechanics.py: exact math is computed directly;
anything that varies by contract, country, or market is the caller's evidence to
supply, not this module's guess.

Every entry point that touches a real trade opportunity is scoped to a real FAL lane
via fal_vertical.assert_lane_scope -- a call for an unknown lane or a project/lane
mismatch is rejected, not silently reassigned.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from fal_vertical import assert_lane_scope


def _positive(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ValueError(f"{name} must be a positive number, got {value!r}")


def _non_negative(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(f"{name} must be a non-negative number, got {value!r}")


def _rate(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
        raise ValueError(f"{name} must be a fraction between 0 and 1, got {value!r}")


def fx_convert(amount: float, rate: float) -> float:
    """Convert `amount` in currency A to currency B using a caller-supplied rate
    (units of B per unit of A). No rate is assumed or cached -- FX moves constantly
    and a stale rate presented as current would be worse than no conversion."""
    _non_negative("amount", amount)
    _positive("rate", rate)
    return amount * rate


@dataclass(frozen=True)
class LandedCostBreakdown:
    fob_price_per_ton: float
    freight_per_ton: float
    insurance_amount_per_ton: float
    customs_duty_amount_per_ton: float
    other_fees_per_ton: float
    landed_cost_per_ton: float


def landed_cost_per_ton(
    *,
    fob_price_per_ton: float,
    freight_per_ton: float,
    insurance_rate: float,
    customs_duty_rate: float,
    other_fees_per_ton: float = 0.0,
) -> LandedCostBreakdown:
    """Standard CIF-plus-duty landed cost build-up:
    CIF = FOB + freight + insurance (insurance computed on FOB+freight, the common
    convention); landed = CIF + customs duty (computed on CIF) + other fees.
    `insurance_rate` and `customs_duty_rate` are fractions (e.g. 0.005 = 0.5%) that
    must come from an actual quote/tariff schedule -- this function does not assume
    a typical rate.
    """
    _positive("fob_price_per_ton", fob_price_per_ton)
    _non_negative("freight_per_ton", freight_per_ton)
    _rate("insurance_rate", insurance_rate)
    _rate("customs_duty_rate", customs_duty_rate)
    _non_negative("other_fees_per_ton", other_fees_per_ton)

    cfr = fob_price_per_ton + freight_per_ton
    insurance_amount = cfr * insurance_rate
    cif = cfr + insurance_amount
    customs_duty_amount = cif * customs_duty_rate
    landed = cif + customs_duty_amount + other_fees_per_ton
    return LandedCostBreakdown(
        fob_price_per_ton=fob_price_per_ton,
        freight_per_ton=freight_per_ton,
        insurance_amount_per_ton=insurance_amount,
        customs_duty_amount_per_ton=customs_duty_amount,
        other_fees_per_ton=other_fees_per_ton,
        landed_cost_per_ton=landed,
    )


@dataclass(frozen=True)
class MarginResult:
    landed_cost_per_ton: float
    sale_price_per_ton: float
    gross_margin_per_ton: float
    gross_margin_pct: float


def margin(*, landed_cost_per_ton: float, sale_price_per_ton: float) -> MarginResult:
    _positive("landed_cost_per_ton", landed_cost_per_ton)
    _positive("sale_price_per_ton", sale_price_per_ton)
    gross = sale_price_per_ton - landed_cost_per_ton
    pct = gross / sale_price_per_ton
    return MarginResult(landed_cost_per_ton, sale_price_per_ton, gross, pct)


def breakeven_sale_price(*, landed_cost_per_ton: float, target_margin_pct: float) -> float:
    """Sale price needed to hit a target margin percentage (of sale price), given a
    known landed cost. target_margin_pct is a fraction (0.10 = 10%)."""
    _positive("landed_cost_per_ton", landed_cost_per_ton)
    if isinstance(target_margin_pct, bool) or not isinstance(target_margin_pct, (int, float)) or not 0 <= target_margin_pct < 1:
        raise ValueError("target_margin_pct must be a fraction in [0, 1)")
    return landed_cost_per_ton / (1 - target_margin_pct)


def spec_adjusted_price(
    *,
    base_price_per_ton: float,
    base_spec_pct: float,
    actual_spec_pct: float,
    premium_per_point_per_ton: float,
) -> float:
    """Adjust a base price for a difference between contracted and actual chemistry
    spec (e.g. % Mn or % Si content), using a premium/discount-per-percentage-point
    figure that must come from the actual contract or a quoted schedule --
    ferroalloy spec premiums vary by product, buyer, and market and are never
    assumed here.
    """
    _positive("base_price_per_ton", base_price_per_ton)
    _positive("base_spec_pct", base_spec_pct)
    _positive("actual_spec_pct", actual_spec_pct)
    if isinstance(premium_per_point_per_ton, bool) or not isinstance(premium_per_point_per_ton, (int, float)):
        raise ValueError("premium_per_point_per_ton must be a number")
    spec_diff_points = actual_spec_pct - base_spec_pct
    return base_price_per_ton + spec_diff_points * premium_per_point_per_ton


@dataclass(frozen=True)
class Shipment:
    quantity_tons: float
    price_per_ton: float


def weighted_average_price_per_ton(shipments: Iterable[Shipment]) -> float:
    items = tuple(shipments)
    if not items:
        raise ValueError("at_least_one_shipment_required")
    total_qty = 0.0
    total_value = 0.0
    for s in items:
        _positive("quantity_tons", s.quantity_tons)
        _positive("price_per_ton", s.price_per_ton)
        total_qty += s.quantity_tons
        total_value += s.quantity_tons * s.price_per_ton
    return total_value / total_qty


@dataclass(frozen=True)
class FALOpportunityEconomics:
    project_id: str
    lane_id: str
    landed_cost: LandedCostBreakdown
    margin: MarginResult
    viable: bool


def evaluate_fal_lane_opportunity(
    *,
    project_id: str,
    lane_id: str,
    fob_price_per_ton: float,
    freight_per_ton: float,
    insurance_rate: float,
    customs_duty_rate: float,
    target_sale_price_per_ton: float,
    other_fees_per_ton: float = 0.0,
) -> FALOpportunityEconomics:
    """Lane-scoped economics check for one FAL-A/FAL-B opportunity. This is a pure
    calculation -- it does not create an approval, a draft, or any commitment. Pair
    its output with opportunity_suggestion_engine.OpportunityQueue for the human
    review step; this function has no side effects and contacts nobody.
    """
    assert_lane_scope(project_id=project_id, lane_id=lane_id)
    cost = landed_cost_per_ton(
        fob_price_per_ton=fob_price_per_ton,
        freight_per_ton=freight_per_ton,
        insurance_rate=insurance_rate,
        customs_duty_rate=customs_duty_rate,
        other_fees_per_ton=other_fees_per_ton,
    )
    m = margin(landed_cost_per_ton=cost.landed_cost_per_ton, sale_price_per_ton=target_sale_price_per_ton)
    return FALOpportunityEconomics(
        project_id=project_id,
        lane_id=lane_id,
        landed_cost=cost,
        margin=m,
        viable=m.gross_margin_per_ton > 0,
    )
