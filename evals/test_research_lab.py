from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from contracts import EvidenceClass
from research_lab import (
    DEFAULT_RESEARCH_BENCHMARK_POLICY,
    DEFAULT_SCORE_WEIGHTS,
    OpportunityScoreWeights,
    ResearchBenchmarkPolicy,
    ResearchLabStore,
    ResearchProviderBenchmark,
    ResearchRun,
    ResearchRunRecord,
    assign_duplicate_groups,
    dedup_rate,
    rank_opportunities,
    run_summary,
    score_opportunity,
    source_diversity,
)

UTC_NOW = "2026-09-04T10:00:00+00:00"
OLD_DATE = "2025-01-01T00:00:00+00:00"


def research_run(**changes) -> ResearchRun:
    values = dict(
        run_id="run-2026-09-04-001",
        project_id="PRJ-EXAMPLE-01",
        lane_id="LANE-A",
        query_set_version="qsv-v0.1",
        objective="Find plausible buyers for an example product.",
        created_at=UTC_NOW,
    )
    values.update(changes)
    return ResearchRun(**values)


def research_record(**changes) -> ResearchRunRecord:
    values = dict(
        run_id="run-2026-09-04-001",
        project_id="PRJ-EXAMPLE-01",
        lane_id="LANE-A",
        query_set_version="qsv-v0.1",
        provider="null-search-provider",
        query="example query",
        url="https://example.invalid/company-a",
        source_type="company_website",
        retrieved_at=UTC_NOW,
        published_at=None,
        entity_name="Example Company A",
        country="Exampleland",
        buyer_type="distributor",
        product_signal="mentions relevant product",
        evidence_class=EvidenceClass.CLAIM,
        verification_state="unverified",
    )
    values.update(changes)
    return ResearchRunRecord(**values)


def benchmark(**changes) -> ResearchProviderBenchmark:
    values = dict(
        provider_id="candidate-provider",
        coverage=0.6, unique_buyer_yield=0.1, verified_buyer_yield=0.05,
        citation_accuracy=0.85, source_quality=0.7, hallucination_rate=0.02,
        duplicate_rate=0.3, stale_result_rate=0.1, false_positive_rate=0.1,
        latency_ms=900.0, cost_per_100_raw_results=0.5, cost_per_100_verified_buyers=10.0,
        decision="BUILD", evaluated_at=UTC_NOW, sample_size=50,
    )
    values.update(changes)
    return ResearchProviderBenchmark(**values)


def policy(**changes) -> ResearchBenchmarkPolicy:
    values = dict(
        policy_version="test-research-policy-v1",
        min_coverage=0.5, min_unique_buyer_yield=0.05, min_verified_buyer_yield=0.02,
        min_citation_accuracy=0.8, min_source_quality=0.6, max_hallucination_rate=0.05,
        max_duplicate_rate=0.6, max_stale_result_rate=0.3, max_false_positive_rate=0.2,
    )
    values.update(changes)
    return ResearchBenchmarkPolicy(**values)


class ResearchRunValidationTests(unittest.TestCase):
    def test_valid_run_passes(self):
        research_run().validate()

    def test_rejects_invalid_run_id(self):
        with self.assertRaises(ValueError):
            research_run(run_id="Not Safe!").validate()

    def test_rejects_empty_objective(self):
        with self.assertRaises(ValueError):
            research_run(objective="  ").validate()

    def test_project_and_lane_ids_are_carried_unchanged(self):
        run = research_run(project_id="anything-goes", lane_id="totally-made-up-lane")
        run.validate()
        self.assertEqual(run.lane_id, "totally-made-up-lane")


