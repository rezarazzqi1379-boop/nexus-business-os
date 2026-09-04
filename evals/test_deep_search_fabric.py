from __future__ import annotations

import unittest
from hashlib import sha256

from deep_search_fabric import (
    CoverageGap,
    EvidenceGraph,
    EvidenceLink,
    ProviderPerformanceTracker,
    QueryNode,
    SearchFrontier,
    StopDecision,
    _gap_id_for,
    allocate_budget,
    build_query_lattice,
    classify_temporal_state,
    detect_coverage_gaps,
    evaluate_stop_conditions,
    expand_entity_relationships,
    generate_expansion_queries,
    make_query_id,
    query_family,
    reconcile_gap_history,
    run_recursive_search,
)
from discovery_pipeline import NormalizedDiscoveryResult, QueryExpansionPlan, group_duplicates, resolve_entities

UTC_NOW = "2026-09-04T10:00:00+00:00"
RECENT = "2026-08-20T00:00:00+00:00"
STALE = "2023-01-01T00:00:00+00:00"
OLD_DATE = "2023-01-01T00:00:00+00:00"


def plan(**changes) -> QueryExpansionPlan:
    values = dict(
        objective="Find plausible buyers.", project_id="PRJ-EXAMPLE-01", lane_id="LANE-A",
        query_set_version="qsv-v0.1", product_terms=("widget", "gadget"), buyer_terms=("distributor",),
        procurement_terms=("tender",), industry_terms=("manufacturing",), geography_terms=("Exampleland",),
        language_terms=("en",),
    )
    values.update(changes)
    return QueryExpansionPlan(**values)


def result(**changes) -> NormalizedDiscoveryResult:
    values = dict(
        provider="synthetic-a", query="widget distributor Exampleland", url="https://example.invalid/company-a",
        title="Example Company A", snippet="Example Company A listed for widget distribution.",
        retrieved_at=UTC_NOW, published_at=RECENT, project_id="PRJ-EXAMPLE-01", lane_id="LANE-A",
        entity_name_hint="Example Company A", country_hint="Exampleland", buyer_type_hint=None,
    )
    values.update(changes)
    return NormalizedDiscoveryResult(**values)


class QueryLatticeTests(unittest.TestCase):
    def test_build_lattice_produces_depth_zero_nodes(self):
        lattice = build_query_lattice(plan())
        self.assertTrue(all(n.search_depth == 0 for n in lattice.root_nodes))
        self.assertTrue(all(n.parent_query_id is None for n in lattice.root_nodes))
        self.assertTrue(all(n.origin == "initial" for n in lattice.root_nodes))

    def test_lattice_is_deterministic(self):
        self.assertEqual(build_query_lattice(plan()).root_nodes, build_query_lattice(plan()).root_nodes)

    def test_query_id_is_stable_for_same_inputs(self):
        self.assertEqual(make_query_id("q", None, 0), make_query_id("q", None, 0))
        self.assertNotEqual(make_query_id("q", None, 0), make_query_id("q", "parent", 1))


class SearchFrontierTests(unittest.TestCase):
    def test_add_is_idempotent(self):
        frontier = SearchFrontier()
        node = QueryNode("q1", "text", None, 0, "initial")
        self.assertTrue(frontier.add(node))
        self.assertFalse(frontier.add(node))
        self.assertEqual(len(frontier), 1)

    def test_new_node_starts_in_new_state(self):
        frontier = SearchFrontier()
        frontier.add(QueryNode("q1", "text", None, 0, "initial"))
        self.assertEqual(frontier.state("q1"), "NEW")

    def test_rejects_unknown_state_value(self):
        frontier = SearchFrontier()
        frontier.add(QueryNode("q1", "text", None, 0, "initial"))
        with self.assertRaises(ValueError):
            frontier.set_state("q1", "NOT_A_REAL_STATE")

    def test_unknown_query_id_raises(self):
        frontier = SearchFrontier()
        with self.assertRaises(KeyError):
            frontier.set_state("no-such-id", "QUEUED")

    def test_nodes_in_state_filters_correctly(self):
        frontier = SearchFrontier()
        frontier.add(QueryNode("q1", "a", None, 0, "initial"))
        frontier.add(QueryNode("q2", "b", None, 0, "initial"))
        frontier.set_state("q1", "QUEUED")
        self.assertEqual([n.query_id for n in frontier.nodes_in_state("QUEUED")], ["q1"])
        self.assertEqual([n.query_id for n in frontier.nodes_in_state("NEW")], ["q2"])

    def test_valid_full_lifecycle_transition(self):
        frontier = SearchFrontier()
        frontier.add(QueryNode("q1", "a", None, 0, "initial"))
        frontier.set_state("q1", "QUEUED")
        frontier.set_state("q1", "SEARCHED")
        frontier.set_state("q1", "EXPAND")
        self.assertEqual(frontier.state("q1"), "EXPAND")

    def test_new_to_rejected_is_allowed(self):
        frontier = SearchFrontier()
        frontier.add(QueryNode("q1", "a", None, 0, "initial"))
        frontier.set_state("q1", "REJECTED")
        self.assertEqual(frontier.state("q1"), "REJECTED")

    def test_new_cannot_jump_directly_to_searched(self):
        frontier = SearchFrontier()
        frontier.add(QueryNode("q1", "a", None, 0, "initial"))
        with self.assertRaisesRegex(ValueError, "invalid_frontier_transition"):
            frontier.set_state("q1", "SEARCHED")

    def test_searched_cannot_go_back_to_queued(self):
        frontier = SearchFrontier()
        frontier.add(QueryNode("q1", "a", None, 0, "initial"))
        frontier.set_state("q1", "QUEUED")
        frontier.set_state("q1", "SEARCHED")
        with self.assertRaisesRegex(ValueError, "invalid_frontier_transition"):
            frontier.set_state("q1", "QUEUED")

    def test_terminal_state_cannot_transition_further(self):
        frontier = SearchFrontier()
        frontier.add(QueryNode("q1", "a", None, 0, "initial"))
        frontier.set_state("q1", "QUEUED")
        frontier.set_state("q1", "SEARCHED")
        frontier.set_state("q1", "EXHAUSTED")
        with self.assertRaises(ValueError):
            frontier.set_state("q1", "EXPAND")


