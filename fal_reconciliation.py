"""Authority-neutral reconciliation layer for the two PRJ-FAL-01 APIs.

The legacy APIs describe different role dimensions.  This module preserves both instead
of promoting either branch's terminology to canonical authority.  Commercial facts stay
unknown (or explicitly source-version-disputed) until separately verified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

PROJECT_ID = "PRJ-FAL-01"
HOME_MARKET_ID = "IRAN"
FAL_A_LANE_ID = "FAL-A"
FAL_B_LANE_ID = "FAL-B"
UNKNOWN = "UNKNOWN"
SOURCE_VERSION_DISPUTED = "SOURCE_VERSION_DISPUTED"
_UNRESOLVED_VALUES = frozenset({UNKNOWN, SOURCE_VERSION_DISPUTED})


class FALReconciliationError(ValueError):
    """Raised when an adapter would blur project, lane, or authority boundaries."""


@dataclass(frozen=True)
class RoleDimensions:
    """Roles separated by meaning; neither dimension overwrites the other."""

    operational: str
    economic: str

    def validate(self) -> None:
        if not self.operational.strip() or not self.economic.strip():
            raise FALReconciliationError("fal_role_dimension_must_be_explicit")


@dataclass(frozen=True)
class ReconciledFALLane:
    project_id: str
    lane_id: str
    direction: str
    product: str
    home_market_id: str
    home_roles: RoleDimensions
    foreign_roles: RoleDimensions
    dynamic_facts: Mapping[str, str] = field(default_factory=dict)
    authority_state: str = "RECONCILIATION_PENDING"

    def validate(self) -> None:
        if self.project_id != PROJECT_ID:
            raise FALReconciliationError("cross_project_contamination")
        if self.lane_id not in {FAL_A_LANE_ID, FAL_B_LANE_ID}:
            raise FALReconciliationError("unknown_fal_lane_id")
        if self.direction not in {"IMPORT", "EXPORT"}:
            raise FALReconciliationError("invalid_fal_direction")
        if self.home_market_id != HOME_MARKET_ID:
            raise FALReconciliationError("invalid_fal_home_market")
        if self.authority_state != "RECONCILIATION_PENDING":
            raise FALReconciliationError("authority_promotion_requires_approval")
        self.home_roles.validate()
        self.foreign_roles.validate()
        if any(value not in _UNRESOLVED_VALUES for value in self.dynamic_facts.values()):
            raise FALReconciliationError("dynamic_fact_must_remain_unknown_or_disputed")


_PRODUCTS = {FAL_A_LANE_ID: "ferromanganese", FAL_B_LANE_ID: "ferrosilicon"}
_OPERATIONAL = {
    FAL_A_LANE_ID: ("END_USER", "SUPPLIER"),
    FAL_B_LANE_ID: ("PRODUCER", "BUYER"),
}
_ECONOMIC = {
    FAL_A_LANE_ID: ("IMPORTER", "SUPPLIER"),
    FAL_B_LANE_ID: ("EXPORTER", "BUYER"),
}


def reconciled_lane(lane_id: str, *, dynamic_facts: Mapping[str, str] | None = None) -> ReconciledFALLane:
    if lane_id not in _PRODUCTS:
        raise FALReconciliationError("unknown_fal_lane_id")
    direction = "IMPORT" if lane_id == FAL_A_LANE_ID else "EXPORT"
    home_operational, foreign_operational = _OPERATIONAL[lane_id]
    home_economic, foreign_economic = _ECONOMIC[lane_id]
    lane = ReconciledFALLane(
        project_id=PROJECT_ID,
        lane_id=lane_id,
        direction=direction,
        product=_PRODUCTS[lane_id],
        home_market_id=HOME_MARKET_ID,
        home_roles=RoleDimensions(home_operational, home_economic),
        foreign_roles=RoleDimensions(foreign_operational, foreign_economic),
        dynamic_facts=dict(dynamic_facts or {}),
    )
    lane.validate()
    return lane


def from_prj_binding(binding: object) -> ReconciledFALLane:
    """Adapt ``prj_fal_01.LaneDiscoveryBinding`` without trusting it across lanes."""
    lane = reconciled_lane(getattr(binding, "lane_id", ""))
    expected = (lane.direction, lane.home_market_id, lane.home_roles.economic, lane.foreign_roles.economic)
    actual = tuple(getattr(binding, name, "") for name in
                   ("direction", "home_market_id", "home_market_role", "foreign_market_role"))
    if actual != expected:
        raise FALReconciliationError("prj_binding_semantic_mismatch")
    return lane


def from_vertical_lane(vertical: object) -> ReconciledFALLane:
    """Adapt ``fal_vertical.FALVerticalLane`` while preserving its role dimension."""
    lane = reconciled_lane(getattr(vertical, "lane_id", ""), dynamic_facts={"commercial": UNKNOWN})
    expected = (lane.project_id, lane.direction, lane.product, lane.home_market_id,
                lane.home_roles.operational, lane.foreign_roles.operational, "RESEARCH_UNKNOWN")
    actual = tuple(getattr(vertical, name, "") for name in (
        "project_id", "direction", "product", "home_market_id", "home_market_role",
        "foreign_market_role", "commercial_state"))
    if actual != expected:
        raise FALReconciliationError("vertical_lane_semantic_mismatch")
    return lane


def assert_same_reconciled_scope(left: ReconciledFALLane, right: ReconciledFALLane) -> None:
    left.validate()
    right.validate()
    if left.project_id != right.project_id:
        raise FALReconciliationError("cross_project_contamination")
    if left.lane_id != right.lane_id:
        raise FALReconciliationError("cross_lane_contamination")