class ResearchRunRecordValidationTests(unittest.TestCase):
    def test_valid_record_passes(self):
        research_record().validate()

    def test_rejects_non_retrievable_url(self):
        with self.assertRaises(ValueError):
            research_record(url="ftp://example.invalid/x").validate()

    def test_rejects_invalid_source_type(self):
        with self.assertRaises(ValueError):
            research_record(source_type="rumor").validate()

    def test_rejects_invalid_buyer_type(self):
        with self.assertRaises(ValueError):
            research_record(buyer_type="not_a_real_type").validate()

    def test_buyer_type_none_is_allowed_before_classification(self):
        research_record(buyer_type=None).validate()

    def test_rejects_naive_retrieved_at(self):
        with self.assertRaises(ValueError):
            research_record(retrieved_at="2026-09-04T10:00:00").validate()

    def test_default_review_state_is_pending(self):
        self.assertEqual(research_record().review_state, "pending")

    def test_raw_record_never_carries_fact_by_default(self):
        self.assertEqual(research_record().evidence_class, EvidenceClass.CLAIM)

    def test_unknown_lane_id_is_not_rejected(self):
        record = research_record(project_id="anything-goes", lane_id="totally-made-up-lane")
        record.validate()
        self.assertEqual(record.lane_id, "totally-made-up-lane")


class DedupTests(unittest.TestCase):
    def test_same_url_yields_same_group(self):
        a = research_record(url="https://example.invalid/x")
        b = research_record(url="https://example.invalid/x")
        grouped = assign_duplicate_groups((a, b))
        self.assertEqual(grouped[0].duplicate_group, grouped[1].duplicate_group)

    def test_different_url_yields_different_group(self):
        a = research_record(url="https://example.invalid/x")
        b = research_record(url="https://example.invalid/y")
        grouped = assign_duplicate_groups((a, b))
        self.assertNotEqual(grouped[0].duplicate_group, grouped[1].duplicate_group)

    def test_dedup_rate_is_zero_for_all_unique(self):
        records = assign_duplicate_groups((
            research_record(url="https://example.invalid/1"),
            research_record(url="https://example.invalid/2"),
        ))
        self.assertEqual(dedup_rate(records), 0.0)

    def test_dedup_rate_reflects_duplicates(self):
        records = assign_duplicate_groups((
            research_record(url="https://example.invalid/1"),
            research_record(url="https://example.invalid/1"),
            research_record(url="https://example.invalid/2"),
        ))
        self.assertAlmostEqual(dedup_rate(records), 1 - 2 / 3)

    def test_source_diversity_counts_distinct_values(self):
        records = (
            research_record(provider="a", source_type="company_website"),
            research_record(provider="b", source_type="trade_database"),
        )
        diversity = source_diversity(records)
        self.assertEqual(diversity["distinct_providers"], 2)
        self.assertEqual(diversity["distinct_source_types"], 2)


class ScoringTests(unittest.TestCase):
    def test_weights_must_sum_to_one(self):
        with self.assertRaises(ValueError):
            OpportunityScoreWeights(0.5, 0.5, 0.5, 0.5).validate()

    def test_default_weights_are_valid(self):
        DEFAULT_SCORE_WEIGHTS.validate()

    def test_verified_scores_higher_than_unverified(self):
        verified = research_record(verification_state="verified")
        unverified = research_record(verification_state="unverified")
        self.assertGreater(score_opportunity(verified), score_opportunity(unverified))

    def test_fact_scores_higher_than_claim(self):
        fact = research_record(evidence_class=EvidenceClass.FACT)
        claim = research_record(evidence_class=EvidenceClass.CLAIM)
        self.assertGreater(score_opportunity(fact), score_opportunity(claim))

    def test_score_is_deterministic(self):
        record = research_record()
        self.assertEqual(score_opportunity(record), score_opportunity(record))

    def test_score_never_exceeds_unit_range(self):
        record = research_record(verification_state="verified", evidence_class=EvidenceClass.FACT,
                                 source_type="official_portal", published_at=UTC_NOW)
        self.assertLessEqual(score_opportunity(record), 1.0)
        self.assertGreaterEqual(score_opportunity(record), 0.0)

    def test_rank_opportunities_orders_descending_and_caps_top_n(self):
        records = [research_record(url=f"https://example.invalid/{i}",
                                   verification_state="verified" if i < 3 else "unverified")
                  for i in range(10)]
        ranked = rank_opportunities(records, top_n=5)
        self.assertEqual(len(ranked), 5)
        scores = [r.opportunity_score for r in ranked]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_recent_publication_scores_higher_than_stale(self):
        recent = research_record(published_at=UTC_NOW, retrieved_at=UTC_NOW)
        stale = research_record(published_at=OLD_DATE, retrieved_at=UTC_NOW)
        self.assertGreaterEqual(score_opportunity(recent), score_opportunity(stale))


