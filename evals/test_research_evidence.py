from __future__ import annotations

import unittest
from dataclasses import dataclass

import research_evidence as re_module
from contracts import EvidenceClass
from research_evidence import (
    DEFAULT_SEARCH_BENCHMARK_POLICY,
    EvidenceClaim,
    NullSearchProvider,
    ResearchQueryResult,
    SearchBenchmarkPolicy,
    SearchProviderBenchmark,
    SearchResult,
    default_search_providers,
    run_research_query,
    search_provider_record,
)
from nexus_brain.resource_router import ResourceRouter

UTC_NOW = "2026-09-03T12:00:00+00:00"


@dataclass(frozen=True)
class FakeSearchProvider:
    """A minimal provider used only in tests, to prove injection works without editing the module."""

    provider_id: str = "fake-search-v1"
    hits: tuple[SearchResult, ...] = (
        SearchResult(title="Fake Source", url="https://example.invalid/fake", snippet="a fake finding"),
    )

    def search(self, query: str, *, max_results: int) -> tuple[SearchResult, ...]:
        return self.hits[:max_results]


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


def policy(**changes) -> SearchBenchmarkPolicy:
    values = dict(
        policy_version="test-policy-v1",
        min_coverage=0.6,
        min_citation_accuracy=0.8,
        min_source_quality=0.6,
        max_hallucination_rate=0.05,
        min_sample_size=20,
    )
    values.update(changes)
    return SearchBenchmarkPolicy(**values)


class NullSearchProviderTests(unittest.TestCase):
    def test_always_returns_empty_and_never_raises(self):
        provider = NullSearchProvider()
        self.assertEqual(provider.search("anything", max_results=5), ())


class SearchResultValidationTests(unittest.TestCase):
    def test_valid_result_passes(self):
        SearchResult(title="T", url="https://example.invalid/x", snippet="s").validate()

    def test_rejects_empty_title(self):
        with self.assertRaisesRegex(ValueError, "invalid_search_result_title"):
            SearchResult(title="   ", url="https://example.invalid/x", snippet="s").validate()

    def test_rejects_empty_snippet(self):
        with self.assertRaisesRegex(ValueError, "invalid_search_result_snippet"):
            SearchResult(title="T", url="https://example.invalid/x", snippet="").validate()

    def test_rejects_non_http_url(self):
        with self.assertRaisesRegex(ValueError, "invalid_search_result_url"):
            SearchResult(title="T", url="ftp://example.invalid/x", snippet="s").validate()

    def test_rejects_unparseable_published_at(self):
        with self.assertRaises(ValueError):
            SearchResult(title="T", url="https://example.invalid/x", snippet="s",
                        published_at="not-a-date").validate()

    def test_accepts_valid_published_at(self):
        SearchResult(title="T", url="https://example.invalid/x", snippet="s",
                    published_at=UTC_NOW).validate()


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

    def test_non_numeric_confidence_raises_value_error_not_type_error(self):
        try:
            evidence_claim(confidence="high").validate()
            self.fail("expected ValueError")
        except ValueError:
            pass
        except TypeError:
            self.fail("non-numeric confidence must raise ValueError, not TypeError")

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

    def test_unknown_or_made_up_lane_id_is_not_rejected(self):
        """This module is lane-neutral transport: it does not know or enforce any lane taxonomy."""
        claim = evidence_claim(project_id="anything-goes-123", lane_id="totally-made-up-lane")
        claim.validate()
        self.assertEqual(claim.lane_id, "totally-made-up-lane")


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

    def test_invalid_search_result_is_rejected_before_becoming_a_claim(self):
        bad_result = SearchResult(title="", url="https://example.invalid/a", snippet="a claim")
        with self.assertRaises(ValueError):
            re_module._claim_from_search_result(bad_result, query="q", retrieved_at=UTC_NOW,
                                                project_id=None, lane_id=None)