class ProviderPerformanceTrackerTests(unittest.TestCase):
    def test_marginal_yield_computed_from_latest_round(self):
        tracker = ProviderPerformanceTracker()
        tracker.record("p1", 0, new_unique_entities=2, total_results=10)
        self.assertAlmostEqual(tracker.marginal_yield("p1"), 0.2)

    def test_unknown_provider_has_zero_yield(self):
        self.assertEqual(ProviderPerformanceTracker().marginal_yield("nobody"), 0.0)

    def test_yield_uses_most_recent_round_not_average(self):
        tracker = ProviderPerformanceTracker()
        tracker.record("p1", 0, 5, 10)
        tracker.record("p1", 1, 1, 10)
        self.assertAlmostEqual(tracker.marginal_yield("p1"), 0.1)


class SearchBudgetAllocatorTests(unittest.TestCase):
    def test_single_provider_gets_the_whole_budget(self):
        allocation = allocate_budget(ProviderPerformanceTracker(), ["p1"], total_budget=10)
        self.assertEqual(allocation, {"p1": 10})

    def test_three_providers_budget_two_floor_one_never_exceeds_budget(self):
        allocation = allocate_budget(ProviderPerformanceTracker(), ["a", "b", "c"], total_budget=2, min_floor=1)
        self.assertLessEqual(sum(allocation.values()), 2)
        self.assertEqual(sum(allocation.values()), 2)  # every unit is still handed out
        self.assertEqual(set(v for v in allocation.values() if v > 0).union({0}), {0, 1})

    def test_three_providers_budget_ten_sums_to_budget(self):
        allocation = allocate_budget(ProviderPerformanceTracker(), ["a", "b", "c"], total_budget=10, min_floor=1)
        self.assertEqual(sum(allocation.values()), 10)
        self.assertTrue(all(v >= 1 for v in allocation.values()))

    def test_zero_yield_splits_evenly_and_deterministically(self):
        first = allocate_budget(ProviderPerformanceTracker(), ["a", "b", "c"], total_budget=10)
        second = allocate_budget(ProviderPerformanceTracker(), ["a", "b", "c"], total_budget=10)
        self.assertEqual(first, second)

    def test_unequal_yield_gives_more_to_higher_yield_provider(self):
        tracker = ProviderPerformanceTracker()
        tracker.record("p1", 0, 9, 10)
        tracker.record("p2", 0, 1, 10)
        allocation = allocate_budget(tracker, ["p1", "p2"], total_budget=20, min_floor=1)
        self.assertGreater(allocation["p1"], allocation["p2"])
        self.assertEqual(sum(allocation.values()), 20)

    def test_ties_break_deterministically_by_provider_id(self):
        first = allocate_budget(ProviderPerformanceTracker(), ["b", "a"], total_budget=10)
        second = allocate_budget(ProviderPerformanceTracker(), ["a", "b"], total_budget=10)
        self.assertEqual(first, second)

    def test_duplicate_provider_ids_are_deduplicated(self):
        allocation = allocate_budget(ProviderPerformanceTracker(), ["a", "a", "b"], total_budget=10)
        self.assertEqual(set(allocation), {"a", "b"})

    def test_budget_zero_allocates_nothing(self):
        allocation = allocate_budget(ProviderPerformanceTracker(), ["a", "b"], total_budget=0)
        self.assertEqual(allocation, {"a": 0, "b": 0})

    def test_never_exceeds_budget_across_many_combinations(self):
        tracker = ProviderPerformanceTracker()
        tracker.record("a", 0, 3, 10)
        tracker.record("b", 0, 1, 10)
        for providers in (["a"], ["a", "b"], ["a", "b", "c"], ["a", "b", "c", "d", "e"]):
            for budget in (0, 1, 2, 3, 5, 10, 17, 100):
                allocation = allocate_budget(tracker, providers, total_budget=budget, min_floor=1)
                self.assertLessEqual(sum(allocation.values()), budget)


