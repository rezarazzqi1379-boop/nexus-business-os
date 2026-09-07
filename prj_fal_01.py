"""PRJ-FAL-01 (Ferroalloys Trade) -- lane configuration and cross-module wiring.

This module is a working structural model derived from disputed/reconciling project
artifacts; authority promotion pending. It encodes only the STRUCTURAL scope common to
every version of those artifacts encountered so far -- project id, lane ids, directions,
roles, the lane-isolation rule, and a minimal generic domain lexicon -- never a
specification number, price, chemistry value, or counterparty/producer identity. Every one
of those remains UNKNOWN pending independent verification and authority reconciliation;
encoding a live, frequently-revised evidence value here would let it silently calcify into
a stale "fact" baked into code, which this module's own discipline forbids.

FAL-A (ferromanganese import into Iran) and FAL-B (Iranian ferrosilicon export) are related
only at portfolio level: grades, prices, counterparties, origins, destinations, routes and
feasibility assumptions must never transfer between them. Two structural mechanisms
enforce that here:
  1. ``FalLaneEvidenceStore`` -- a per-lane MarketEvidence mapping, so both lanes can
     legitimately reference the same home market_id ("IRAN") without their evidence
     colliding under one shared dict key.
  2. ``classify_fal_buyer_opportunity()`` -- see its docstring for a real cross-module
     vocabulary conflict this resolves for this project specifically.

No live Iranian source is read anywhere in this module -- see iran_source_providers.py's
integration report; this project's live provider state remains LIVE_PROVIDER_UNWIRED.

Authority-version dispute handling: this project's authority status is
AUTHORITY_CONFLICT / RECONCILIATION_PENDING. See SOURCE_VERSION_DISPUTED below for the
generic convention this module uses if a future field's value ever depends on which side
of an unresolved authority dispute is correct. Nothing in this module currently needs that
tag: every field here (lane direction, role, lexicon) is structural and holds regardless
of how that dispute resolves.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from discovery_pipeline import BuyerClassification  # noqa: E402
from market_intelligence import (  # noqa: E402
    ENTITY_ROLES,
    LaneDiscoveryBinding,
    MarketEvidence,
    RoleKeywordRule,
    is_buyer_role,
)

PROJECT_ID = "PRJ-FAL-01"
HOME_MARKET_ID = "IRAN"

# Tag for any field/claim whose correct value depends on which of two conflicting external
# authority-document versions governs. Use this literal (never a guessed value) if a
# future field must carry a version-specific claim before that conflict is independently
# resolved -- do not silently pick one version's claim as ground truth. Nothing exported
# from this module currently carries this tag.
SOURCE_VERSION_DISPUTED = "SOURCE_VERSION_DISPUTED"

FAL_A_LANE_ID = "FAL-A"
FAL_B_LANE_ID = "FAL-B"
FAL_LANE_IDS = frozenset({FAL_A_LANE_ID, FAL_B_LANE_ID})

# FAL-A: ferromanganese import into Iran -- Iran is the importing/end-market side, the
# foreign market is the supply side. Every specification/price/counterparty field remains
# UNKNOWN pending authority reconciliation; nothing beyond the structural lane shape
# belongs here.
FAL_A = LaneDiscoveryBinding(
    lane_id=FAL_A_LANE_ID, direction="IMPORT", home_market_id=HOME_MARKET_ID,
    home_market_role="IMPORTER", foreign_market_role="SUPPLIER",
)

# FAL-B: Iranian ferrosilicon export -- Iran is the exporting/supply side, the foreign
# market is the buyer side. No specification, chemistry, or producer identity is encoded
# here; those remain unresolved pending authority reconciliation.
FAL_B = LaneDiscoveryBinding(
    lane_id=FAL_B_LANE_ID, direction="EXPORT", home_market_id=HOME_MARKET_ID,
    home_market_role="EXPORTER", foreign_market_role="BUYER",
)

LANES = (FAL_A, FAL_B)


def validate_lanes() -> None:
    for lane in LANES:
        lane.validate()
    if FAL_A.direction == FAL_B.direction:
        raise ValueError("fal_a_and_fal_b_must_have_different_directions")


# ---------------------------------------------------------------------------
# Minimal generic product/role lexicon (English + Persian). No real company names, no
# chemistry, no prices -- only generic product/role terminology common across the
# disputed/reconciling project artifacts.
# Rule order matters: logistics and tendering-body keywords are checked before buyer/
# supplier keywords so a freight forwarder or tender notice is never misclassified as a
# counterparty just because "buyer"-adjacent language appears nearby in the same text.
# ---------------------------------------------------------------------------

FAL_A_PRODUCT_KEYWORDS = ("ferromanganese", "فرو منگنز")
FAL_B_PRODUCT_KEYWORDS = ("ferrosilicon", "فروسیلیس")

FAL_ROLE_RULES = (
    RoleKeywordRule("LOGISTICS_INTERMEDIARY", ("logistics", "حمل‌ونقل")),
    RoleKeywordRule("GOVERNMENT_TENDERING_BODY", ("tender", "مناقصه")),
    RoleKeywordRule("SUPPLIER", ("supplier", "تامین‌کننده")),
    RoleKeywordRule("PRODUCER", ("producer", "تولیدکننده")),
    RoleKeywordRule("IMPORTER", ("importer", "واردکننده")),
    RoleKeywordRule("EXPORTER", ("exporter", "صادرکننده")),
    RoleKeywordRule("DISTRIBUTOR", ("distributor", "توزیع‌کننده")),
    RoleKeywordRule("TRADER", ("trader", "بازرگان")),
    RoleKeywordRule("BUYER", ("buyer", "خریدار")),
)


def validate_role_rules() -> None:
    for rule in FAL_ROLE_RULES:
        rule.validate()
    if set(FAL_A_PRODUCT_KEYWORDS) & set(FAL_B_PRODUCT_KEYWORDS):
        raise ValueError("fal_a_and_fal_b_product_keywords_must_not_overlap")


# ---------------------------------------------------------------------------
# 1. Lane-isolated evidence store
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FalLaneEvidenceStore:
    """Per-lane MarketEvidence mapping. FAL-A and FAL-B both legitimately use
    home_market_id="IRAN", so a single shared ``{market_id: MarketEvidence}`` dict would
    let FAL-A's Iran-side evidence silently collide with FAL-B's under the same key.
    Keying by (lane_id, market_id) instead makes that collision structurally impossible --
    the enforced version of the working rule that lane evidence must never transfer between
    FAL-A and FAL-B.
    """

    by_lane: Mapping[str, Mapping[str, MarketEvidence]]

    def validate(self) -> None:
        unknown = set(self.by_lane) - FAL_LANE_IDS
        if unknown:
            raise ValueError("unknown_fal_lane_id")
        for lane_id, evidence_map in self.by_lane.items():
            for market_id, ev in evidence_map.items():
                if ev.market_id != market_id:
                    raise ValueError("evidence_market_id_key_mismatch")
                ev.validate()

    def evidence_for(self, lane_id: str, market_id: str) -> MarketEvidence | None:
        self.validate()
        if lane_id not in FAL_LANE_IDS:
            raise ValueError("unknown_fal_lane_id")
        return self.by_lane.get(lane_id, {}).get(market_id)


# ---------------------------------------------------------------------------
# 2. Buyer-opportunity classification -- resolves a real cross-module vocabulary conflict
# ---------------------------------------------------------------------------

_CATEGORY_TO_ROLE = {
    "steel_mill": "END_USER",
    "foundry": "END_USER",
    "importer": "IMPORTER",
    "trader": "TRADER",
    "distributor": "DISTRIBUTOR",
    "procurement_authority": "GOVERNMENT_TENDERING_BODY",
    "logistics_intermediary": "LOGISTICS_INTERMEDIARY",
    "unknown": "UNKNOWN",
}

assert set(_CATEGORY_TO_ROLE.values()) <= ENTITY_ROLES  # every mapped role must be real


def classify_fal_buyer_opportunity(classification: BuyerClassification) -> bool:
    """Whether a discovery_pipeline.BuyerClassification is a real buyer opportunity for
    PRJ-FAL-01 -- deliberately NOT the same question as ``classification.is_buyer_opportunity``.

    discovery_pipeline.py's own ``is_buyer_opportunity`` excludes only "unknown" and
    "logistics_intermediary" -- it treats "procurement_authority" as a buyer.
    market_intelligence.py's fuller taxonomy treats the equivalent
    GOVERNMENT_TENDERING_BODY role as *never* a buyer, because a tendering body issues a
    demand signal but is not itself the counterparty. This function enforces that stricter,
    generically safer rule for this project rather than silently inheriting
    discovery_pipeline's looser cross-project default. It only remaps a
    BuyerClassification.category value to a role and checks is_buyer_role() -- it does not
    reference any specific counterparty, tender, or evidence record.
    """
    classification.validate()
    role = _CATEGORY_TO_ROLE[classification.category]
    return is_buyer_role(role)
