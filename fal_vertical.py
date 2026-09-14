"""Compatibility API for the parallel PRJ-FAL-01 vertical binding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from market_intelligence import LaneDiscoveryBinding, RoleKeywordRule

PROJECT_ID = "PRJ-FAL-01"
HOME_MARKET_ID = "IRAN"
LANE_FAL_A = "FAL-A"
LANE_FAL_B = "FAL-B"


@dataclass(frozen=True)
class FALVerticalLane:
    project_id: str; lane_id: str; direction: str; product: str
    home_market_id: str; home_market_role: str; foreign_market_role: str
    commercial_state: str

    def validate(self) -> None:
        if self.project_id != PROJECT_ID: raise ValueError("invalid_fal_project_id")
        if self.lane_id not in {LANE_FAL_A, LANE_FAL_B}: raise ValueError("invalid_fal_lane_id")
        if self.direction not in {"IMPORT", "EXPORT"}: raise ValueError("invalid_fal_direction")
        if self.product not in {"ferromanganese", "ferrosilicon"}: raise ValueError("invalid_fal_product")
        if self.home_market_id != HOME_MARKET_ID: raise ValueError("invalid_fal_home_market")
        if self.commercial_state != "RESEARCH_UNKNOWN":
            raise ValueError("fal_dynamic_commercial_state_must_remain_unknown")
        LaneDiscoveryBinding(self.lane_id, self.direction, self.home_market_id,
                             self.home_market_role, self.foreign_market_role).validate()


FAL_A = FALVerticalLane(PROJECT_ID, LANE_FAL_A, "IMPORT", "ferromanganese", HOME_MARKET_ID,
                        "END_USER", "SUPPLIER", "RESEARCH_UNKNOWN")
FAL_B = FALVerticalLane(PROJECT_ID, LANE_FAL_B, "EXPORT", "ferrosilicon", HOME_MARKET_ID,
                        "PRODUCER", "BUYER", "RESEARCH_UNKNOWN")
FAL_ROLE_RULES = (
    RoleKeywordRule("LOGISTICS_INTERMEDIARY", ("logistics", "حمل‌ونقل")),
    RoleKeywordRule("GOVERNMENT_TENDERING_BODY", ("tender", "مناقصه")),
    RoleKeywordRule("PRODUCER", ("producer", "تولیدکننده")),
    RoleKeywordRule("SUPPLIER", ("supplier", "تامین‌کننده")),
    RoleKeywordRule("IMPORTER", ("importer", "واردکننده")),
    RoleKeywordRule("EXPORTER", ("exporter", "صادرکننده")),
    RoleKeywordRule("DISTRIBUTOR", ("distributor", "توزیع‌کننده")),
    RoleKeywordRule("TRADER", ("trader", "بازرگان")),
    RoleKeywordRule("BUYER", ("buyer", "خریدار")),
)


class FALIsolationError(ValueError): pass


def lane_by_id(lane_id: str) -> FALVerticalLane:
    if lane_id == LANE_FAL_A: return FAL_A
    if lane_id == LANE_FAL_B: return FAL_B
    raise ValueError("unknown_fal_lane")


def assert_lane_scope(*, project_id: str, lane_id: str) -> FALVerticalLane:
    lane = lane_by_id(lane_id)
    if project_id != lane.project_id: raise FALIsolationError("cross_project_contamination")
    lane.validate()
    return lane


def assert_same_lane_scope(left: Mapping[str, str], right: Mapping[str, str]) -> None:
    left_lane = assert_lane_scope(project_id=left.get("project_id", ""), lane_id=left.get("lane_id", ""))
    right_lane = assert_lane_scope(project_id=right.get("project_id", ""), lane_id=right.get("lane_id", ""))
    if left_lane.lane_id != right_lane.lane_id: raise FALIsolationError("cross_lane_contamination")


def canonical_scope_summary() -> dict[str, object]:
    return {"project_id": PROJECT_ID, "home_market_id": HOME_MARKET_ID,
            "lanes": {lane.lane_id: {"direction": lane.direction, "product": lane.product,
            "home_market_role": lane.home_market_role, "foreign_market_role": lane.foreign_market_role,
            "commercial_state": lane.commercial_state} for lane in (FAL_A, FAL_B)},
            "dynamic_facts": "UNKNOWN_UNTIL_VERIFIED", "live_provider_state": "LIVE_PROVIDER_UNWIRED"}