class TemporalStateTests(unittest.TestCase):
    def test_no_publication_date_is_current(self):
        self.assertEqual(classify_temporal_state(UTC_NOW, None), "current")

    def test_recent_publication_is_current(self):
        self.assertEqual(classify_temporal_state(UTC_NOW, RECENT), "current")

    def test_old_publication_is_expired_historical(self):
        self.assertEqual(classify_temporal_state(UTC_NOW, STALE), "expired_historical")

    def test_expired_is_a_label_not_a_rejection(self):
        state = classify_temporal_state(UTC_NOW, "2020-01-01T00:00:00+00:00")
        self.assertIn(state, ("stale", "expired_historical"))

    def test_invalid_retrieved_at_raises(self):
        with self.assertRaises(ValueError):
            classify_temporal_state("not-a-date", None)

    def test_naive_retrieved_at_raises(self):
        with self.assertRaises(ValueError):
            classify_temporal_state("2026-09-04T10:00:00", None)

    def test_naive_publication_date_raises(self):
        with self.assertRaises(ValueError):
            classify_temporal_state(UTC_NOW, "2026-08-20T00:00:00")

    def test_invalid_publication_date_raises(self):
        with self.assertRaises(ValueError):
            classify_temporal_state(UTC_NOW, "not-a-date")

    def test_publication_materially_in_future_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "publication_date_in_future"):
            classify_temporal_state(UTC_NOW, "2026-12-01T00:00:00+00:00")

    def test_publication_within_small_clock_skew_tolerance_is_accepted(self):
        # a few hours "in the future" is tolerated clock skew, not rejected
        self.assertEqual(classify_temporal_state("2026-09-04T00:00:00+00:00", "2026-09-04T06:00:00+00:00"), "current")


class EvidenceGraphTests(unittest.TestCase):
    def test_expand_relationships_detects_subsidiary_keyword(self):
        groups = group_duplicates((result(snippet="Example Co, a subsidiary of Example Holdings, sells widgets."),))
        candidates = resolve_entities(groups)
        links = expand_entity_relationships(candidates[0], {g.group_id: g for g in groups})
        self.assertTrue(any(l.relationship_type == "subsidiary_of" for l in links))

    def test_expand_relationships_detects_alias_keyword(self):
        groups = group_duplicates((result(snippet="Example Co, trading as Example Trading, sells widgets."),))
        candidates = resolve_entities(groups)
        links = expand_entity_relationships(candidates[0], {g.group_id: g for g in groups})
        self.assertTrue(any(l.relationship_type == "alias_of" for l in links))

    def test_no_relationship_keyword_yields_no_links(self):
        groups = group_duplicates((result(snippet="Nothing relevant here."),))
        candidates = resolve_entities(groups)
        links = expand_entity_relationships(candidates[0], {g.group_id: g for g in groups})
        self.assertEqual(links, ())

    def test_evidence_graph_merge_is_deduplicating(self):
        link = EvidenceLink("ent_1", "target", "subsidiary_of", "https://example.invalid/x")
        graph = EvidenceGraph().merge((link, link))
        self.assertEqual(len(graph.links), 1)

    def test_links_from_filters_by_candidate(self):
        a = EvidenceLink("ent_1", "target-a", "subsidiary_of", "https://example.invalid/a")
        b = EvidenceLink("ent_2", "target-b", "subsidiary_of", "https://example.invalid/b")
        graph = EvidenceGraph((a, b))
        self.assertEqual(graph.links_from("ent_1"), (a,))


