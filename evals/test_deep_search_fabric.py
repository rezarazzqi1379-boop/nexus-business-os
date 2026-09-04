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
    allocate_budget,
    build_query_lattice,
    classify_temporal_state,
    detect_coverage_gaps,
    evaluate_stop_conditions,
    expand_entity_relationships,
    generate_expansion_queries,
    make_query_id,
    query_family,
    run_recursive_search,
)
from discovery_pipeline import NormalizedDiscoveryResult, QueryExpansionPlan, group_duplicates, resolve_entities

UTC_NOW = "2026-09-04T10:00:00+00:00"
RECENT = "2026-08-20T00:00:00+00:00"
STALE = "2023-01-01T00:00:00+00:00"


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
        node = QueryNode("q1", "text", None, 0, "initial")
        frontier.add(node)
        self.assertEqual(frontier.state("q1"), "NEW")

    def test_rejects_invalid_state(self):
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
        frontier.set_state("q1", "SEARCHED")
        self.assertEqual([n.query_id for n in frontier.nodes_in_state("SEARCHED")], ["q1"])
        self.assertEqual([n.query_id for n in frontier.nodes_in_state("NEW")], ["q2"])


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
    def test_every_provider_gets_at_least_the_floor(self):
        tracker = ProviderPerformanceTracker()
        allocation = allocate_budget(tracker, ["p1", "p2"], total_budget=10, min_floor=2)
        self.assertGreaterEqual(allocation["p1"], 2)
        self.assertGreaterEqual(allocation["p2"], 2)

    def test_allocation_sums_to_budget_or_less(self):
        tracker = ProviderPerformanceTracker()
        tracker.record("p1", 0, 8, 10)
        tracker.record("p2", 0, 1, 10)
        allocation = allocate_budget(tracker, ["p1", "p2"], total_budget=20, min_floor=1)
        self.assertLessEqual(sum(allocation.values()), 20)

    def test_higher_yield_provider_gets_more_budget(self):
        tracker = ProviderPerformanceTracker()
        tracker.record("p1", 0, 9, 10)
        tracker.record("p2", 0, 1, 10)
        allocation = allocate_budget(tracker, ["p1", "p2"], total_budget=20, min_floor=1)
        self.assertGreater(allocation["p1"], allocation["p2"])

    def test_deterministic_tie_break_by_provider_id(self):
        tracker = ProviderPerformanceTracker()
        first = allocate_budget(tracker, ["b", "a"], total_budget=10)
        second = allocate_budget(tracker, ["a", "b"], total_budget=10)
        self.assertEqual(first, second)


class TemporalStateTests(unittest.TestCase):
    def test_no_publication_date_is_current(self):
        self.assertEqual(classify_temporal_state(UTC_NOW, None), "current")

    def test_recent_publication_is_current(self):
        self.assertEqual(classify_temporal_state(UTC_NOW, RECENT), "current")

    def test_old_publication_is_expired_historical(self):
        self.assertEqual(classify_temporal_state(UTC_NOW, STALE), "expired_historical")

    def test_expired_is_a_label_not_a_rejection(self):
        # classify_temporal_state never raises for old evidence -- it's retained, just labeled
        state = classify_temporal_state(UTC_NOW, "2020-01-01T00:00:00+00:00")
        self.assertIn(state, ("stale", "expired_historical"))


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


class CoverageGapTests(unittest.TestCase):
    def test_uncovered_geography_becomes_a_gap(self):
        groups = group_duplicates((result(country_hint="OtherPlace"),))
        gaps = detect_coverage_gaps(plan(geography_terms=("Exampleland", "SecondMarket")), groups)
        self.assertTrue(any("SecondMarket" in g.dimension for g in gaps))
        self.assertTrue(any("Exampleland" in g.dimension for g in gaps))  # OtherPlace != Exampleland either

    def test_covered_geography_is_not_a_gap(self):
        groups = group_duplicates((result(country_hint="Exampleland"),))
        gaps = detect_coverage_gaps(plan(geography_terms=("Exampleland",)), groups)
        self.assertEqual(gaps, ())

    def test_gap_starts_open(self):
        gap = CoverageGap("gap_1", "geography:X", "no match")
        gap.validate()
        self.assertEqual(gap.state, "OPEN")

    def test_two_failed_attempts_stay_open(self):
        gap = CoverageGap("gap_1", "geography:X", "no match")
        gap = gap.record_failed_attempt("family-a", "provider-1")
        gap = gap.record_failed_attempt("family-b", "provider-2")
        self.assertEqual(gap.state, "OPEN")

    def test_three_distinct_failed_attempts_become_blocked(self):
        gap = CoverageGap("gap_1", "geography:X", "no match")
        gap = gap.record_failed_attempt("family-a", "provider-1")
        gap = gap.record_failed_attempt("family-b", "provider-2")
        gap = gap.record_failed_attempt("family-c", "provider-3")
        self.assertEqual(gap.state, "BLOCKED_UNKNOWN")

    def test_repeating_the_same_attempt_does_not_count_as_distinct(self):
        gap = CoverageGap("gap_1", "geography:X", "no match")
        gap = gap.record_failed_attempt("family-a", "provider-1")
        gap = gap.record_failed_attempt("family-a", "provider-1")
        gap = gap.record_failed_attempt("family-a", "provider-1")
        self.assertEqual(gap.state, "OPEN")


