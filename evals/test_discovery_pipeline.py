from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from contracts import EvidenceClass
from discovery_pipeline import (
    DEFAULT_DISCOVERY_SCORE_WEIGHTS,
    BuyerClassification,
    DiscoveryScoreWeights,
    NormalizedDiscoveryResult,
    NullDiscoveryAdapter,
    QueryExpansionPlan,
    ScoredEntity,
    build_approval_pack,
    build_verification_queue,
    classify_buyer,
    compute_run_metrics,
    dedup_rate,
    default_discovery_adapters,
    group_duplicates,
    ingest_external_discoveries,
    process_discovery_batch,
    resolve_entities,
    score_entity,
    source_diversity,
)
from research_lab import ResearchLabStore, ResearchRun

UTC_NOW = "2026-09-04T10:00:00+00:00"
RECENT = "2026-08-20T00:00:00+00:00"
STALE = "2024-01-01T00:00:00+00:00"


def plan(**changes) -> QueryExpansionPlan:
    values = dict(
        objective="Find plausible buyers for an example product.",
        project_id="PRJ-EXAMPLE-01",
        lane_id="LANE-A",
        query_set_version="qsv-v0.1",
        product_terms=("widget", "gadget"),
        buyer_terms=("distributor",),
        procurement_terms=("tender",),
        industry_terms=("manufacturing",),
        geography_terms=("Exampleland",),
        language_terms=("en", "fr"),
    )
    values.update(changes)
    return QueryExpansionPlan(**values)


def result(**changes) -> NormalizedDiscoveryResult:
    values = dict(
        provider="null-discovery-adapter",
        query="widget distributor Exampleland",
        url="https://example.invalid/company-a",
        title="Example Company A steel mill",
        snippet="A tender for widget procurement was issued by Example Company A.",
        retrieved_at=UTC_NOW,
        published_at=RECENT,
        project_id="PRJ-EXAMPLE-01",
        lane_id="LANE-A",
        entity_name_hint="Example Company A",
        country_hint="Exampleland",
        buyer_type_hint=None,
    )
    values.update(changes)
    return NormalizedDiscoveryResult(**values)


def run(**changes) -> ResearchRun:
    values = dict(run_id="run-2026-09-04-001", project_id="PRJ-EXAMPLE-01", lane_id="LANE-A",
                 query_set_version="qsv-v0.1", objective="Find plausible buyers.", created_at=UTC_NOW)
    values.update(changes)
    return ResearchRun(**values)


class QueryExpansionPlanTests(unittest.TestCase):
    def test_valid_plan_passes(self):
        plan().validate()

    def test_rejects_empty_product_terms(self):
        with self.assertRaises(ValueError):
            plan(product_terms=()).validate()

    def test_rejects_duplicate_terms(self):
        with self.assertRaises(ValueError):
            plan(product_terms=("widget", "widget")).validate()

    def test_expand_is_deterministic_and_bounded(self):
        self.assertEqual(plan().expand(), plan().expand())
        big = plan(product_terms=tuple(f"p{i}" for i in range(50)))
        self.assertLessEqual(len(big.expand(max_queries=10)), 10)

    def test_project_and_lane_ids_pass_through(self):
        p = plan(project_id="anything-goes", lane_id="totally-made-up-lane")
        p.validate()
        self.assertEqual(p.lane_id, "totally-made-up-lane")


class NullDiscoveryAdapterTests(unittest.TestCase):
    def test_always_returns_empty(self):
        self.assertEqual(NullDiscoveryAdapter().discover("q", limit=10), ())

    def test_default_registry_is_fresh_each_call(self):
        self.assertIsNot(default_discovery_adapters(), default_discovery_adapters())