class CoverageGapLifecycleTests(unittest.TestCase):
    def test_uncovered_geography_becomes_a_gap(self):
        groups = group_duplicates((result(country_hint="OtherPlace"),))
        gaps = detect_coverage_gaps(plan(geography_terms=("Exampleland", "SecondMarket")), groups)
        self.assertTrue(any("SecondMarket" in g.dimension for g in gaps))

    def test_covered_geography_is_not_a_gap(self):
        groups = group_duplicates((result(country_hint="Exampleland"),))
        gaps = detect_coverage_gaps(plan(geography_terms=("Exampleland",)), groups)
        self.assertEqual(gaps, ())

    def test_gap_starts_open(self):
        gap = CoverageGap("gap_1", "geography:X", "no match")
        gap.validate()
        self.assertEqual(gap.state, "OPEN")

    def test_two_failed_attempts_same_pair_stay_open(self):
        gap = CoverageGap("gap_1", "geography:X", "no match")
        gap = gap.record_failed_attempt("family-a", "provider-1")
        gap = gap.record_failed_attempt("family-a", "provider-1")
        self.assertEqual(gap.state, "OPEN")

    def test_same_family_three_different_providers_is_three_distinct_strategies(self):
        gap = CoverageGap("gap_1", "geography:X", "no match")
        gap = gap.record_failed_attempt("family-a", "provider-1")
        gap = gap.record_failed_attempt("family-a", "provider-2")
        gap = gap.record_failed_attempt("family-a", "provider-3")
        self.assertEqual(gap.state, "BLOCKED_UNKNOWN")

    def test_different_family_same_provider_also_counts_as_distinct(self):
        gap = CoverageGap("gap_1", "geography:X", "no match")
        gap = gap.record_failed_attempt("family-a", "provider-1")
        gap = gap.record_failed_attempt("family-b", "provider-1")
        gap = gap.record_failed_attempt("family-c", "provider-1")
        self.assertEqual(gap.state, "BLOCKED_UNKNOWN")

    def test_repeating_the_same_attempt_does_not_count_as_distinct(self):
        gap = CoverageGap("gap_1", "geography:X", "no match")
        gap = gap.record_failed_attempt("family-a", "provider-1")
        gap = gap.record_failed_attempt("family-a", "provider-1")
        gap = gap.record_failed_attempt("family-a", "provider-1")
        self.assertEqual(gap.state, "OPEN")

    def test_resolve_advances_state_and_keeps_history(self):
        gap = CoverageGap("gap_1", "geography:X", "no match")
        gap = gap.record_failed_attempt("family-a", "provider-1")
        resolved = gap.resolve()
        self.assertEqual(resolved.state, "RESOLVED")
        self.assertEqual(resolved.attempted, gap.attempted)

    def test_resolved_gap_ignores_further_failed_attempts(self):
        gap = CoverageGap("gap_1", "geography:X", "no match").resolve()
        gap = gap.record_failed_attempt("family-a", "provider-1")
        self.assertEqual(gap.state, "RESOLVED")

    def test_reconcile_marks_newly_covered_dimension_resolved(self):
        target_plan = plan(geography_terms=("Exampleland", "India"))
        round0_groups = group_duplicates((result(country_hint="Exampleland"),))
        gaps_by_id = reconcile_gap_history({}, target_plan, round0_groups)
        india_gap_id = _gap_id_for("geography:India")
        self.assertEqual(gaps_by_id[india_gap_id].state, "OPEN")

        round1_groups = group_duplicates((
            result(country_hint="Exampleland"),
            result(url="https://example.invalid/india-co", country_hint="India", entity_name_hint="India Co"),
        ))
        gaps_by_id = reconcile_gap_history(gaps_by_id, target_plan, round1_groups)
        self.assertEqual(gaps_by_id[india_gap_id].state, "RESOLVED")

    def test_coverage_ratio_increases_deterministically_after_resolution(self):
        target_plan = plan(geography_terms=("Exampleland", "India"))

        def ratio(gaps_by_id):
            open_or_blocked = sum(1 for g in gaps_by_id.values() if g.state in ("OPEN", "BLOCKED_UNKNOWN"))
            return 1 - (open_or_blocked / len(target_plan.geography_terms))

        round0_groups = group_duplicates((result(country_hint="Exampleland"),))
        gaps_by_id = reconcile_gap_history({}, target_plan, round0_groups)
        ratio_before = ratio(gaps_by_id)

        round1_groups = group_duplicates((
            result(country_hint="Exampleland"),
            result(url="https://example.invalid/india-co", country_hint="India", entity_name_hint="India Co"),
        ))
        gaps_by_id = reconcile_gap_history(gaps_by_id, target_plan, round1_groups)
        ratio_after = ratio(gaps_by_id)

        self.assertGreater(ratio_after, ratio_before)

    def test_gap_history_is_never_deleted_on_resolution(self):
        target_plan = plan(geography_terms=("Exampleland", "India"))
        round0_groups = group_duplicates((result(country_hint="Exampleland"),))
        gaps_by_id = reconcile_gap_history({}, target_plan, round0_groups)
        india_gap_id = _gap_id_for("geography:India")
        self.assertIn(india_gap_id, gaps_by_id)

        round1_groups = group_duplicates((
            result(country_hint="Exampleland"),
            result(url="https://example.invalid/india-co", country_hint="India", entity_name_hint="India Co"),
        ))
        gaps_by_id = reconcile_gap_history(gaps_by_id, target_plan, round1_groups)
        self.assertIn(india_gap_id, gaps_by_id)  # still present, now RESOLVED, never removed


class RecursiveQueryGeneratorTests(unittest.TestCase):
    def test_probable_entity_gets_a_confirmation_query(self):
        groups = group_duplicates((result(entity_name_hint="Example Company A"),))
        candidates = resolve_entities(groups)
        nodes = generate_expansion_queries(candidates, {g.group_id: g for g in groups}, (), (),
                                           search_depth=1, parent_query_id=None)
        self.assertTrue(any("example company a" in n.query_text for n in nodes))

    def test_exact_entity_gets_no_confirmation_query(self):
        groups = group_duplicates((
            result(url="https://example.invalid/1", entity_name_hint="Example Company A"),
            result(url="https://example.invalid/2", entity_name_hint="Example Company A"),
        ))
        candidates = resolve_entities(groups)
        nodes = generate_expansion_queries(candidates, {g.group_id: g for g in groups}, (), (),
                                           search_depth=1, parent_query_id=None)
        self.assertEqual(nodes, ())

    def test_relationship_link_produces_a_follow_up_query(self):
        link = EvidenceLink("ent_1", "parentco international", "subsidiary_of", "https://example.invalid/x")
        nodes = generate_expansion_queries((), {}, (), (link,), search_depth=1, parent_query_id=None)
        self.assertTrue(any(n.query_text == "parentco international" for n in nodes))

    def test_blocked_gap_is_not_re_queried(self):
        gap = CoverageGap("gap_1", "geography:X", "no match", state="BLOCKED_UNKNOWN")
        nodes = generate_expansion_queries((), {}, (gap,), (), search_depth=1, parent_query_id=None)
        self.assertEqual(nodes, ())

    def test_resolved_gap_is_not_re_queried(self):
        gap = CoverageGap("gap_1", "geography:X", "no match").resolve()
        nodes = generate_expansion_queries((), {}, (gap,), (), search_depth=1, parent_query_id=None)
        self.assertEqual(nodes, ())

    def test_open_gap_produces_an_alternate_query(self):
        gap = CoverageGap("gap_1", "geography:X", "no match")
        nodes = generate_expansion_queries((), {}, (gap,), (), search_depth=1, parent_query_id=None)
        self.assertTrue(len(nodes) >= 1)


