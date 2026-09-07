from __future__ import annotations

import unittest

from fal_vertical import (
    FAL_A,
    FAL_B,
    FALIsolationError,
    FAL_ROLE_RULES,
    HOME_MARKET_ID,
    LANE_FAL_A,
    LANE_FAL_B,
    PROJECT_ID,
    assert_lane_scope,
    assert_same_lane_scope,
    canonical_scope_summary,
)
from market_intelligence import classify_entity_role


class CanonicalScopeTests(unittest.TestCase):
    def test_fal_a_is_ferromanganese_import_into_iran(self):
        FAL_A.validate()
        self.assertEqual(FAL_A.project_id, PROJECT_ID)
        self.assertEqual(FAL_A.lane_id, LANE_FAL_A)
        self.assertEqual(FAL_A.direction, "IMPORT")
        self.assertEqual(FAL_A.product, "ferromanganese")
        self.assertEqual(FAL_A.home_market_id, HOME_MARKET_ID)
        self.assertEqual(FAL_A.home_market_role, "END_USER")
        self.assertEqual(FAL_A.foreign_market_role, "SUPPLIER")

    def test_fal_b_is_ferrosilicon_export_from_iran(self):
        FAL_B.validate()
        self.assertEqual(FAL_B.project_id, PROJECT_ID)
        self.assertEqual(FAL_B.lane_id, LANE_FAL_B)
        self.assertEqual(FAL_B.direction, "EXPORT")
        self.assertEqual(FAL_B.product, "ferrosilicon")
        self.assertEqual(FAL_B.home_market_id, HOME_MARKET_ID)
        self.assertEqual(FAL_B.home_market_role, "PRODUCER")
        self.assertEqual(FAL_B.foreign_market_role, "BUYER")

    def test_dynamic_commercial_facts_remain_unknown(self):
        summary = canonical_scope_summary()
        self.assertEqual(summary["dynamic_facts"], "UNKNOWN_UNTIL_VERIFIED")
        self.assertEqual(summary["live_provider_state"], "LIVE_PROVIDER_UNWIRED")
        self.assertEqual(summary["lanes"][LANE_FAL_A]["commercial_state"], "RESEARCH_UNKNOWN")
        self.assertEqual(summary["lanes"][LANE_FAL_B]["commercial_state"], "RESEARCH_UNKNOWN")


class LaneIsolationTests(unittest.TestCase):
    def test_fal_a_scope_is_accepted(self):
        lane = assert_lane_scope(project_id=PROJECT_ID, lane_id=LANE_FAL_A)
        self.assertEqual(lane, FAL_A)

    def test_fal_b_scope_is_accepted(self):
        lane = assert_lane_scope(project_id=PROJECT_ID, lane_id=LANE_FAL_B)
        self.assertEqual(lane, FAL_B)

    def test_wrong_project_fails_closed(self):
        with self.assertRaisesRegex(FALIsolationError, "cross_project_contamination"):
            assert_lane_scope(project_id="PRJ-KCL-01", lane_id=LANE_FAL_A)

    def test_fal_a_supplier_evidence_cannot_join_fal_b_buyer_evidence(self):
        supplier = {"project_id": PROJECT_ID, "lane_id": LANE_FAL_A, "role": "SUPPLIER"}
        buyer = {"project_id": PROJECT_ID, "lane_id": LANE_FAL_B, "role": "BUYER"}
        with self.assertRaisesRegex(FALIsolationError, "cross_lane_contamination"):
            assert_same_lane_scope(supplier, buyer)

    def test_fal_b_producer_claim_cannot_join_fal_a_specification(self):
        producer_claim = {"project_id": PROJECT_ID, "lane_id": LANE_FAL_B, "evidence_class": "CLAIM"}
        import_spec = {"project_id": PROJECT_ID, "lane_id": LANE_FAL_A, "evidence_class": "UNKNOWN"}
        with self.assertRaisesRegex(FALIsolationError, "cross_lane_contamination"):
            assert_same_lane_scope(producer_claim, import_spec)

    def test_same_lane_join_is_allowed(self):
        left = {"project_id": PROJECT_ID, "lane_id": LANE_FAL_A}
        right = {"project_id": PROJECT_ID, "lane_id": LANE_FAL_A}
        self.assertIsNone(assert_same_lane_scope(left, right))


class MinimalRoleLexiconTests(unittest.TestCase):
    def test_persian_supplier_term(self):
        role, _ = classify_entity_role("این شرکت تامین‌کننده مواد اولیه است", FAL_ROLE_RULES)
        self.assertEqual(role, "SUPPLIER")

    def test_persian_buyer_term(self):
        role, _ = classify_entity_role("خریدار فروسیلیس", FAL_ROLE_RULES)
        self.assertEqual(role, "BUYER")

    def test_logistics_has_priority_over_buyer(self):
        role, _ = classify_entity_role("شرکت حمل‌ونقل برای خرید کالا", FAL_ROLE_RULES)
        self.assertEqual(role, "LOGISTICS_INTERMEDIARY")

    def test_tender_body_is_not_silently_a_buyer(self):
        role, _ = classify_entity_role("اعلام مناقصه و تدارکات خرید", FAL_ROLE_RULES)
        self.assertEqual(role, "GOVERNMENT_TENDERING_BODY")


if __name__ == "__main__":
    unittest.main()