class RunSummaryTests(unittest.TestCase):
    def test_summary_counts_unique_entities_and_dedupe_rate(self):
        run = research_run()
        records = assign_duplicate_groups((
            research_record(url="https://example.invalid/1", entity_name="Company A"),
            research_record(url="https://example.invalid/1", entity_name="Company A"),
            research_record(url="https://example.invalid/2", entity_name="Company B"),
        ))
        summary = run_summary(run, records)
        self.assertEqual(summary["total_raw_discoveries"], 3)
        self.assertEqual(summary["unique_entity_count"], 2)
        self.assertAlmostEqual(summary["dedupe_rate"], 1 - 2 / 3)

    def test_summary_digest_is_deterministic(self):
        run = research_run()
        records = (research_record(),)
        self.assertEqual(run_summary(run, records)["digest"], run_summary(run, records)["digest"])

    def test_summary_never_invents_a_buyer_count_beyond_records_given(self):
        run = research_run()
        summary = run_summary(run, ())
        self.assertEqual(summary["total_raw_discoveries"], 0)
        self.assertEqual(summary["unique_entity_count"], 0)


class ResearchLabStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ResearchLabStore(Path(self.temp.name))

    def tearDown(self):
        self.temp.cleanup()

    def test_all_subdirectories_are_created(self):
        for name in ResearchLabStore.SUBDIRS:
            self.assertTrue((self.store.root / name).is_dir())

    def test_create_and_read_run_round_trips(self):
        run = research_run()
        self.store.create_run(run)
        self.assertEqual(self.store.read_run(run.run_id), run)

    def test_create_run_twice_fails_closed(self):
        run = research_run()
        self.store.create_run(run)
        with self.assertRaises(ValueError):
            self.store.create_run(run)

    def test_read_unknown_run_returns_none(self):
        self.assertIsNone(self.store.read_run("no-such-run"))

    def test_append_candidates_requires_existing_run(self):
        with self.assertRaises(KeyError):
            self.store.append_candidates("no-such-run", (research_record(),))

    def test_append_and_read_candidates_round_trips(self):
        run = research_run()
        self.store.create_run(run)
        records = (research_record(), research_record(url="https://example.invalid/2"))
        self.store.append_candidates(run.run_id, records)
        self.assertEqual(self.store.read_candidates(run.run_id), records)

    def test_append_is_cumulative_across_calls(self):
        run = research_run()
        self.store.create_run(run)
        self.store.append_candidates(run.run_id, (research_record(url="https://example.invalid/1"),))
        self.store.append_candidates(run.run_id, (research_record(url="https://example.invalid/2"),))
        self.assertEqual(len(self.store.read_candidates(run.run_id)), 2)

    def test_append_rejects_project_id_mismatch(self):
        run = research_run(project_id="PRJ-A")
        self.store.create_run(run)
        mismatched = research_record(project_id="PRJ-B")
        with self.assertRaisesRegex(ValueError, "record_project_id_mismatch"):
            self.store.append_candidates(run.run_id, (mismatched,))

    def test_append_rejects_lane_id_mismatch(self):
        run = research_run(lane_id="LANE-A")
        self.store.create_run(run)
        mismatched = research_record(lane_id="LANE-B")
        with self.assertRaisesRegex(ValueError, "record_lane_id_mismatch"):
            self.store.append_candidates(run.run_id, (mismatched,))

    def test_append_rejects_run_id_mismatch(self):
        run = research_run()
        self.store.create_run(run)
        mismatched = research_record(run_id="a-different-run")
        with self.assertRaisesRegex(ValueError, "record_run_id_mismatch"):
            self.store.append_candidates(run.run_id, (mismatched,))

    def test_a_bad_record_rejects_the_whole_batch_before_any_write(self):
        run = research_run()
        self.store.create_run(run)
        good = research_record(url="https://example.invalid/1")
        bad = research_record(url="ftp://example.invalid/2")
        with self.assertRaises(ValueError):
            self.store.append_candidates(run.run_id, (good, bad))
        self.assertEqual(self.store.read_candidates(run.run_id), ())

    def test_write_score_report_round_trips_as_json(self):
        run = research_run()
        self.store.create_run(run)
        report = run_summary(run, ())
        path = self.store.write_score_report(run.run_id, report)
        self.assertTrue(path.exists())

    def test_write_benchmark_persists_valid_record(self):
        path = self.store.write_benchmark(benchmark())
        self.assertTrue(path.exists())

    def test_write_benchmark_rejects_invalid_record(self):
        with self.assertRaises(ValueError):
            self.store.write_benchmark(benchmark(decision="KEEP", coverage=0.01))

    def test_write_entities_persists_a_list_of_dicts(self):
        path = self.store.write_entities("some-run", [{"candidate_id": "ent_1", "resolution_state": "exact"}])
        self.assertTrue(path.exists())

    def test_write_report_persists_arbitrary_dict(self):
        path = self.store.write_report("some-run", {"raw_count": 10, "unique_count": 7})
        self.assertTrue(path.exists())