class StopConditionTests(unittest.TestCase):
    def test_budget_exhausted_wins(self):
        decision = evaluate_stop_conditions(round_index=0, new_unique_entities_this_round=5,
                                            total_unique_entities=5, coverage_ratio=0.0, coverage_target=1.0,
                                            verified_ratio=0.0, verification_target=1.0, queries_executed=100,
                                            query_budget=100)
        self.assertEqual(decision.reason, "budget_exhausted")

    def test_coverage_target_reached(self):
        decision = evaluate_stop_conditions(round_index=0, new_unique_entities_this_round=5,
                                            total_unique_entities=5, coverage_ratio=0.9, coverage_target=0.8,
                                            verified_ratio=0.0, verification_target=1.0, queries_executed=1,
                                            query_budget=100)
        self.assertEqual(decision.reason, "coverage_target_reached")

    def test_no_new_evidence_stops_after_round_zero(self):
        decision = evaluate_stop_conditions(round_index=1, new_unique_entities_this_round=0,
                                            total_unique_entities=10, coverage_ratio=0.0, coverage_target=1.0,
                                            verified_ratio=0.0, verification_target=1.0, queries_executed=1,
                                            query_budget=100)
        self.assertEqual(decision.reason, "no_new_evidence_from_repeated_queries")

    def test_first_round_never_stops_on_no_new_evidence(self):
        decision = evaluate_stop_conditions(round_index=0, new_unique_entities_this_round=0,
                                            total_unique_entities=0, coverage_ratio=0.0, coverage_target=1.0,
                                            verified_ratio=0.0, verification_target=1.0, queries_executed=1,
                                            query_budget=100)
        self.assertFalse(decision.should_stop)

    def test_marginal_yield_below_threshold(self):
        decision = evaluate_stop_conditions(round_index=1, new_unique_entities_this_round=1,
                                            total_unique_entities=1000, coverage_ratio=0.0, coverage_target=1.0,
                                            verified_ratio=0.0, verification_target=1.0, queries_executed=1,
                                            query_budget=100, marginal_yield_threshold=0.02)
        self.assertEqual(decision.reason, "marginal_yield_below_threshold")

    def test_invalid_stop_reason_rejected(self):
        with self.assertRaises(ValueError):
            StopDecision(True, "not_a_real_reason").validate()


def _make_synthetic_provider(provider_id: str):
    def provider_fn(query_text: str, limit: int) -> tuple[NormalizedDiscoveryResult, ...]:
        text_lower = query_text.lower()
        if "parentco international" in text_lower:
            return (NormalizedDiscoveryResult(
                provider=provider_id, query=query_text, url="https://example.invalid/parentco",
                title="ParentCo International", snippet="ParentCo International is a global trading group.",
                retrieved_at=UTC_NOW, published_at=UTC_NOW, project_id="PRJ-EXAMPLE-01", lane_id="LANE-A",
                entity_name_hint="ParentCo International", country_hint="Exampleland", buyer_type_hint=None,
            ),)
        seed = int(sha256(f"{provider_id}:{query_text}".encode()).hexdigest(), 16)
        count = min(limit, 3 + seed % 3)
        results = []
        for i in range(count):
            idx = (seed + i) % 50
            entity = f"Example Entity {idx}"
            snippet = f"{entity} listed for {query_text}."
            if idx == 7:
                snippet = f"{entity}, a subsidiary of ParentCo International, is active in {query_text}."
            results.append(NormalizedDiscoveryResult(
                provider=provider_id, query=query_text, url=f"https://example.invalid/entity-{idx}",
                title=entity, snippet=snippet, retrieved_at=UTC_NOW, published_at=UTC_NOW,
                project_id="PRJ-EXAMPLE-01", lane_id="LANE-A", entity_name_hint=entity,
                country_hint="Exampleland", buyer_type_hint=None,
            ))
        return tuple(results)
    return provider_fn


def _empty_provider(query_text: str, limit: int) -> tuple[NormalizedDiscoveryResult, ...]:
    return ()


def _big_plan() -> QueryExpansionPlan:
    return plan(
        product_terms=tuple(f"product-{i}" for i in range(70)),
        buyer_terms=("distributor", "trader"), procurement_terms=("tender",),
        industry_terms=("manufacturing",), geography_terms=("Exampleland",), language_terms=("en",),
    )