class DefaultSearchProvidersTests(unittest.TestCase):
    def test_default_registry_contains_only_null_provider(self):
        registry = default_search_providers()
        self.assertEqual(set(registry), {NullSearchProvider.provider_id})

    def test_default_registry_is_a_fresh_dict_each_call(self):
        first, second = default_search_providers(), default_search_providers()
        self.assertIsNot(first, second)
        first["mutated"] = NullSearchProvider()
        self.assertNotIn("mutated", second)


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

    def test_injected_fake_provider_is_routed_and_called(self):
        fake = FakeSearchProvider()
        record = search_provider_record(fake.provider_id, production_approved=True, policy_verified=True)
        router = ResourceRouter(providers=(record,))
        result = run_research_query(router, "ferrosilicon buyers", providers={fake.provider_id: fake})
        self.assertTrue(result.provider_available)
        self.assertEqual(result.provider_id, fake.provider_id)
        self.assertEqual(len(result.claims), 1)
        self.assertEqual(result.claims[0].source_name, "Fake Source")
        self.assertEqual(result.claims[0].evidence_class, EvidenceClass.CLAIM)

    def test_injected_provider_preserves_project_and_lane_ids_unchanged(self):
        fake = FakeSearchProvider()
        record = search_provider_record(fake.provider_id, production_approved=True, policy_verified=True)
        router = ResourceRouter(providers=(record,))
        result = run_research_query(router, "q", providers={fake.provider_id: fake},
                                    project_id="PRJ-FAL-01", lane_id="totally-unvalidated-lane")
        self.assertEqual(result.claims[0].project_id, "PRJ-FAL-01")
        self.assertEqual(result.claims[0].lane_id, "totally-unvalidated-lane")

    def test_default_registry_used_when_providers_omitted(self):
        record = search_provider_record(NullSearchProvider.provider_id, production_approved=True,
                                        policy_verified=True)
        router = ResourceRouter(providers=(record,))
        result = run_research_query(router, "q")  # no providers= kwarg -> default registry
        self.assertTrue(result.provider_available)
        self.assertEqual(result.provider_id, NullSearchProvider.provider_id)

    def test_registry_key_mismatched_with_provider_id_is_rejected(self):
        mislabeled = NullSearchProvider()  # its .provider_id is "null-search-provider"
        record = search_provider_record("mislabeled-key", production_approved=True, policy_verified=True)
        router = ResourceRouter(providers=(record,))
        with self.assertRaisesRegex(ValueError, "provider_registry_id_mismatch"):
            run_research_query(router, "q", providers={"mislabeled-key": mislabeled})


class SearchBenchmarkPolicyTests(unittest.TestCase):
    def test_valid_policy_passes(self):
        policy().validate()

    def test_rejects_empty_policy_version(self):
        with self.assertRaises(ValueError):
            policy(policy_version="  ").validate()

    def test_rejects_out_of_range_threshold(self):
        with self.assertRaises(ValueError):
            policy(min_coverage=1.4).validate()

    def test_rejects_sample_size_below_one(self):
        with self.assertRaises(ValueError):
            policy(min_sample_size=0).validate()

    def test_default_policy_has_a_version(self):
        self.assertEqual(DEFAULT_SEARCH_BENCHMARK_POLICY.policy_version, "nexus.search-benchmark-policy.v1")


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

    def test_non_numeric_rate_raises_value_error_not_type_error(self):
        try:
            benchmark(coverage="high").validate()
            self.fail("expected ValueError")
        except ValueError:
            pass
        except TypeError:
            self.fail("non-numeric coverage must raise ValueError, not TypeError")

    def test_keep_requires_every_mandatory_threshold_coverage(self):
        with self.assertRaisesRegex(ValueError, "coverage_below_policy"):
            benchmark(decision="KEEP", coverage=0.1).validate()

    def test_keep_requires_every_mandatory_threshold_citation_accuracy(self):
        with self.assertRaisesRegex(ValueError, "citation_accuracy_below_policy"):
            benchmark(decision="KEEP", citation_accuracy=0.1).validate()

    def test_keep_requires_every_mandatory_threshold_source_quality(self):
        with self.assertRaisesRegex(ValueError, "source_quality_below_policy"):
            benchmark(decision="KEEP", source_quality=0.1).validate()

    def test_keep_requires_every_mandatory_threshold_sample_size(self):
        with self.assertRaisesRegex(ValueError, "sample_size_below_policy"):
            benchmark(decision="KEEP", sample_size=2).validate()

    def test_connect_requires_low_hallucination_rate(self):
        with self.assertRaisesRegex(ValueError, "hallucination_rate_above_policy"):
            benchmark(decision="CONNECT", hallucination_rate=0.4).validate()

    def test_build_or_defer_may_remain_below_every_threshold(self):
        benchmark(decision="DEFER", coverage=0.01, citation_accuracy=0.01, source_quality=0.01,
                 hallucination_rate=0.9, sample_size=1).validate()
        benchmark(decision="BUILD", coverage=0.01, citation_accuracy=0.01, source_quality=0.01,
                 hallucination_rate=0.9, sample_size=1).validate()
        benchmark(decision="REJECT", coverage=0.01, citation_accuracy=0.01, source_quality=0.01,
                 hallucination_rate=0.9, sample_size=1).validate()

    def test_custom_policy_can_be_stricter_or_looser_than_default(self):
        lenient = policy(min_coverage=0.05)
        benchmark(decision="KEEP", coverage=0.1).validate(lenient)
        strict = policy(min_coverage=0.99)
        with self.assertRaisesRegex(ValueError, "coverage_below_policy"):
            benchmark(decision="KEEP", coverage=0.9).validate(strict)

    def test_no_magic_thresholds_survive_from_earlier_hardcoded_version(self):
        # a benchmark passing the old single hardcoded hallucination check but failing on
        # coverage must still be rejected for KEEP -- proves coverage is actually enforced.
        with self.assertRaisesRegex(ValueError, "coverage_below_policy"):
            benchmark(decision="KEEP", hallucination_rate=0.01, coverage=0.2).validate()


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