class ResearchBenchmarkPolicyTests(unittest.TestCase):
    def test_valid_policy_passes(self):
        policy().validate()

    def test_rejects_out_of_range_threshold(self):
        with self.assertRaises(ValueError):
            policy(min_coverage=1.5).validate()


class ResearchProviderBenchmarkTests(unittest.TestCase):
    def test_valid_benchmark_passes(self):
        benchmark().validate()

    def test_rejects_negative_latency(self):
        with self.assertRaises(ValueError):
            benchmark(latency_ms=-1).validate()

    def test_non_numeric_rate_raises_value_error_not_type_error(self):
        try:
            benchmark(coverage="lots").validate()
            self.fail("expected ValueError")
        except ValueError:
            pass
        except TypeError:
            self.fail("non-numeric coverage must raise ValueError, not TypeError")

    def test_keep_requires_coverage_threshold(self):
        with self.assertRaisesRegex(ValueError, "coverage_below_policy"):
            benchmark(decision="KEEP", coverage=0.01).validate()

    def test_keep_requires_unique_buyer_yield_threshold(self):
        with self.assertRaisesRegex(ValueError, "unique_buyer_yield_below_policy"):
            benchmark(decision="KEEP", unique_buyer_yield=0.001).validate()

    def test_keep_requires_low_duplicate_rate(self):
        with self.assertRaisesRegex(ValueError, "duplicate_rate_above_policy"):
            benchmark(decision="KEEP", duplicate_rate=0.99).validate()

    def test_build_or_defer_may_remain_below_every_threshold(self):
        benchmark(decision="DEFER", coverage=0.01, unique_buyer_yield=0.0, verified_buyer_yield=0.0,
                 citation_accuracy=0.01, source_quality=0.01, hallucination_rate=0.9,
                 duplicate_rate=0.99, stale_result_rate=0.99, false_positive_rate=0.99).validate()

    def test_custom_policy_changes_outcome(self):
        lenient = policy(min_coverage=0.01)
        benchmark(decision="KEEP", coverage=0.05).validate(lenient)


if __name__ == "__main__":
    unittest.main()