class ScopeIsolationTests(unittest.TestCase):
    def _bad_provider(self, *, bad_project=None, bad_lane=None, missing_project=False, missing_lane=False):
        def provider_fn(query_text, limit):
            pid = None if missing_project else (bad_project or "PRJ-EXAMPLE-01")
            lid = None if missing_lane else (bad_lane or "LANE-A")
            return (NormalizedDiscoveryResult(
                provider="bad-provider", query=query_text, url="https://example.invalid/bad",
                title="Bad Co", snippet="Bad Co listing.", retrieved_at=UTC_NOW, published_at=UTC_NOW,
                project_id=pid, lane_id=lid, entity_name_hint="Bad Co", country_hint="Exampleland",
                buyer_type_hint=None,
            ),)
        return provider_fn

    def test_wrong_project_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "scope_mismatch"):
            run_recursive_search(plan(), {"bad": self._bad_provider(bad_project="PRJ-WRONG")},
                                 run_id="run-bad-1", max_depth=1, query_budget=10)

    def test_wrong_lane_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "scope_mismatch"):
            run_recursive_search(plan(), {"bad": self._bad_provider(bad_lane="LANE-WRONG")},
                                 run_id="run-bad-2", max_depth=1, query_budget=10)

    def test_missing_project_id_rejected_when_plan_has_project(self):
        with self.assertRaisesRegex(ValueError, "scope_mismatch"):
            run_recursive_search(plan(), {"bad": self._bad_provider(missing_project=True)},
                                 run_id="run-bad-3", max_depth=1, query_budget=10)

    def test_missing_lane_id_rejected_when_plan_has_lane(self):
        with self.assertRaisesRegex(ValueError, "scope_mismatch"):
            run_recursive_search(plan(), {"bad": self._bad_provider(missing_lane=True)},
                                 run_id="run-bad-4", max_depth=1, query_budget=10)

    def test_correct_arbitrary_scope_is_preserved_across_all_rounds(self):
        custom_plan = plan(project_id="anything-goes-123", lane_id="totally-made-up-lane",
                           geography_terms=("Exampleland",))
        provider_id = "synthetic-a"

        def provider_fn(query_text, limit):
            url_suffix = sha256(query_text.encode()).hexdigest()[:12]
            return (NormalizedDiscoveryResult(
                provider=provider_id, query=query_text, url=f"https://example.invalid/{url_suffix}",
                title="Some Co", snippet="Some Co listing, a subsidiary of Another Co.", retrieved_at=UTC_NOW,
                published_at=UTC_NOW, project_id="anything-goes-123", lane_id="totally-made-up-lane",
                entity_name_hint="Some Co", country_hint="Exampleland", buyer_type_hint=None,
            ),)

        outcome = run_recursive_search(custom_plan, {provider_id: provider_fn}, run_id="run-scope-ok",
                                       max_depth=2, query_budget=50, coverage_target=2.0, verification_target=2.0)
        self.assertGreater(len(outcome.all_results), 0)
        for r in outcome.all_results:
            self.assertEqual(r.project_id, "anything-goes-123")
            self.assertEqual(r.lane_id, "totally-made-up-lane")


class RecursiveSearchAcceptanceTests(unittest.TestCase):
    def test_generates_at_least_200_query_variants(self):
        lattice = build_query_lattice(_big_plan(), max_queries=1000)
        self.assertGreaterEqual(len(lattice.root_nodes), 200)

    def test_processes_at_least_1000_synthetic_results_and_recursion_adds_new_entities(self):
        provider_fns = {"synthetic-a": _make_synthetic_provider("synthetic-a"),
                        "synthetic-b": _make_synthetic_provider("synthetic-b")}
        outcome = run_recursive_search(
            _big_plan(), provider_fns, run_id="run-acceptance-1", max_depth=2,
            query_budget=1500, results_per_query=10, coverage_target=2.0, verification_target=2.0,
        )

        self.assertGreaterEqual(len(outcome.all_results), 1000)
        self.assertGreaterEqual(len(outcome.rounds), 2)

        baseline_names = {e.normalized_name for e in outcome.rounds[0].entities}
        final_names = {e.normalized_name for e in outcome.entities_by_id.values()}
        self.assertNotIn("parentco international", baseline_names)
        self.assertIn("parentco international", final_names)

        for r in outcome.all_results:
            self.assertEqual(r.project_id, "PRJ-EXAMPLE-01")
            self.assertEqual(r.lane_id, "LANE-A")
            self.assertEqual(r.evidence_class.value, "CLAIM")
            self.assertEqual(r.verification_state, "unverified")

    def test_recursive_search_is_deterministic(self):
        provider_fns = {"synthetic-a": _make_synthetic_provider("synthetic-a"),
                        "synthetic-b": _make_synthetic_provider("synthetic-b")}
        first = run_recursive_search(_big_plan(), provider_fns, run_id="run-a", max_depth=2,
                                     query_budget=600, coverage_target=2.0, verification_target=2.0)
        second = run_recursive_search(_big_plan(), provider_fns, run_id="run-a", max_depth=2,
                                      query_budget=600, coverage_target=2.0, verification_target=2.0)
        self.assertEqual(len(first.all_results), len(second.all_results))
        self.assertEqual(set(first.entities_by_id), set(second.entities_by_id))

    def test_no_result_ever_leaves_its_declared_scope(self):
        provider_fns = {"synthetic-a": _make_synthetic_provider("synthetic-a")}
        outcome = run_recursive_search(_big_plan(), provider_fns, run_id="run-scope", max_depth=2,
                                       query_budget=400, coverage_target=2.0, verification_target=2.0)
        scopes = {(r.project_id, r.lane_id) for r in outcome.all_results}
        self.assertEqual(scopes, {("PRJ-EXAMPLE-01", "LANE-A")})

    def test_stop_reason_is_one_of_the_measurable_reasons(self):
        provider_fns = {"synthetic-a": _make_synthetic_provider("synthetic-a")}
        outcome = run_recursive_search(_big_plan(), provider_fns, run_id="run-stop", max_depth=2,
                                       query_budget=400, coverage_target=2.0, verification_target=2.0)
        self.assertIn(outcome.stop_reason, (
            "marginal_yield_below_threshold", "coverage_target_reached", "verification_target_reached",
            "budget_exhausted", "no_new_evidence_from_repeated_queries", "max_depth_reached",
        ))

    def test_query_budget_is_never_exceeded(self):
        provider_fns = {"synthetic-a": _make_synthetic_provider("synthetic-a"),
                        "synthetic-b": _make_synthetic_provider("synthetic-b")}
        outcome = run_recursive_search(_big_plan(), provider_fns, run_id="run-budget", max_depth=3,
                                       query_budget=300, coverage_target=2.0, verification_target=2.0)
        total_executed = sum(len(r.executed_query_ids) for r in outcome.rounds)
        self.assertLessEqual(total_executed, 300)