class NormalizedDiscoveryResultTests(unittest.TestCase):
    def test_valid_result_passes(self):
        result().validate()

    def test_evidence_class_is_locked_to_claim(self):
        with self.assertRaisesRegex(ValueError, "normalized_discovery_result_must_be_claim"):
            result(evidence_class=EvidenceClass.FACT).validate()

    def test_verification_state_is_locked_to_unverified(self):
        with self.assertRaisesRegex(ValueError, "normalized_discovery_result_must_be_unverified"):
            result(verification_state="verified").validate()

    def test_rejects_invalid_buyer_type_hint(self):
        with self.assertRaises(ValueError):
            result(buyer_type_hint="not_a_real_category").validate()

    def test_project_and_lane_ids_pass_through_unchanged(self):
        r = result(project_id="anything-goes", lane_id="totally-made-up-lane")
        r.validate()
        self.assertEqual(r.lane_id, "totally-made-up-lane")

    def test_to_research_run_record_never_upgrades_evidence(self):
        record = result().to_research_run_record(run_id="run-001", query_set_version="qsv-v0.1")
        self.assertEqual(record.evidence_class, EvidenceClass.CLAIM)
        self.assertEqual(record.verification_state, "unverified")


class DedupCategoryTests(unittest.TestCase):
    def test_exact_duplicate_same_url(self):
        groups = group_duplicates((result(), result()))
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].dedup_category, "exact_duplicate")
        self.assertEqual(groups[0].source_count, 2)

    def test_unique_when_nothing_shares_identity(self):
        groups = group_duplicates((result(url="https://example.invalid/a", entity_name_hint=None),))
        self.assertEqual(groups[0].dedup_category, "unique")

    def test_probable_duplicate_across_urls_same_entity_same_country(self):
        groups = group_duplicates((
            result(url="https://example.invalid/1", entity_name_hint="Example Co", country_hint="Exampleland"),
            result(url="https://example.invalid/2", entity_name_hint="Example Co", country_hint="Exampleland"),
        ))
        self.assertEqual({g.dedup_category for g in groups}, {"probable_duplicate"})
        self.assertIn(groups[1].group_id, groups[0].related_group_ids)

    def test_ambiguous_when_same_entity_conflicting_country(self):
        groups = group_duplicates((
            result(url="https://example.invalid/1", entity_name_hint="Example Co", country_hint="Exampleland"),
            result(url="https://example.invalid/2", entity_name_hint="Example Co", country_hint="Otherland"),
        ))
        self.assertEqual({g.dedup_category for g in groups}, {"ambiguous"})

    def test_no_provenance_is_lost(self):
        a, b = result(title="First"), result(title="Second")
        groups = group_duplicates((a, b))
        self.assertEqual({m.title for m in groups[0].members}, {"First", "Second"})

    def test_cross_scope_mixing_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "cross_run_contamination"):
            group_duplicates((result(project_id="PRJ-A"), result(project_id="PRJ-B")))

    def test_source_diversity_counts_distinct_providers(self):
        groups = group_duplicates((result(provider="a"), result(provider="b", url="https://example.invalid/2")))
        diversity = source_diversity(groups)
        self.assertEqual(diversity["distinct_providers"], 2)


class EntityResolutionTests(unittest.TestCase):
    def test_unresolved_when_no_entity_hint(self):
        groups = group_duplicates((result(entity_name_hint=None),))
        self.assertEqual(resolve_entities(groups)[0].resolution_state, "unresolved")

    def test_probable_when_single_group_supports_name(self):
        groups = group_duplicates((result(entity_name_hint="Example Company A"),))
        self.assertEqual(resolve_entities(groups)[0].resolution_state, "probable")

    def test_exact_when_two_independent_groups_agree(self):
        groups = group_duplicates((
            result(url="https://example.invalid/1", entity_name_hint="Example Company A"),
            result(url="https://example.invalid/2", entity_name_hint="Example Company A"),
        ))
        candidates = resolve_entities(groups)
        self.assertEqual(candidates[0].resolution_state, "exact")

    def test_ambiguous_never_auto_merges(self):
        groups = group_duplicates((
            result(entity_name_hint="Example Company A"),
            result(entity_name_hint="Totally Different Company B"),
        ))
        candidates = resolve_entities(groups)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].resolution_state, "ambiguous")

    def test_resolution_is_deterministic(self):
        groups = group_duplicates((result(entity_name_hint="Example Company A"),
                                   result(url="https://example.invalid/2", entity_name_hint="Example Company A")))
        self.assertEqual(resolve_entities(groups), resolve_entities(groups))


