from __future__ import annotations

import unittest

from deep_search_fabric import ProviderPerformanceTracker
from market_intelligence import (
    ENTITY_ROLES,
    LaneDiscoveryBinding,
    MarketEvidence,
    MarketPriorityPlan,
    MarketTier,
    RoleKeywordRule,
    allocate_market_budget,
    classify_entity_role,
    is_buyer_role,
    rerank_markets_by_evidence,
)

# Placeholder market ids -- generic labels, not asserted business facts about any real market.
TIER0 = "MARKET-TIER0"
TIER1 = "MARKET-TIER1"
TIER2 = "MARKET-TIER2"
TIER3 = "MARKET-TIER3"


def plan(**tiers_override) -> MarketPriorityPlan:
    tiers = tiers_override.get("tiers") or (
        MarketTier(TIER0, 0, "home market prior"),
        MarketTier(TIER1, 1, "regional prior"),
        MarketTier(TIER2, 2, "secondary prior"),
        MarketTier(TIER3, 3, "rest of world prior"),
    )
    return MarketPriorityPlan(tiers=tiers)


def evidence(market_id: str, **changes) -> MarketEvidence:
    values = dict(market_id=market_id)
    values.update(changes)
    return MarketEvidence(**values)


class EntityRoleTests(unittest.TestCase):
    def test_all_documented_roles_are_present(self):
        expected = {
            "BUYER", "END_USER", "PRODUCER", "SUPPLIER", "DISTRIBUTOR", "TRADER", "IMPORTER",
            "EXPORTER", "LOGISTICS_INTERMEDIARY", "AGENT_INTERMEDIARY", "GOVERNMENT_TENDERING_BODY",
            "MARKET_PRICE_SOURCE", "UNKNOWN",
        }
        self.assertEqual(ENTITY_ROLES, expected)

    def test_buyer_and_end_user_are_buyer_roles(self):
        self.assertTrue(is_buyer_role("BUYER"))
        self.assertTrue(is_buyer_role("END_USER"))

    def test_logistics_is_never_a_buyer_role(self):
        self.assertFalse(is_buyer_role("LOGISTICS_INTERMEDIARY"))

    def test_government_tendering_body_is_never_a_buyer_role(self):
        self.assertFalse(is_buyer_role("GOVERNMENT_TENDERING_BODY"))

    def test_market_price_source_is_never_a_buyer_role(self):
        self.assertFalse(is_buyer_role("MARKET_PRICE_SOURCE"))

    def test_unknown_is_never_a_buyer_role(self):
        self.assertFalse(is_buyer_role("UNKNOWN"))

    def test_invalid_role_is_rejected(self):
        with self.assertRaises(ValueError):
            is_buyer_role("NOT_A_REAL_ROLE")


class ClassifyEntityRoleTests(unittest.TestCase):
    def test_ordered_rules_let_logistics_win_over_generic_buyer_keyword_in_same_text(self):
        rules = (
            RoleKeywordRule("LOGISTICS_INTERMEDIARY", ("forwarding", "حمل و نقل")),
            RoleKeywordRule("BUYER", ("purchase", "خرید")),
        )
        role, keyword = classify_entity_role("Example Forwarding Co handles purchase logistics.", rules)
        self.assertEqual(role, "LOGISTICS_INTERMEDIARY")
        self.assertEqual(keyword, "forwarding")

    def test_persian_keyword_is_matched_like_any_other(self):
        rules = (RoleKeywordRule("PRODUCER", ("تولید کننده", "producer")),)
        role, _ = classify_entity_role("این یک تولید کننده نمونه است", rules)
        self.assertEqual(role, "PRODUCER")

    def test_no_match_returns_unknown(self):
        rules = (RoleKeywordRule("BUYER", ("purchase",)),)
        role, keyword = classify_entity_role("nothing relevant here", rules)
        self.assertEqual(role, "UNKNOWN")
        self.assertEqual(keyword, "")

    def test_classification_is_never_influenced_by_repetition_count(self):
        # a fixed set of rules run once against text; nothing here counts occurrences or
        # supporting-record volume, so repeating the keyword changes nothing about the outcome.
        rules = (RoleKeywordRule("LOGISTICS_INTERMEDIARY", ("forwarding",)),)
        once = classify_entity_role("forwarding", rules)
        many = classify_entity_role("forwarding forwarding forwarding forwarding", rules)
        self.assertEqual(once, many)

    def test_invalid_rule_role_is_rejected(self):
        with self.assertRaises(ValueError):
            classify_entity_role("x", (RoleKeywordRule("NOT_A_REAL_ROLE", ("x",)),))

    def test_rule_with_no_keywords_is_rejected(self):
        with self.assertRaises(ValueError):
            RoleKeywordRule("BUYER", ()).validate()


class MarketPriorityPlanTests(unittest.TestCase):
    def test_ranked_market_ids_follows_tier_order(self):
        self.assertEqual(plan().ranked_market_ids(), (TIER0, TIER1, TIER2, TIER3))

    def test_duplicate_market_id_is_rejected(self):
        bad_plan = MarketPriorityPlan(tiers=(MarketTier("X", 0, "a"), MarketTier("X", 1, "b")))
        with self.assertRaises(ValueError):
            bad_plan.validate()

    def test_negative_tier_is_rejected(self):
        with self.assertRaises(ValueError):
            MarketTier("X", -1, "bad").validate()