class PerformanceRoutingTests(unittest.TestCase):
    def test_round_zero_allocation_is_fair_with_empty_tracker(self):
        provider_fns = {"a": _make_synthetic_provider("a"), "b": _make_synthetic_provider("b")}
        outcome = run_recursive_search(_big_plan(), provider_fns, run_id="run-fair", max_depth=1,
                                       query_budget=300, coverage_target=2.0, verification_target=2.0)
        allocation = outcome.rounds[0].provider_allocation
        self.assertLessEqual(abs(allocation["a"] - allocation["b"]), 1)

    def test_later_round_routes_more_budget_to_higher_yield_provider(self):
        provider_fns = {"high-yield": _make_synthetic_provider("high-yield"), "no-yield": _empty_provider}
        outcome = run_recursive_search(_big_plan(), provider_fns, run_id="run-routed", max_depth=2,
                                       query_budget=600, coverage_target=2.0, verification_target=2.0)
        self.assertGreaterEqual(len(outcome.rounds), 2)
        round1_allocation = outcome.rounds[1].provider_allocation
        self.assertEqual(round1_allocation["no-yield"], 1)  # only the floor
        self.assertGreater(round1_allocation["high-yield"], round1_allocation["no-yield"])

    def test_provider_ids_are_preserved_in_provenance(self):
        provider_fns = {"named-provider-x": _make_synthetic_provider("named-provider-x")}
        outcome = run_recursive_search(_big_plan(), provider_fns, run_id="run-provenance", max_depth=1,
                                       query_budget=50, coverage_target=2.0, verification_target=2.0)
        self.assertTrue(all(r.provider == "named-provider-x" for r in outcome.all_results))

    def test_anti_spin_tracking_uses_real_provider_ids_not_a_placeholder(self):
        target_plan = plan(geography_terms=("Exampleland", "NeverFoundLand"))
        provider_fns = {"real-provider-1": _make_synthetic_provider("real-provider-1")}
        outcome = run_recursive_search(target_plan, provider_fns, run_id="run-attrib", max_depth=3,
                                       query_budget=300, coverage_target=2.0, verification_target=2.0)
        for gap in outcome.coverage_gaps:
            for _, provider_id in gap.attempted:
                self.assertIn(provider_id, provider_fns)
                self.assertNotEqual(provider_id, "synthetic")