class BuyerClassificationTests(unittest.TestCase):
    def test_unknown_when_no_signal(self):
        groups = group_duplicates((result(title="Nothing relevant", snippet="just filler"),))
        candidates = resolve_entities(groups)
        classification = classify_buyer(candidates[0], {g.group_id: g for g in groups})
        self.assertEqual(classification.category, "unknown")
        self.assertEqual(classification.confidence, 0.0)
        self.assertFalse(classification.is_buyer_opportunity)

    def test_steel_mill_keyword_is_classified_as_buyer(self):
        groups = group_duplicates((result(title="Example Steel Mill Ltd", snippet="a steel mill"),))
        candidates = resolve_entities(groups)
        classification = classify_buyer(candidates[0], {g.group_id: g for g in groups})
        self.assertEqual(classification.category, "steel_mill")
        self.assertTrue(classification.is_buyer_opportunity)

    def test_logistics_forwarder_is_not_treated_as_buyer_even_with_high_volume(self):
        # "Bsm Forwarding"-like entity appearing across MANY independent groups (high shipment
        # count) must still classify as logistics_intermediary, never promoted to a buyer
        # category merely because it has many supporting records.
        members = tuple(
            result(url=f"https://example.invalid/shipment-{i}", entity_name_hint="Bsm Forwarding",
                  title="Bsm Forwarding Co", snippet=f"shipment record {i} handled by Bsm Forwarding")
            for i in range(20)
        )
        groups = group_duplicates(members)
        candidates = resolve_entities(groups)
        self.assertEqual(candidates[0].resolution_state, "exact")  # strong volume support...
        classification = classify_buyer(candidates[0], {g.group_id: g for g in groups})
        self.assertEqual(classification.category, "logistics_intermediary")  # ...but not a buyer
        self.assertFalse(classification.is_buyer_opportunity)

    def test_buyer_type_hint_used_when_no_keyword_matches(self):
        groups = group_duplicates((result(title="no keywords here", snippet="plain text",
                                          buyer_type_hint="trader"),))
        candidates = resolve_entities(groups)
        classification = classify_buyer(candidates[0], {g.group_id: g for g in groups})
        self.assertEqual(classification.category, "trader")

    def test_classification_never_invents_a_real_company_fact(self):
        groups = group_duplicates((result(),))
        candidates = resolve_entities(groups)
        classify_buyer(candidates[0], {g.group_id: g for g in groups}).validate()


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
        first = score_entity(candidates[0], groups_by_id)
        second = score_entity(candidates[0], groups_by_id)
        self.assertEqual(first, second)

    def test_score_stays_within_unit_range(self):
        groups = group_duplicates((result(),))
        candidates = resolve_entities(groups)
        scored = score_entity(candidates[0], {g.group_id: g for g in groups})
        self.assertGreaterEqual(scored.score, 0.0)
        self.assertLessEqual(scored.score, 1.0)

    def test_exact_resolution_scores_higher_verification_depth_than_ambiguous(self):
        exact_groups = group_duplicates((
            result(url="https://example.invalid/1", entity_name_hint="Example Company A"),
            result(url="https://example.invalid/2", entity_name_hint="Example Company A"),
        ))
        exact_candidates = resolve_entities(exact_groups)
        exact_scored = score_entity(exact_candidates[0], {g.group_id: g for g in exact_groups})

        ambiguous_groups = group_duplicates((
            result(entity_name_hint="Example Company A"),
            result(entity_name_hint="Totally Different Company B"),
        ))
        ambiguous_candidates = resolve_entities(ambiguous_groups)
        ambiguous_scored = score_entity(ambiguous_candidates[0], {g.group_id: g for g in ambiguous_groups})

        self.assertGreater(exact_scored.breakdown["verification_depth"],
                           ambiguous_scored.breakdown["verification_depth"])