class RerankByEvidenceTests(unittest.TestCase):
    def test_pure_prior_ranking_with_no_evidence_matches_tier_order(self):
        ranked = rerank_markets_by_evidence(plan(), {}, evidence_weight=0.0)
        self.assertEqual(ranked, (TIER0, TIER1, TIER2, TIER3))

    def test_strong_evidence_can_promote_a_lower_tier_market_above_a_higher_tier_one(self):
        strong_evidence = {
            TIER3: evidence(TIER3, demand_signal=1.0, procurement_signal=1.0, trade_flow_signal=1.0,
                           expected_value=1.0),
        }
        ranked = rerank_markets_by_evidence(plan(), strong_evidence, evidence_weight=1.0)
        self.assertEqual(ranked[0], TIER3)  # promoted to the top purely by evidence

    def test_missing_evidence_defaults_to_neutral_not_zero(self):
        # with evidence_weight=1.0 and NO evidence supplied for any market, every market gets
        # the same neutral 0.5 composite -- ties break by market_id, never by "looks unproven".
        ranked = rerank_markets_by_evidence(plan(), {}, evidence_weight=1.0)
        self.assertEqual(ranked, tuple(sorted((TIER0, TIER1, TIER2, TIER3))))

    def test_reranking_is_deterministic(self):
        first = rerank_markets_by_evidence(plan(), {TIER1: evidence(TIER1, demand_signal=0.8)})
        second = rerank_markets_by_evidence(plan(), {TIER1: evidence(TIER1, demand_signal=0.8)})
        self.assertEqual(first, second)

    def test_out_of_range_evidence_weight_is_rejected(self):
        with self.assertRaises(ValueError):
            rerank_markets_by_evidence(plan(), {}, evidence_weight=1.5)

    def test_out_of_range_evidence_field_is_rejected(self):
        with self.assertRaises(ValueError):
            evidence(TIER0, demand_signal=1.5).validate()


class MarketBudgetAllocationTests(unittest.TestCase):
    def test_seeded_allocation_never_exceeds_budget(self):
        tracker = ProviderPerformanceTracker()
        allocation = allocate_market_budget(tracker, plan(), {}, total_budget=100, min_floor=1)
        self.assertLessEqual(sum(allocation.values()), 100)

    def test_seeded_allocation_sums_to_budget_when_achievable(self):
        tracker = ProviderPerformanceTracker()
        allocation = allocate_market_budget(tracker, plan(), {}, total_budget=100, min_floor=1)
        self.assertEqual(sum(allocation.values()), 100)

    def test_tier0_gets_more_seed_budget_than_tier3_with_no_yield_data_yet(self):
        tracker = ProviderPerformanceTracker()
        allocation = allocate_market_budget(tracker, plan(), {}, total_budget=100, min_floor=1)
        self.assertGreater(allocation[TIER0], allocation[TIER3])

    def test_scarce_budget_never_exceeds_total(self):
        tracker = ProviderPerformanceTracker()
        allocation = allocate_market_budget(tracker, plan(), {}, total_budget=2, min_floor=1)
        self.assertLessEqual(sum(allocation.values()), 2)

    def test_once_real_yield_exists_allocation_responds_to_it_not_just_the_prior(self):
        tracker = ProviderPerformanceTracker()
        tracker.record(TIER3, 0, new_unique_entities=9, total_results=10)
        tracker.record(TIER0, 0, new_unique_entities=0, total_results=10)
        allocation = allocate_market_budget(tracker, plan(), {}, total_budget=100, min_floor=1)
        self.assertGreater(allocation[TIER3], allocation[TIER0])

    def test_evidence_shifted_allocation_still_never_exceeds_budget(self):
        tracker = ProviderPerformanceTracker()
        strong_evidence = {TIER3: evidence(TIER3, demand_signal=1.0, expected_value=1.0)}
        allocation = allocate_market_budget(tracker, plan(), strong_evidence, total_budget=17, min_floor=1)
        self.assertLessEqual(sum(allocation.values()), 17)


class LaneDiscoveryBindingTests(unittest.TestCase):
    def test_valid_export_lane_binding(self):
        LaneDiscoveryBinding(
            lane_id="LANE-EXPORT-EXAMPLE", direction="EXPORT", home_market_id=TIER0,
            home_market_role="PRODUCER", foreign_market_role="BUYER",
        ).validate()

    def test_valid_import_lane_binding(self):
        LaneDiscoveryBinding(
            lane_id="LANE-IMPORT-EXAMPLE", direction="IMPORT", home_market_id=TIER0,
            home_market_role="END_USER", foreign_market_role="SUPPLIER",
        ).validate()

    def test_home_and_foreign_roles_must_differ(self):
        with self.assertRaisesRegex(ValueError, "home_and_foreign_roles_must_differ"):
            LaneDiscoveryBinding(
                lane_id="LANE-BAD", direction="EXPORT", home_market_id=TIER0,
                home_market_role="BUYER", foreign_market_role="BUYER",
            ).validate()

    def test_invalid_direction_is_rejected(self):
        with self.assertRaises(ValueError):
            LaneDiscoveryBinding(
                lane_id="LANE-BAD", direction="SIDEWAYS", home_market_id=TIER0,
                home_market_role="PRODUCER", foreign_market_role="BUYER",
            ).validate()

    def test_invalid_role_is_rejected(self):
        with self.assertRaises(ValueError):
            LaneDiscoveryBinding(
                lane_id="LANE-BAD", direction="EXPORT", home_market_id=TIER0,
                home_market_role="NOT_A_REAL_ROLE", foreign_market_role="BUYER",
            ).validate()


if __name__ == "__main__":
    unittest.main()
