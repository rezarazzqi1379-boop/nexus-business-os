from __future__ import annotations

import unittest

from contracts import EvidenceClass
from discovery_pipeline import (
    DEFAULT_DISCOVERY_SCORE_WEIGHTS,
    DiscoveryScoreWeights,
    NormalizedDiscoveryResult,
    NullDiscoveryAdapter,
    QueryExpansionPlan,
    build_verification_queue,
    classify_buyer,
    dedup_rate,
    default_discovery_adapters,
    group_duplicates,
    normalize_entity_name,
    resolve_entities,
    score_entity,
    source_diversity,
)

UTC_NOW = "2026-09-04T10:00:00+00:00"
RECENT = "2026-08-20T00:00:00+00:00"
STALE = "2024-01-01T00:00:00+00:00"


def plan(**changes) -> QueryExpansionPlan:
    values = dict(
        objective="Find plausible buyers for an example product.",
        product_terms=("widget", "gadget"),
        buyer_role_terms=("distributor",),
        procurement_terms=("tender",),
        industry_terms=("manufacturing",),
        geography_terms=("Exampleland",),
        language_variants=("en", "fr"),
        query_set_version="qsv-v0.1",
    )
    values.update(changes)
    return QueryExpansionPlan(**values)


def result(**changes) -> NormalizedDiscoveryResult:
    values = dict(
        provider="null-discovery-adapter",
        url="https://example.invalid/company-a",
        title="Example Company A steel mill",
        snippet="A tender for widget procurement was issued by Example Company A.",
        retrieved_at=UTC_NOW,
        published_at=RECENT,
        project_id="PRJ-EXAMPLE-01",
        lane_id="LANE-A",
        raw_query="widget distributor Exampleland",
        entity_hint="Example Company A",
    )
    values.update(changes)
    return NormalizedDiscoveryResult(**values)


class QueryExpansionPlanTests(unittest.TestCase):
    def test_valid_plan_passes(self):
        plan().validate()

    def test_rejects_empty_product_terms(self):
        with self.assertRaises(ValueError):
            plan(product_terms=()).validate()

    def test_rejects_duplicate_terms(self):
        with self.assertRaises(ValueError):
            plan(product_terms=("widget", "widget")).validate()

    def test_expand_is_deterministic(self):
        self.assertEqual(plan().expand(), plan().expand())

    def test_expand_has_no_duplicate_queries(self):
        queries = plan().expand()
        self.assertEqual(len(queries), len(set(queries)))

    def test_expand_respects_max_queries(self):
        big_plan = plan(product_terms=tuple(f"product-{i}" for i in range(50)))
        self.assertLessEqual(len(big_plan.expand(max_queries=10)), 10)

    def test_non_english_variant_is_tagged(self):
        queries = plan(language_variants=("fr",)).expand()
        self.assertTrue(all("[fr]" in q for q in queries))


class NullDiscoveryAdapterTests(unittest.TestCase):
    def test_always_returns_empty(self):
        self.assertEqual(NullDiscoveryAdapter().discover("q", limit=10), ())

    def test_default_registry_is_fresh_each_call(self):
        first, second = default_discovery_adapters(), default_discovery_adapters()
        self.assertIsNot(first, second)


class NormalizedDiscoveryResultTests(unittest.TestCase):
    def test_valid_result_passes(self):
        result().validate()

    def test_rejects_non_http_url(self):
        with self.assertRaises(ValueError):
            result(url="ftp://example.invalid/x").validate()

    def test_rejects_empty_title(self):
        with self.assertRaises(ValueError):
            result(title="  ").validate()

    def test_evidence_class_is_locked_to_claim(self):
        with self.assertRaisesRegex(ValueError, "normalized_discovery_result_must_be_claim"):
            result(evidence_class=EvidenceClass.FACT).validate()

    def test_verification_state_is_locked_to_unverified(self):
        with self.assertRaisesRegex(ValueError, "normalized_discovery_result_must_be_unverified"):
            result(verification_state="verified").validate()

    def test_project_and_lane_ids_pass_through_unchanged(self):
        r = result(project_id="anything-goes", lane_id="totally-made-up-lane")
        r.validate()
        self.assertEqual(r.lane_id, "totally-made-up-lane")

    def test_to_research_run_record_never_upgrades_evidence(self):
        record = result().to_research_run_record(run_id="run-001", query_set_version="qsv-v0.1")
        self.assertEqual(record.evidence_class, EvidenceClass.CLAIM)
        self.assertEqual(record.verification_state, "unverified")
        self.assertEqual(record.project_id, "PRJ-EXAMPLE-01")


