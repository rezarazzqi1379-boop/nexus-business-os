from __future__ import annotations

import unittest

import research_evidence as re_module
from contracts import EvidenceClass
from research_evidence import (
    EvidenceClaim,
    NullSearchProvider,
    ResearchQueryResult,
    SearchProviderBenchmark,
    SearchResult,
    run_research_query,
    search_provider_record,
)
from nexus_brain.resource_router import ResourceRouter

UTC_NOW = "2026-09-03T12:00:00+00:00"


def evidence_claim(**changes) -> EvidenceClaim:
    values = dict(
        claim_id="claim_abc123",
        statement="Example statement.",
        source_name="Example Source",
        url="https://example.invalid/page",
        retrieved_at=UTC_NOW,
        evidence_class=EvidenceClass.CLAIM,
        confidence=0.3,
        verification_state="unverified",
    )
    values.update(changes)
    return EvidenceClaim(**values)


def benchmark(**changes) -> SearchProviderBenchmark:
    values = dict(
        provider_id="candidate-provider",
        coverage=0.7,
        freshness=0.6,
        citation_accuracy=0.8,
        source_quality=0.7,
        latency_ms=800.0,
        cost_usd_per_query=0.01,
        duplicate_rate=0.05,
        hallucination_rate=0.02,
        decision="BUILD",
        evaluated_at=UTC_NOW,
        sample_size=25,
    )
    values.update(changes)
    return SearchProviderBenchmark(**values)


class NullSearchProviderTests(unittest.TestCase):
    def test_always_returns_empty_and_never_raises(self):
        provider = NullSearchProvider()
        self.assertEqual(provider.search("anything", max_results=5), ())


class EvidenceClaimValidationTests(unittest.TestCase):
    def test_valid_claim_passes(self):
        evidence_claim().validate()

    def test_rejects_non_retrievable_url(self):
        with self.assertRaisesRegex(ValueError, "evidence_claim_requires_retrievable_url"):
            evidence_claim(url="ftp://example.invalid/x").validate()

    def test_rejects_naive_retrieved_at(self):
        with self.assertRaises(ValueError):
            evidence_claim(retrieved_at="2026-09-03T12:00:00").validate()

    def test_rejects_invalid_confidence(self):
        with self.assertRaises(ValueError):
            evidence_claim(confidence=1.5).validate()

    def test_rejects_invalid_verification_state(self):
        with self.assertRaises(ValueError):
            evidence_claim(verification_state="trusted_forever").validate()

    def test_rejects_invalid_evidence_class(self):
        with self.assertRaises(ValueError):
            evidence_claim(evidence_class="NOT_A_REAL_CLASS").validate()

    def test_lane_and_project_ids_are_optional_but_preserved(self):
        claim = evidence_claim(project_id="PRJ-FAL-01", lane_id="FAL-B")
        claim.validate()
        self.assertEqual(claim.project_id, "PRJ-FAL-01")
        self.assertEqual(claim.lane_id, "FAL-B")


class SearchResultWrappingTests(unittest.TestCase):
    def test_search_result_is_always_wrapped_as_claim_never_fact(self):
        result = SearchResult(title="A Source", url="https://example.invalid/a", snippet="a claim")
        claim = re_module._claim_from_search_result(
            result, query="q", retrieved_at=UTC_NOW, project_id="PRJ-FAL-01", lane_id="FAL-A"
        )
        self.assertEqual(claim.evidence_class, EvidenceClass.CLAIM)
        self.assertEqual(claim.verification_state, "unverified")
        self.assertEqual(claim.project_id, "PRJ-FAL-01")
        self.assertEqual(claim.lane_id, "FAL-A")

    def test_same_result_same_query_same_timestamp_yields_stable_claim_id(self):
        result = SearchResult(title="A Source", url="https://example.invalid/a", snippet="a claim")
        first = re_module._claim_from_search_result(result, query="q", retrieved_at=UTC_NOW,
                                                     project_id=None, lane_id=None)
        second = re_module._claim_from_search_result(result, query="q", retrieved_at=UTC_NOW,
                                                      project_id=None, lane_id=None)
        self.assertEqual(first.claim_id, second.claim_id)


class RunResearchQueryTests(unittest.TestCase):
    def test_no_eligible_provider_degrades_gracefully(self):
        router = ResourceRouter(providers=())
        result = run_research_query(router, "ferrosilicon export buyers")
        self.assertFalse(result.provider_available)
        self.assertIsNone(result.provider_id)
        self.assertEqual(result.claims, ())

    def test_eligible_but_unimplemented_provider_also_degrades_gracefully(self):
        record = search_provider_record("some-unimplemented-provider", production_approved=True,
                                        policy_verified=True)
        router = ResourceRouter(providers=(record,))
        result = run_research_query(router, "steel mills")
        self.assertFalse(result.provider_available)
        self.assertEqual(result.claims, ())

    def test_eligible_implemented_null_provider_is_selected_but_returns_no_claims(self):
        record = search_provider_record(NullSearchProvider.provider_id, production_approved=True,
                                        policy_verified=True)
        router = ResourceRouter(providers=(record,))
        result = run_research_query(router, "ferromanganese producers", project_id="PRJ-FAL-01", lane_id="FAL-A")
        self.assertTrue(result.provider_available)
        self.assertEqual(result.provider_id, NullSearchProvider.provider_id)
        self.assertEqual(result.claims, ())

    def test_rejects_empty_query(self):
        router = ResourceRouter(providers=())
        with self.assertRaises(ValueError):
            run_research_query(router, "   ")

    def test_digest_is_deterministic_and_sensitive_to_project_id(self):
        router = ResourceRouter(providers=())
        first = run_research_query(router, "buyers", project_id="PRJ-FAL-01")
        second = run_research_query(router, "buyers", project_id="PRJ-FAL-01")
        self.assertEqual(first.digest, second.digest)
        third = run_research_query(router, "buyers", project_id="PRJ-HYD-01")
        self.assertNotEqual(first.digest, third.digest)


class SearchProviderBenchmarkTests(unittest.TestCase):
    def test_valid_benchmark_passes(self):
        benchmark().validate()

    def test_rejects_out_of_range_rate(self):
        with self.assertRaises(ValueError):
            benchmark(coverage=1.4).validate()

    def test_rejects_unknown_decision(self):
        with self.assertRaises(ValueError):
            benchmark(decision="INSTALL_IMMEDIATELY").validate()

    def test_rejects_sample_size_below_one(self):
        with self.assertRaises(ValueError):
            benchmark(sample_size=0).validate()

    def test_keep_or_connect_requires_low_hallucination_rate(self):
        with self.assertRaisesRegex(ValueError, "decision_inconsistent_with_hallucination_rate"):
            benchmark(decision="KEEP", hallucination_rate=0.4).validate()

    def test_build_or_defer_may_have_high_hallucination_rate(self):
        benchmark(decision="DEFER", hallucination_rate=0.4).validate()


class SearchProviderRecordTests(unittest.TestCase):
    def test_unverified_provider_defaults_to_discovery_only(self):
        record = search_provider_record("candidate-x")
        self.assertEqual(record.authority, "DISCOVERY_ONLY")
        self.assertFalse(record.production_approved)
        self.assertIn("search", record.capabilities)

    def test_verified_provider_gets_official_authority(self):
        record = search_provider_record("candidate-x", policy_verified=True)
        self.assertEqual(record.authority, "OFFICIAL_DOCS_VERIFIED")


if __name__ == "__main__":
    unittest.main()