class RealDataReadinessTests(unittest.TestCase):
    """A provider-neutral fixture shaped like noisy external commercial data: duplicate
    aliases, a logistics intermediary, a steel mill, a procurement authority, a country-level
    market row, a relationship hint, and expired historical tender evidence.
    """

    def _fixture_plan(self) -> QueryExpansionPlan:
        return plan(product_terms=("widget", "gadget", "component"), geography_terms=("Exampleland",))

    def _fixture_provider(self, provider_id: str = "readiness"):
        pool = (
            NormalizedDiscoveryResult(
                provider=provider_id, query="q", url="https://example.invalid/acme-1",
                title="Acme Steel Mills", snippet="Acme Steel Mills issued a tender for widget procurement.",
                retrieved_at=UTC_NOW, published_at=RECENT, project_id="PRJ-EXAMPLE-01", lane_id="LANE-A",
                entity_name_hint="Acme Steel Mills", country_hint="Exampleland", buyer_type_hint=None),
            NormalizedDiscoveryResult(
                provider=provider_id, query="q", url="https://example.invalid/acme-2",
                title="Acme Steel Mills (second listing)",
                snippet="Acme Steel Mills, a subsidiary of Global Metals Holding, operates a steel mill.",
                retrieved_at=UTC_NOW, published_at=RECENT, project_id="PRJ-EXAMPLE-01", lane_id="LANE-A",
                entity_name_hint="Acme Steel Mills", country_hint="Exampleland", buyer_type_hint=None),
            NormalizedDiscoveryResult(
                provider=provider_id, query="q", url="https://example.invalid/bsm-forwarding",
                title="Bsm Forwarding", snippet="Bsm Forwarding handled a high volume of shipment logistics.",
                retrieved_at=UTC_NOW, published_at=RECENT, project_id="PRJ-EXAMPLE-01", lane_id="LANE-A",
                entity_name_hint="Bsm Forwarding", country_hint="Exampleland", buyer_type_hint=None),
            NormalizedDiscoveryResult(
                provider=provider_id, query="q", url="https://example.invalid/procurement-authority",
                title="National Procurement Authority",
                snippet="National Procurement Authority issued a tender board notice.",
                retrieved_at=UTC_NOW, published_at=RECENT, project_id="PRJ-EXAMPLE-01", lane_id="LANE-A",
                entity_name_hint="National Procurement Authority", country_hint="Exampleland",
                buyer_type_hint=None),
            NormalizedDiscoveryResult(
                provider=provider_id, query="q", url="https://example.invalid/italy-market",
                title="Italy Market Signal", snippet="Italy shows rising demand this quarter, per trade bulletin.",
                retrieved_at=UTC_NOW, published_at=RECENT, project_id="PRJ-EXAMPLE-01", lane_id="LANE-A",
                entity_name_hint=None, country_hint="Italy", buyer_type_hint=None),
            NormalizedDiscoveryResult(
                provider=provider_id, query="q", url="https://example.invalid/expired-tender",
                title="Historic Tender Notice", snippet="A widget tender was issued in a prior cycle.",
                retrieved_at=UTC_NOW, published_at=OLD_DATE, project_id="PRJ-EXAMPLE-01", lane_id="LANE-A",
                entity_name_hint="Historic Buyer Co", country_hint="Exampleland", buyer_type_hint=None),
        )

        def provider_fn(query_text: str, limit: int) -> tuple[NormalizedDiscoveryResult, ...]:
            text_lower = query_text.lower()
            if "global metals holding" in text_lower:
                return (NormalizedDiscoveryResult(
                    provider=provider_id, query=query_text, url="https://example.invalid/global-metals",
                    title="Global Metals Holding", snippet="Global Metals Holding is a diversified metals group.",
                    retrieved_at=UTC_NOW, published_at=RECENT, project_id="PRJ-EXAMPLE-01", lane_id="LANE-A",
                    entity_name_hint="Global Metals Holding", country_hint="Exampleland", buyer_type_hint=None,
                ),)
            seed = int(sha256(f"{provider_id}:{query_text}".encode()).hexdigest(), 16)
            count = min(limit, 2 + seed % 3)
            chosen = [pool[(seed + i) % len(pool)] for i in range(count)]
            return tuple(NormalizedDiscoveryResult(**{**vars(item), "query": query_text}) for item in chosen)

        return provider_fn

    def _run(self, **overrides):
        params = dict(run_id="run-readiness", max_depth=2, query_budget=400, coverage_target=2.0,
                     verification_target=2.0)
        params.update(overrides)
        return run_recursive_search(self._fixture_plan(), {"readiness": self._fixture_provider()}, **params)

    def test_no_scope_contamination(self):
        outcome = self._run()
        scopes = {(r.project_id, r.lane_id) for r in outcome.all_results}
        self.assertEqual(scopes, {("PRJ-EXAMPLE-01", "LANE-A")})

    def test_market_row_never_becomes_a_company_buyer(self):
        outcome = self._run()
        market_entities = [e for e in outcome.entities_by_id.values() if e.resolution_state == "unresolved"]
        self.assertTrue(market_entities)
        for entity in market_entities:
            classification = outcome.classifications_by_id.get(entity.candidate_id)
            if classification is not None:
                self.assertFalse(classification.is_buyer_opportunity)

    def test_forwarder_stays_non_buyer_despite_high_volume_signal(self):
        outcome = self._run()
        forwarder = next(e for e in outcome.entities_by_id.values() if e.normalized_name == "bsm forwarding")
        classification = outcome.classifications_by_id[forwarder.candidate_id]
        self.assertEqual(classification.category, "logistics_intermediary")
        self.assertFalse(classification.is_buyer_opportunity)

    def test_steel_mill_is_classified_as_a_buyer(self):
        outcome = self._run()
        acme = next(e for e in outcome.entities_by_id.values() if e.normalized_name == "acme steel mills")
        classification = outcome.classifications_by_id[acme.candidate_id]
        self.assertEqual(classification.category, "steel_mill")
        self.assertTrue(classification.is_buyer_opportunity)

    def test_procurement_authority_is_distinct_from_steel_mill(self):
        outcome = self._run()
        authority = next(e for e in outcome.entities_by_id.values()
                         if e.normalized_name == "national procurement authority")
        classification = outcome.classifications_by_id[authority.candidate_id]
        self.assertEqual(classification.category, "procurement_authority")
        self.assertNotEqual(classification.category, "steel_mill")

    def test_expired_historical_tender_evidence_is_retained_not_discarded(self):
        outcome = self._run()
        expired_urls = [r.url for r in outcome.all_results if r.url == "https://example.invalid/expired-tender"]
        self.assertTrue(expired_urls)  # still present in cumulative results
        matching = next(r for r in outcome.all_results if r.url == "https://example.invalid/expired-tender")
        self.assertEqual(classify_temporal_state(matching.retrieved_at, matching.published_at), "expired_historical")

    def test_recursive_query_adds_new_evidence_via_relationship_hint(self):
        outcome = self._run()
        baseline_names = {e.normalized_name for e in outcome.rounds[0].entities}
        final_names = {e.normalized_name for e in outcome.entities_by_id.values()}
        self.assertNotIn("global metals holding", baseline_names)
        self.assertIn("global metals holding", final_names)

    def test_budget_never_exceeded_on_realistic_fixture(self):
        outcome = self._run(query_budget=150)
        total_executed = sum(len(r.executed_query_ids) for r in outcome.rounds)
        self.assertLessEqual(total_executed, 150)

    def test_malformed_cross_project_row_fails_the_whole_run_closed(self):
        def bad_provider(query_text, limit):
            return (NormalizedDiscoveryResult(
                provider="readiness-bad", query=query_text, url="https://example.invalid/cross-project",
                title="Cross Project Co", snippet="Cross Project Co listing.", retrieved_at=UTC_NOW,
                published_at=RECENT, project_id="PRJ-OTHER-99", lane_id="LANE-A",
                entity_name_hint="Cross Project Co", country_hint="Exampleland", buyer_type_hint=None,
            ),)
        with self.assertRaisesRegex(ValueError, "scope_mismatch"):
            run_recursive_search(self._fixture_plan(), {"readiness-bad": bad_provider}, run_id="run-readiness-bad",
                                 max_depth=1, query_budget=10)


if __name__ == "__main__":
    unittest.main()