class DedupTests(unittest.TestCase):
    def test_same_url_collapses_into_one_group(self):
        groups = group_duplicates((result(), result()))
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].source_count, 2)

    def test_different_url_yields_separate_groups(self):
        groups = group_duplicates((result(url="https://example.invalid/a"),
                                   result(url="https://example.invalid/b")))
        self.assertEqual(len(groups), 2)

    def test_url_case_and_trailing_slash_are_canonicalized(self):
        a = result(url="https://Example.invalid/Path/")
        b = result(url="https://example.invalid/Path")
        groups = group_duplicates((a, b))
        self.assertEqual(len(groups), 1)

    def test_no_provenance_is_lost_within_a_group(self):
        a, b = result(title="First listing"), result(title="Second listing")
        groups = group_duplicates((a, b))
        self.assertEqual(set(m.title for m in groups[0].members), {"First listing", "Second listing"})

    def test_dedup_rate_reflects_collapsed_duplicates(self):
        groups = group_duplicates((result(), result(), result(url="https://example.invalid/other")))
        self.assertAlmostEqual(dedup_rate(groups), 1 - 2 / 3)

    def test_cross_scope_mixing_is_rejected(self):
        a = result(project_id="PRJ-A", lane_id="LANE-A")
        b = result(project_id="PRJ-B", lane_id="LANE-A")
        with self.assertRaisesRegex(ValueError, "cross_run_contamination"):
            group_duplicates((a, b))

    def test_source_diversity_counts_distinct_providers(self):
        groups = group_duplicates((result(provider="a"), result(provider="b", url="https://example.invalid/2")))
        diversity = source_diversity(groups)
        self.assertEqual(diversity["distinct_providers"], 2)
        self.assertEqual(diversity["total_raw_results"], 2)


class EntityResolutionTests(unittest.TestCase):
    def test_unresolved_when_no_entity_hint(self):
        groups = group_duplicates((result(entity_hint=None),))
        candidates = resolve_entities(groups)
        self.assertEqual(candidates[0].resolution_state, "unresolved")

    def test_probable_when_single_group_supports_name(self):
        groups = group_duplicates((result(entity_hint="Example Company A"),))
        candidates = resolve_entities(groups)
        self.assertEqual(candidates[0].resolution_state, "probable")

    def test_exact_when_two_independent_groups_agree(self):
        groups = group_duplicates((
            result(url="https://example.invalid/1", entity_hint="Example Company A"),
            result(url="https://example.invalid/2", entity_hint="Example Company A"),
        ))
        candidates = resolve_entities(groups)
        self.assertEqual(candidates[0].resolution_state, "exact")
        self.assertEqual(len(candidates[0].supporting_group_ids), 2)

    def test_ambiguous_never_auto_merges_conflicting_hints_in_one_group(self):
        groups = group_duplicates((
            result(entity_hint="Example Company A"),
            result(entity_hint="Totally Different Company B"),
        ))
        candidates = resolve_entities(groups)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].resolution_state, "ambiguous")

    def test_resolution_is_deterministic(self):
        groups = group_duplicates((result(entity_hint="Example Company A"),
                                   result(url="https://example.invalid/2", entity_hint="Example Company A")))
        self.assertEqual(resolve_entities(groups), resolve_entities(groups))


class BuyerClassificationTests(unittest.TestCase):
    def test_unknown_when_no_keyword_matches(self):
        groups = group_duplicates((result(title="Nothing relevant here", snippet="just filler text"),))
        candidates = resolve_entities(groups)
        groups_by_id = {g.group_id: g for g in groups}
        classification = classify_buyer(candidates[0], groups_by_id)
        self.assertEqual(classification.category, "unknown")
        self.assertEqual(classification.confidence, 0.0)

    def test_steel_mill_keyword_is_classified(self):
        groups = group_duplicates((result(title="Example Steel Mill Ltd", snippet="a steel mill in Exampleland"),))
        candidates = resolve_entities(groups)
        groups_by_id = {g.group_id: g for g in groups}
        classification = classify_buyer(candidates[0], groups_by_id)
        self.assertEqual(classification.category, "end_user_steel_mill")
        self.assertGreater(classification.confidence, 0.0)

    def test_classification_never_invents_a_real_company_fact(self):
        groups = group_duplicates((result(),))
        candidates = resolve_entities(groups)
        groups_by_id = {g.group_id: g for g in groups}
        classification = classify_buyer(candidates[0], groups_by_id)
        classification.validate()


