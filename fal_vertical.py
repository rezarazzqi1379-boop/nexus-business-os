"""PRJ-FAL-01 canonical vertical binding for Deep Search / market intelligence.

Stable scope only, recovered from the canonical Ferroalloys Trade Master v0.2:
FAL-A = ferromanganese import into Iran; FAL-B = Iranian ferrosilicon export.
Dynamic commercial facts remain UNKNOWN until independently verified.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from market_intelligence import LaneDiscoveryBinding, RoleKeywordRule

PROJECT_ID = "PRJ-FAL-01"
HOME_MARKET_ID = "IRAN"
LANE_FAL_A = "FAL-A"
LANE_FAL_B = "FAL-B"
PRODUCT_FERROMANGANESE = "ferromanganese"
PRODUCT_FERROSILICON = "ferrosilicon"


@dataclass(frozen=True)
class FALVerticalLane:
    project_id: str
    lane_id: str
    direction: str
    product: str
    home_market_id: str
    home_market_role: str
    foreign_market_role: str
    commercial_state: str

    def validate(self) -> None:
        if self.project_id != PROJECT_ID:
            raise ValueError("invalid_fal_project_id")
        if self.lane_id not in {LANE_FAL_A, LANE_FAL_B}:
            raise ValueError("invalid_fal_lane_id")
        if self.direction not in {"IMPORT", "EXPORT"}:
            raise ValueError("invalid_fal_direction")
        if self.product not in {PRODUCT_FERROMANGANESE, PRODUCT_FERROSILICON}:
            raise ValueError("invalid_fal_product")
        if self.home_market_id != HOME_MARKET_ID:
            raise ValueError("invalid_fal_home_market")
        if self.commercial_state != "RESEARCH_UNKNOWN":
            raise ValueError("fal_dynamic_commercial_state_must_remain_unknown")
        LaneDiscoveryBinding(
            lane_id=self.lane_id,
            direction=self.direction,
            home_market_id=self.home_market_id,
            home_market_role=self.home_market_role,
            foreign_market_role=self.foreign_market_role,
        ).validate()


FAL_A = FALVerticalLane(
    project_id=PROJECT_ID,
    lane_id=LANE_FAL_A,
    direction="IMPORT",
    product=PRODUCT_FERROMANGANESE,
    home_market_id=HOME_MARKET_ID,
    home_market_role="END_USER",
    foreign_market_role="SUPPLIER",
    commercial_state="RESEARCH_UNKNOWN",
)

FAL_B = FALVerticalLane(
    project_id=PROJECT_ID,
    lane_id=LANE_FAL_B,
    direction="EXPORT",
    product=PRODUCT_FERROSILICON,
    home_market_id=HOME_MARKET_ID,
    home_market_role="PRODUCER",
    foreign_market_role="BUYER",
    commercial_state="RESEARCH_UNKNOWN",
)


# Minimal stable terminology only. No company names, prices, grades, HS codes, or routes.
FAL_ROLE_RULES = (
    RoleKeywordRule("LOGISTICS_INTERMEDIARY", ("logistics", "freight", "forwarding", "حمل و نقل", "حمل‌ونقل")),
    RoleKeywordRule("GOVERNMENT_TENDERING_BODY", ("tender", "procurement", "مناقصه", "تدارکات")),
    RoleKeywordRule("PRODUCER", ("producer", "manufacturer", "تولید کننده", "تولیدکننده")),
    RoleKeywordRule("SUPPLIER", ("supplier", "تامین کننده", "تأمین کننده", "تامین‌کننده", "تأمین‌کننده")),
    RoleKeywordRule("IMPORTER", ("importer", "وارد کننده", "واردکننده")),
    RoleKeywordRule("EXPORTER", ("exporter", "صادر کننده", "صادرکننده")),
    RoleKeywordRule("DISTRIBUTOR", ("distributor", "distribution", "توزیع کننده", "توزیع‌کننده")),
    RoleKeywordRule("TRADER", ("trader", "trading", "بازرگان", "تاجر")),
    RoleKeywordRule("BUYER", ("buyer", "purchase", "خریدار", "خرید")),
)


class FALIsolationError(ValueError):
    pass


def lane_by_id(lane_id: str) -> FALVerticalLane:
    if lane_id == LANE_FAL_A:
        return FAL_A
    if lane_id == LANE_FAL_B:
        return FAL_B
    raise ValueError("unknown_fal_lane")


def assert_lane_scope(*, project_id: str, lane_id: str) -> FALVerticalLane:
    lane = lane_by_id(lane_id)
    if project_id != lane.project_id:
        raise FALIsolationError("cross_project_contamination")
    lane.validate()
    return lane


def assert_same_lane_scope(left: Mapping[str, str], right: Mapping[str, str]) -> None:
    """Fail closed on any cross-project or cross-lane evidence join."""
    left_lane = assert_lane_scope(project_id=left.get("project_id", ""), lane_id=left.get("lane_id", ""))
    right_lane = assert_lane_scope(project_id=right.get("project_id", ""), lane_id=right.get("lane_id", ""))
    if left_lane.lane_id != right_lane.lane_id:
        raise FALIsolationError("cross_lane_contamination")


def canonical_scope_summary() -> dict[str, object]:
    for lane in (FAL_A, FAL_B):
        lane.validate()
    return {
        "project_id": PROJECT_ID,
        "home_market_id": HOME_MARKET_ID,
        "lanes": {
            LANE_FAL_A: {
                "direction": FAL_A.direction,
                "product": FAL_A.product,
                "home_market_role": FAL_A.home_market_role,
                "foreign_market_role": FAL_A.foreign_market_role,
                "commercial_state": FAL_A.commercial_state,
            },
            LANE_FAL_B: {
                "direction": FAL_B.direction,
                "product": FAL_B.product,
                "home_market_role": FAL_B.home_market_role,
                "foreign_market_role": FAL_B.foreign_market_role,
                "commercial_state": FAL_B.commercial_state,
            },
        },
        "dynamic_facts": "UNKNOWN_UNTIL_VERIFIED",
        "live_provider_state": "LIVE_PROVIDER_UNWIRED",
    }