class RecursiveQueryGeneratorTests(unittest.TestCase):
    def test_probable_entity_gets_a_confirmation_query(self):
        groups = group_duplicates((result(entity_name_hint="Example Company A"),))
        candidates = resolve_entities(groups)
        nodes = generate_expansion_queries(candidates, {g.group_id: g for g in groups}, (), (),
                                           search_depth=1, parent_query_id=None)
        self.assertTrue(any("example company a" in n.query_text for n in nodes))
        self.assertTrue(all(n.search_depth == 1 for n in nodes))

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
        self.assertTrue(decision.should_stop)
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


def _synthetic_provider(query_text: str, limit: int) -> tuple[NormalizedDiscoveryResult, ...]:
    text_lower = query_text.lower()
    if "parentco international" in text_lower:
        return (NormalizedDiscoveryResult(
            provider="synthetic-a", query=query_text, url="https://example.invalid/parentco",
            title="ParentCo International", snippet="ParentCo International is a global trading group.",
            retrieved_at=UTC_NOW, published_at=UTC_NOW, project_id="PRJ-EXAMPLE-01", lane_id="LANE-A",
            entity_name_hint="ParentCo International", country_hint="Exampleland", buyer_type_hint=None,
        ),)
    seed = int(sha256(query_text.encode()).hexdigest(), 16)
    count = min(limit, 3 + seed % 3)
    results = []
    for i in range(count):
        idx = (seed + i) % 50
        entity = f"Example Entity {idx}"
        snippet = f"{entity} listed for {query_text}."
        if idx == 7:
            snippet = f"{entity}, a subsidiary of ParentCo International, is active in {query_text}."
        results.append(NormalizedDiscoveryResult(
            provider="synthetic-a" if i % 2 == 0 else "synthetic-b", query=query_text,
            url=f"https://example.invalid/entity-{idx}", title=entity, snippet=snippet, retrieved_at=UTC_NOW,
            published_at=UTC_NOW, project_id="PRJ-EXAMPLE-01", lane_id="LANE-A", entity_name_hint=entity,
            country_hint="Exampleland", buyer_type_hint=None,
        ))
    return tuple(results)


class RecursiveSearchAcceptanceTests(unittest.TestCase):
    def _big_plan(self) -> QueryExpansionPlan:
        return plan(
            product_terms=tuple(f"product-{i}" for i in range(70)),
            buyer_terms=("distributor", "trader"), procurement_terms=("tender",),
            industry_terms=("manufacturing",), geography_terms=("Exampleland",), language_terms=("en",),
        )

    def test_generates_at_least_200_query_variants(self):
        lattice = build_query_lattice(self._big_plan(), max_queries=1000)
        self.assertGreaterEqual(len(lattice.root_nodes), 200)

    def test_processes_at_least_1000_synthetic_results_and_recursion_adds_new_entities(self):
        outcome = run_recursive_search(
            self._big_plan(), _synthetic_provider, run_id="run-acceptance-1", max_depth=2,
            query_budget=1500, results_per_query=10, coverage_target=2.0, verification_target=2.0,
        )

        self.assertGreaterEqual(len(outcome.all_results), 1000)
        self.assertGreaterEqual(len(outcome.rounds), 2)

        baseline_names = {e.normalized_name for e in outcome.rounds[0].entities}
        final_names = {e.normalized_name for e in outcome.entities_by_id.values()}
        self.assertNotIn("parentco international", baseline_names)
        self.assertIn("parentco international", final_names)
        self.assertTrue(final_names.issuperset(baseline_names) or len(final_names) > len(baseline_names))

        # every discovery kept project/lane scope and CLAIM/unverified status throughout
        for r in outcome.all_results:
            self.assertEqual(r.project_id, "PRJ-EXAMPLE-01")
            self.assertEqual(r.lane_id, "LANE-A")
            self.assertEqual(r.evidence_class.value, "CLAIM")
            self.assertEqual(r.verification_state, "unverified")

    def test_recursive_search_is_deterministic(self):
        first = run_recursive_search(self._big_plan(), _synthetic_provider, run_id="run-a", max_depth=2,
                                     query_budget=600, coverage_target=2.0, verification_target=2.0)
        second = run_recursive_search(self._big_plan(), _synthetic_provider, run_id="run-a", max_depth=2,
                                      query_budget=600, coverage_target=2.0, verification_target=2.0)
        self.assertEqual(len(first.all_results), len(second.all_results))
        self.assertEqual(set(first.entities_by_id), set(second.entities_by_id))

    def test_no_result_ever_leaves_its_declared_scope(self):
        outcome = run_recursive_search(self._big_plan(), _synthetic_provider, run_id="run-scope", max_depth=2,
                                       query_budget=400, coverage_target=2.0, verification_target=2.0)
        scopes = {(r.project_id, r.lane_id) for r in outcome.all_results}
        self.assertEqual(scopes, {("PRJ-EXAMPLE-01", "LANE-A")})

    def test_stop_reason_is_one_of_the_measurable_reasons(self):
        outcome = run_recursive_search(self._big_plan(), _synthetic_provider, run_id="run-stop", max_depth=2,
                                       query_budget=400, coverage_target=2.0, verification_target=2.0)
        self.assertIn(outcome.stop_reason, (
            "marginal_yield_below_threshold", "coverage_target_reached", "verification_target_reached",
            "budget_exhausted", "no_new_evidence_from_repeated_queries", "max_depth_reached",
        ))


if __name__ == "__main__":
    unittest.main()