class ScoringTests(unittest.TestCase):
    def test_weights_must_sum_to_one(self):
        with self.assertRaises(ValueError):
            DiscoveryScoreWeights(*([0.5] * 9)).validate()

    def test_default_weights_are_valid(self):
        DEFAULT_DISCOVERY_SCORE_WEIGHTS.validate()

    def test_scoring_is_deterministic(self):
        groups = group_duplicates((result(),))
        candidates = resolve_entities(groups)
        groups_by_id = {g.group_id: g for g in groups}
        classification = classify_buyer(candidates[0], groups_by_id)
        first = score_entity(candidates[0], groups_by_id, classification)
        second = score_entity(candidates[0], groups_by_id, classification)
        self.assertEqual(first.score, second.score)
        self.assertEqual(first.breakdown, second.breakdown)

    def test_score_stays_within_unit_range(self):
        groups = group_duplicates((result(),))
        candidates = resolve_entities(groups)
        groups_by_id = {g.group_id: g for g in groups}
        classification = classify_buyer(candidates[0], groups_by_id)
        scored = score_entity(candidates[0], groups_by_id, classification)
        self.assertGreaterEqual(scored.score, 0.0)
        self.assertLessEqual(scored.score, 1.0)

    def test_exact_resolution_scores_higher_verification_depth_than_ambiguous(self):
        exact_groups = group_duplicates((
            result(url="https://example.invalid/1", entity_hint="Example Company A"),
            result(url="https://example.invalid/2", entity_hint="Example Company A"),
        ))
        exact_candidates = resolve_entities(exact_groups)
        exact_by_id = {g.group_id: g for g in exact_groups}
        exact_classification = classify_buyer(exact_candidates[0], exact_by_id)
        exact_scored = score_entity(exact_candidates[0], exact_by_id, exact_classification)

        ambiguous_groups = group_duplicates((
            result(entity_hint="Example Company A"),
            result(entity_hint="Totally Different Company B"),
        ))
        ambiguous_candidates = resolve_entities(ambiguous_groups)
        ambiguous_by_id = {g.group_id: g for g in ambiguous_groups}
        ambiguous_classification = classify_buyer(ambiguous_candidates[0], ambiguous_by_id)
        ambiguous_scored = score_entity(ambiguous_candidates[0], ambiguous_by_id, ambiguous_classification)

        self.assertGreater(exact_scored.breakdown["verification_depth"],
                           ambiguous_scored.breakdown["verification_depth"])


class VerificationQueueTests(unittest.TestCase):
    def test_high_score_requires_primary_source(self):
        from discovery_pipeline import ScoredEntity
        scored = (ScoredEntity("ent_1", 0.9, {}),)
        queue = build_verification_queue(scored, primary_threshold=0.7)
        self.assertEqual(queue[0].requirement, "primary_source_required")

    def test_low_score_requires_secondary_source(self):
        from discovery_pipeline import ScoredEntity
        scored = (ScoredEntity("ent_1", 0.2, {}),)
        queue = build_verification_queue(scored, primary_threshold=0.7)
        self.assertEqual(queue[0].requirement, "secondary_source_required")

    def test_queue_is_capped_at_top_n(self):
        from discovery_pipeline import ScoredEntity
        scored = tuple(ScoredEntity(f"ent_{i}", i / 10, {}) for i in range(30))
        queue = build_verification_queue(scored, top_n=5)
        self.assertEqual(len(queue), 5)

    def test_queue_never_marks_anything_verified(self):
        from discovery_pipeline import ScoredEntity
        scored = (ScoredEntity("ent_1", 0.9, {}),)
        queue = build_verification_queue(scored)
        self.assertNotIn("verified", queue[0].requirement)


class HighVolumeDeterminismTests(unittest.TestCase):
    def _synthetic_batch(self, n: int) -> tuple[NormalizedDiscoveryResult, ...]:
        records = []
        for i in range(n):
            is_duplicate_of = i % 7 == 0 and i > 0  # inject a deterministic duplicate pattern
            url = f"https://example.invalid/company-{i // 7 if is_duplicate_of else i}"
            entity = f"Example Company {(i // 7) if is_duplicate_of else i}" if i % 3 != 0 else None
            records.append(result(
                url=url, entity_hint=entity, raw_query=f"widget distributor query {i % 5}",
                title=f"Listing {i}" + (" steel mill" if i % 11 == 0 else ""),
                snippet=f"snippet {i}" + (" tender procurement issued" if i % 13 == 0 else ""),
            ))
        return tuple(records)

    def test_500_synthetic_discoveries_process_deterministically(self):
        batch = self._synthetic_batch(500)
        for record in batch:
            record.validate()

        groups_first = group_duplicates(batch)
        groups_second = group_duplicates(batch)
        self.assertEqual(groups_first, groups_second)
        self.assertLess(len(groups_first), 500)  # duplicates actually collapsed

        total_sources = sum(g.source_count for g in groups_first)
        self.assertEqual(total_sources, 500)  # no provenance lost

        candidates = resolve_entities(groups_first)
        self.assertTrue(any(c.resolution_state == "unresolved" for c in candidates))

        groups_by_id = {g.group_id: g for g in groups_first}
        scored = tuple(
            score_entity(c, groups_by_id, classify_buyer(c, groups_by_id))
            for c in candidates
        )
        scored_again = tuple(
            score_entity(c, groups_by_id, classify_buyer(c, groups_by_id))
            for c in candidates
        )
        self.assertEqual(scored, scored_again)  # reproducible scoring

        diversity = source_diversity(groups_first)
        self.assertGreaterEqual(diversity["total_raw_results"], 500)

        queue = build_verification_queue(scored, top_n=20)
        self.assertLessEqual(len(queue), 20)
        for item in queue:
            item.validate()

        for record in batch:
            self.assertEqual(record.project_id, "PRJ-EXAMPLE-01")
            self.assertEqual(record.lane_id, "LANE-A")
            self.assertEqual(record.evidence_class, EvidenceClass.CLAIM)


if __name__ == "__main__":
    unittest.main()