class VerificationQueueTests(unittest.TestCase):
    def test_high_score_requires_primary_source(self):
        scored = (ScoredEntity("ent_1", 0.9, {}),)
        classifications = {"ent_1": BuyerClassification("ent_1", "steel_mill", 0.8, "test")}
        queue = build_verification_queue(scored, classifications, primary_threshold=0.7)
        self.assertEqual(queue[0].requirement, "primary_source_required")

    def test_low_score_requires_secondary_source(self):
        scored = (ScoredEntity("ent_1", 0.2, {}),)
        classifications = {"ent_1": BuyerClassification("ent_1", "trader", 0.5, "test")}
        queue = build_verification_queue(scored, classifications, primary_threshold=0.7)
        self.assertEqual(queue[0].requirement, "secondary_source_required")

    def test_logistics_intermediary_is_excluded_from_the_queue(self):
        scored = (ScoredEntity("ent_1", 0.95, {}),)
        classifications = {"ent_1": BuyerClassification("ent_1", "logistics_intermediary", 0.8, "test")}
        queue = build_verification_queue(scored, classifications)
        self.assertEqual(queue, ())

    def test_unknown_is_excluded_from_the_queue(self):
        scored = (ScoredEntity("ent_1", 0.95, {}),)
        classifications = {"ent_1": BuyerClassification("ent_1", "unknown", 0.0, "test")}
        queue = build_verification_queue(scored, classifications)
        self.assertEqual(queue, ())

    def test_queue_never_marks_anything_verified(self):
        scored = (ScoredEntity("ent_1", 0.9, {}),)
        classifications = {"ent_1": BuyerClassification("ent_1", "trader", 0.6, "test")}
        queue = build_verification_queue(scored, classifications)
        self.assertNotIn("verified", queue[0].requirement)

    def test_queue_capped_at_top_n(self):
        scored = tuple(ScoredEntity(f"ent_{i}", i / 30, {}) for i in range(30))
        classifications = {f"ent_{i}": BuyerClassification(f"ent_{i}", "trader", 0.5, "test") for i in range(30)}
        queue = build_verification_queue(scored, classifications, top_n=5)
        self.assertEqual(len(queue), 5)


class RunMetricsTests(unittest.TestCase):
    def test_metrics_never_invents_verified_or_false_positive_counts(self):
        groups = group_duplicates((result(),))
        candidates = resolve_entities(groups)
        classification = classify_buyer(candidates[0], {g.group_id: g for g in groups})
        metrics = compute_run_metrics("run-1", (result(),), groups, (classification,), processing_time=0.01)
        self.assertEqual(metrics.verified_buyer_count, 0)
        self.assertIsNone(metrics.false_positive_rate)

    def test_stale_result_rate_reflects_old_published_at(self):
        stale_result = result(published_at=STALE)
        metrics = compute_run_metrics("run-1", (stale_result,), group_duplicates((stale_result,)), (),
                                      processing_time=0.01)
        self.assertEqual(metrics.stale_result_rate, 1.0)

    def test_plausible_buyer_count_excludes_logistics_and_unknown(self):
        buyer = BuyerClassification("ent_1", "steel_mill", 0.7, "test")
        logistics = BuyerClassification("ent_2", "logistics_intermediary", 0.7, "test")
        unknown = BuyerClassification("ent_3", "unknown", 0.0, "test")
        metrics = compute_run_metrics("run-1", (result(),), group_duplicates((result(),)),
                                      (buyer, logistics, unknown), processing_time=0.01)
        self.assertEqual(metrics.plausible_buyer_count, 1)


class ProcessDiscoveryBatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ResearchLabStore(Path(self.temp.name))

    def tearDown(self):
        self.temp.cleanup()

    def test_outcome_is_deterministic_across_two_runs(self):
        results = (result(), result(url="https://example.invalid/2", entity_name_hint=None))
        first = process_discovery_batch(run(run_id="run-a"), results)
        second = process_discovery_batch(run(run_id="run-b"), results)
        self.assertEqual(first.groups, second.groups)
        self.assertEqual(first.entities, second.entities)
        self.assertEqual(first.scored, second.scored)

    def test_persists_run_candidates_entities_scores_and_report(self):
        results = (result(), result(url="https://example.invalid/2", entity_name_hint="Other Co"))
        outcome = process_discovery_batch(run(), results, store=self.store)
        self.assertIsNotNone(self.store.read_run("run-2026-09-04-001"))
        self.assertEqual(len(self.store.read_candidates("run-2026-09-04-001")), 2)
        self.assertTrue((self.store.root / "entities" / "run-2026-09-04-001.json").exists())
        self.assertTrue((self.store.root / "scores" / "run-2026-09-04-001.json").exists())
        self.assertTrue((self.store.root / "reports" / "run-2026-09-04-001.json").exists())
        self.assertEqual(outcome.metrics.raw_count, 2)

    def test_persisted_candidates_never_carry_fact_or_verified(self):
        process_discovery_batch(run(), (result(),), store=self.store)
        for record in self.store.read_candidates("run-2026-09-04-001"):
            self.assertEqual(record.evidence_class, EvidenceClass.CLAIM)
            self.assertEqual(record.verification_state, "unverified")


class HighVolumeDeterminismTests(unittest.TestCase):
    def _synthetic_batch(self, n: int) -> tuple[NormalizedDiscoveryResult, ...]:
        records = []
        for i in range(n):
            is_dup = i % 7 == 0 and i > 0
            url = f"https://example.invalid/company-{i // 7 if is_dup else i}"
            entity = f"Example Company {(i // 7) if is_dup else i}" if i % 3 != 0 else None
            records.append(result(
                url=url, entity_name_hint=entity, query=f"widget distributor query {i % 5}",
                title=f"Listing {i}" + (" steel mill" if i % 11 == 0 else ""),
                snippet=f"snippet {i}" + (" tender procurement issued" if i % 13 == 0 else ""),
            ))
        return tuple(records)

    def test_500_synthetic_discoveries_process_deterministically(self):
        batch = self._synthetic_batch(500)
        for record in batch:
            record.validate()

        outcome_a = process_discovery_batch(run(), batch)
        outcome_b = process_discovery_batch(run(), batch)
        self.assertEqual(outcome_a.groups, outcome_b.groups)
        self.assertEqual(outcome_a.scored, outcome_b.scored)

        self.assertLess(len(outcome_a.groups), 500)
        total_sources = sum(g.source_count for g in outcome_a.groups)
        self.assertEqual(total_sources, 500)  # no provenance lost

        self.assertTrue(any(c.resolution_state == "unresolved" for c in outcome_a.entities))
        self.assertLessEqual(len(outcome_a.verification_queue), 20)
        for item in outcome_a.verification_queue:
            item.validate()

        self.assertEqual(outcome_a.metrics.raw_count, 500)
        self.assertEqual(outcome_a.metrics.verified_buyer_count, 0)
        self.assertIsNone(outcome_a.metrics.false_positive_rate)

        for record in batch:
            self.assertEqual(record.project_id, "PRJ-EXAMPLE-01")
            self.assertEqual(record.lane_id, "LANE-A")
            self.assertEqual(record.evidence_class, EvidenceClass.CLAIM)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


class IngestExternalDiscoveriesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "external.jsonl"

    def tearDown(self):
        self.temp.cleanup()

    def _row(self, **changes) -> dict:
        row = dict(
            provider="external-live-research", query="widget distributor Exampleland",
            url="https://example.invalid/company-a", title="Example Company A steel mill",
            snippet="A tender for widget procurement was issued.", retrieved_at=UTC_NOW,
            published_at=RECENT, entity_name_hint="Example Company A", country_hint="Exampleland",
        )
        row.update(changes)
        return row

    def test_ingests_valid_rows(self):
        _write_jsonl(self.path, [self._row(), self._row(url="https://example.invalid/company-b")])
        results = ingest_external_discoveries(self.path, project_id="PRJ-EXAMPLE-01", lane_id="LANE-A")
        self.assertEqual(len(results), 2)
        for r in results:
            r.validate()

    def test_project_and_lane_id_come_from_caller_not_file(self):
        rows = [self._row()]
        rows[0]["project_id"] = "PRJ-SHOULD-BE-IGNORED"
        rows[0]["lane_id"] = "LANE-SHOULD-BE-IGNORED"
        _write_jsonl(self.path, rows)
        results = ingest_external_discoveries(self.path, project_id="PRJ-EXAMPLE-01", lane_id="LANE-A")
        self.assertEqual(results[0].project_id, "PRJ-EXAMPLE-01")
        self.assertEqual(results[0].lane_id, "LANE-A")

    def test_external_evidence_class_and_verification_are_never_trusted(self):
        rows = [self._row()]
        rows[0]["evidence_class"] = "FACT"
        rows[0]["verification_state"] = "verified"
        _write_jsonl(self.path, rows)
        results = ingest_external_discoveries(self.path, project_id="PRJ-EXAMPLE-01", lane_id="LANE-A")
        self.assertEqual(results[0].evidence_class, EvidenceClass.CLAIM)
        self.assertEqual(results[0].verification_state, "unverified")

    def test_missing_required_field_fails_the_whole_batch(self):
        rows = [self._row(), self._row()]
        del rows[1]["url"]
        _write_jsonl(self.path, rows)
        with self.assertRaisesRegex(ValueError, "missing_fields_at_line_2"):
            ingest_external_discoveries(self.path, project_id="PRJ-EXAMPLE-01", lane_id="LANE-A")

    def test_malformed_json_line_fails_closed(self):
        self.path.write_text('{"provider": "x"\n', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid_jsonl_at_line_1"):
            ingest_external_discoveries(self.path, project_id="PRJ-EXAMPLE-01", lane_id="LANE-A")

    def test_blank_lines_are_skipped(self):
        _write_jsonl(self.path, [self._row()])
        self.path.write_text(self.path.read_text(encoding="utf-8") + "\n\n", encoding="utf-8")
        results = ingest_external_discoveries(self.path, project_id="PRJ-EXAMPLE-01", lane_id="LANE-A")
        self.assertEqual(len(results), 1)


class ApprovalPackTests(unittest.TestCase):
    def test_recommend_verification_for_high_scoring_queued_buyer(self):
        results = (result(title="Example Steel Mill Ltd", snippet="a steel mill, tender procurement issued"),)
        outcome = process_discovery_batch(run(), results)
        pack = build_approval_pack(outcome, min_score_to_recommend=0.0)
        self.assertEqual(len(pack), 1)
        self.assertEqual(pack[0].recommended_action, "recommend_verification")
        self.assertTrue(pack[0].requires_human_approval)
        self.assertTrue(pack[0].supporting_urls)

    def test_reject_when_not_in_verification_queue(self):
        results = (result(title="Example Steel Mill Ltd", snippet="a steel mill"),)
        outcome = process_discovery_batch(run(), results, top_n=0)
        pack = build_approval_pack(outcome)
        self.assertEqual(pack[0].recommended_action, "reject")

    def test_watch_when_queued_but_below_threshold(self):
        results = (result(title="Example Steel Mill Ltd", snippet="a steel mill"),)
        outcome = process_discovery_batch(run(), results)
        pack = build_approval_pack(outcome, min_score_to_recommend=0.99)
        self.assertEqual(pack[0].recommended_action, "watch")

    def test_logistics_intermediary_never_appears_in_the_pack(self):
        results = tuple(
            result(url=f"https://example.invalid/ship-{i}", entity_name_hint="Bsm Forwarding",
                  title="Bsm Forwarding Co", snippet=f"shipment {i} handled by Bsm Forwarding")
            for i in range(10)
        )
        outcome = process_discovery_batch(run(), results)
        pack = build_approval_pack(outcome)
        self.assertEqual(pack, ())

    def test_pack_never_requires_anything_but_human_approval(self):
        results = (result(title="Example Steel Mill Ltd", snippet="a steel mill, tender procurement issued"),)
        outcome = process_discovery_batch(run(), results)
        for item in build_approval_pack(outcome, min_score_to_recommend=0.0):
            item.validate()
            self.assertTrue(item.requires_human_approval)

    def test_pack_is_sorted_by_descending_score(self):
        results = tuple(
            result(url=f"https://example.invalid/{i}", entity_name_hint=f"Company {i}",
                  title=f"Company {i} steel mill", snippet="tender procurement issued" if i == 0 else "plain")
            for i in range(3)
        )
        outcome = process_discovery_batch(run(), results, top_n=10)
        pack = build_approval_pack(outcome, min_score_to_recommend=0.0)
        scores = [item.score for item in pack]
        self.assertEqual(scores, sorted(scores, reverse=True))


class EndToEndIngestToApprovalPackTests(unittest.TestCase):
    """The 'one vertical proof': external live-research JSONL -> ingest -> dedup -> entity
    resolution -> buyer role -> score -> verification queue -> approval-ready shortlist.
    """

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "external.jsonl"

    def tearDown(self):
        self.temp.cleanup()

    def test_full_vertical_from_external_jsonl_to_approval_pack(self):
        rows = [
            dict(provider="external-live-research", query="widget distributor Exampleland",
                url="https://example.invalid/steelco", title="Example Steel Co",
                snippet="Example Steel Co issued a tender for widget procurement.", retrieved_at=UTC_NOW,
                published_at=RECENT, entity_name_hint="Example Steel Co", country_hint="Exampleland"),
            dict(provider="external-live-research", query="widget distributor Exampleland",
                url="https://example.invalid/steelco-2", title="Example Steel Co listing",
                snippet="Another listing for Example Steel Co, a steel mill.", retrieved_at=UTC_NOW,
                published_at=RECENT, entity_name_hint="Example Steel Co", country_hint="Exampleland"),
            dict(provider="external-live-research", query="widget distributor Exampleland",
                url="https://example.invalid/forwarder", title="Bsm Forwarding",
                snippet="Bsm Forwarding handled shipment logistics.", retrieved_at=UTC_NOW,
                published_at=RECENT, entity_name_hint="Bsm Forwarding", country_hint="Exampleland"),
            dict(provider="external-live-research", query="widget distributor Exampleland",
                url="https://example.invalid/unknown-1", title="Random Listing",
                snippet="No useful signal here.", retrieved_at=UTC_NOW, published_at=None),
        ]
        _write_jsonl(self.path, rows)

        ingested = ingest_external_discoveries(self.path, project_id="PRJ-EXAMPLE-01", lane_id="LANE-A")
        self.assertEqual(len(ingested), 4)
        for r in ingested:
            self.assertEqual(r.evidence_class, EvidenceClass.CLAIM)
            self.assertEqual(r.verification_state, "unverified")

        outcome = process_discovery_batch(run(), ingested, top_n=10, primary_threshold=0.0)
        pack = build_approval_pack(outcome, min_score_to_recommend=0.0)

        # the steel co (2 independent sources) should be recommended; the forwarder must not appear
        self.assertTrue(any(item.buyer_category == "steel_mill" for item in pack))
        self.assertFalse(any(item.normalized_name == "bsm forwarding" for item in pack))
        for item in pack:
            item.validate()
            self.assertTrue(item.requires_human_approval)
            self.assertTrue(item.supporting_urls)


if __name__ == "__main__":
    unittest.main()
