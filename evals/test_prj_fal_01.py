from __future__ import annotations

import unittest

from discovery_pipeline import BuyerClassification
from market_intelligence import MarketEvidence, classify_entity_role
from prj_fal_01 import (
    FAL_A,
    FAL_A_LANE_ID,
    FAL_A_PRODUCT_KEYWORDS,
    FAL_B,
    FAL_B_LANE_ID,
    FAL_B_PRODUCT_KEYWORDS,
    FAL_ROLE_RULES,
    HOME_MARKET_ID,
    FalLaneEvidenceStore,
    classify_fal_buyer_opportunity,
    validate_lanes,
    validate_role_rules,
)


def buyer_classification(**overrides) -> BuyerClassification:
    values = dict(entity_candidate_id="cand-1", category="steel_mill", confidence=0.8, basis="text match")
    values.update(overrides)
    return BuyerClassification(**values)


def evidence(market_id: str, **changes) -> MarketEvidence:
    values = dict(market_id=market_id)
    values.update(changes)
    return MarketEvidence(**values)


class LaneConfigurationTests(unittest.TestCase):
    def test_fal_a_is_an_import_lane(self):
        self.assertEqual(FAL_A.direction, "IMPORT")

    def test_fal_b_is_an_export_lane(self):
        self.assertEqual(FAL_B.direction, "EXPORT")

    def test_fal_a_home_role_is_importer_foreign_role_is_supplier(self):
        self.assertEqual(FAL_A.home_market_role, "IMPORTER")
        self.assertEqual(FAL_A.foreign_market_role, "SUPPLIER")

    def test_fal_b_home_role_is_exporter_foreign_role_is_buyer(self):
        self.assertEqual(FAL_B.home_market_role, "EXPORTER")
        self.assertEqual(FAL_B.foreign_market_role, "BUYER")

    def test_both_lanes_share_the_same_home_market_id(self):
        # portfolio-level relation only -- evidence isolation is enforced separately by
        # FalLaneEvidenceStore, not by giving the lanes different home markets.
        self.assertEqual(FAL_A.home_market_id, HOME_MARKET_ID)
        self.assertEqual(FAL_B.home_market_id, HOME_MARKET_ID)

    def test_validate_lanes_passes(self):
        validate_lanes()  # must not raise

    def test_validate_role_rules_passes(self):
        validate_role_rules()  # must not raise

    def test_fal_a_and_fal_b_product_keywords_never_overlap(self):
        self.assertFalse(set(FAL_A_PRODUCT_KEYWORDS) & set(FAL_B_PRODUCT_KEYWORDS))


class FalLaneEvidenceStoreTests(unittest.TestCase):
    def test_same_home_market_id_evidence_does_not_collide_across_lanes(self):
        store = FalLaneEvidenceStore(by_lane={
            FAL_A_LANE_ID: {HOME_MARKET_ID: evidence(HOME_MARKET_ID, demand_signal=1.0)},
            FAL_B_LANE_ID: {HOME_MARKET_ID: evidence(HOME_MARKET_ID, demand_signal=0.0)},
        })
        self.assertEqual(store.evidence_for(FAL_A_LANE_ID, HOME_MARKET_ID).demand_signal, 1.0)
        self.assertEqual(store.evidence_for(FAL_B_LANE_ID, HOME_MARKET_ID).demand_signal, 0.0)

    def test_missing_market_in_a_lane_returns_none_not_error(self):
        store = FalLaneEvidenceStore(by_lane={FAL_A_LANE_ID: {}})
        self.assertIsNone(store.evidence_for(FAL_A_LANE_ID, "SOME-FOREIGN-MARKET"))

    def test_unknown_lane_id_on_lookup_is_rejected(self):
        store = FalLaneEvidenceStore(by_lane={})
        with self.assertRaisesRegex(ValueError, "unknown_fal_lane_id"):
            store.evidence_for("FAL-Z", HOME_MARKET_ID)

    def test_unknown_lane_id_in_by_lane_is_rejected_on_validate(self):
        store = FalLaneEvidenceStore(by_lane={"FAL-Z": {}})
        with self.assertRaisesRegex(ValueError, "unknown_fal_lane_id"):
            store.validate()

    def test_market_id_key_mismatch_is_rejected(self):
        store = FalLaneEvidenceStore(by_lane={FAL_A_LANE_ID: {HOME_MARKET_ID: evidence("SOMEWHERE-ELSE")}})
        with self.assertRaisesRegex(ValueError, "evidence_market_id_key_mismatch"):
            store.validate()

    def test_invalid_evidence_is_rejected_on_validate(self):
        store = FalLaneEvidenceStore(by_lane={FAL_A_LANE_ID: {HOME_MARKET_ID: evidence(HOME_MARKET_ID, demand_signal=5.0)}})
        with self.assertRaises(ValueError):
            store.validate()


class FalBuyerOpportunityTests(unittest.TestCase):
    def test_steel_mill_is_a_fal_buyer_opportunity(self):
        self.assertTrue(classify_fal_buyer_opportunity(buyer_classification(category="steel_mill")))

    def test_importer_trader_distributor_are_fal_buyer_opportunities(self):
        for category in ("importer", "trader", "distributor", "foundry"):
            self.assertTrue(classify_fal_buyer_opportunity(buyer_classification(category=category)),
                           f"{category} should be a FAL buyer opportunity")

    def test_logistics_intermediary_is_never_a_fal_buyer_opportunity(self):
        self.assertFalse(classify_fal_buyer_opportunity(buyer_classification(category="logistics_intermediary")))

    def test_unknown_is_never_a_fal_buyer_opportunity(self):
        self.assertFalse(classify_fal_buyer_opportunity(buyer_classification(category="unknown")))

    def test_procurement_authority_is_not_a_fal_buyer_opportunity(self):
        # The real regression this module exists to prevent -- see classify_fal_buyer_opportunity's
        # docstring: discovery_pipeline.py's own is_buyer_opportunity disagrees with this.
        self.assertFalse(classify_fal_buyer_opportunity(buyer_classification(category="procurement_authority")))

    def test_this_deliberately_differs_from_discovery_pipelines_own_is_buyer_opportunity(self):
        classification = buyer_classification(category="procurement_authority")
        self.assertTrue(classification.is_buyer_opportunity)  # discovery_pipeline's looser default
        self.assertFalse(classify_fal_buyer_opportunity(classification))  # FAL's stricter rule

    def test_invalid_classification_is_rejected(self):
        with self.assertRaises(ValueError):
            classify_fal_buyer_opportunity(buyer_classification(confidence=5.0))


class FalRoleLexiconTests(unittest.TestCase):
    def test_logistics_keyword_wins_over_buyer_keyword_in_same_text(self):
        role, keyword = classify_entity_role("این تامین‌کننده حمل‌ونقل هم انجام می‌دهد", FAL_ROLE_RULES)
        self.assertEqual(role, "LOGISTICS_INTERMEDIARY")
        self.assertEqual(keyword, "حمل‌ونقل")

    def test_tender_keyword_classifies_as_government_tendering_body_not_buyer(self):
        role, _ = classify_entity_role("این یک مناقصه برای خریدار است", FAL_ROLE_RULES)
        self.assertEqual(role, "GOVERNMENT_TENDERING_BODY")

    def test_english_and_persian_variants_of_each_role_agree(self):
        pairs = {
            "SUPPLIER": ("a supplier of raw material", "یک تامین‌کننده مواد اولیه"),
            "PRODUCER": ("a producer of ferroalloys", "یک تولیدکننده فروآلیاژ"),
            "IMPORTER": ("acting as importer", "به عنوان واردکننده"),
            "EXPORTER": ("acting as exporter", "به عنوان صادرکننده"),
            "DISTRIBUTOR": ("a regional distributor", "یک توزیع‌کننده منطقه‌ای"),
            "TRADER": ("an independent trader", "یک بازرگان مستقل"),
            "BUYER": ("the end buyer", "خریدار نهایی"),
        }
        for role, (english_text, persian_text) in pairs.items():
            english_role, _ = classify_entity_role(english_text, FAL_ROLE_RULES)
            persian_role, _ = classify_entity_role(persian_text, FAL_ROLE_RULES)
            self.assertEqual(english_role, role, english_text)
            self.assertEqual(persian_role, role, persian_text)

    def test_ferromanganese_and_ferrosilicon_keywords_are_disjoint(self):
        for kw in FAL_A_PRODUCT_KEYWORDS:
            self.assertNotIn(kw, FAL_B_PRODUCT_KEYWORDS)


if __name__ == "__main__":
    unittest.main()
