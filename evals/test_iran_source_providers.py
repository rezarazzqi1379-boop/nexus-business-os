from __future__ import annotations

import unittest

from iran_source_providers import (
    IRAN_SOURCE_FAMILIES,
    PROVIDER_INTERFACE_STATUSES,
    IranSourceIntegrationStatus,
    NullIranSourceAdapter,
    build_null_iran_source_registry,
    iran_source_integration_report,
)
from research_evidence import ResearchQueryResult, run_research_query, search_provider_record
from nexus_brain.resource_router import ResourceRouter


def status(**overrides) -> IranSourceIntegrationStatus:
    values = dict(
        source_family="IRICA_CUSTOMS",
        intended_commercial_use="use",
        provider_interface_status="INTERFACE_READY",
        fixture_tested=True,
        live_access_attempted=False,
        live_read_verified=False,
        limitations="none evaluated",
        dependency=None,
        next_integration_step="do the next thing",
    )
    values.update(overrides)
    return IranSourceIntegrationStatus(**values)


class NullIranSourceAdapterTests(unittest.TestCase):
    def test_returns_no_results_for_every_family(self):
        for family in IRAN_SOURCE_FAMILIES:
            adapter = NullIranSourceAdapter(source_family=family)
            self.assertEqual(adapter.search("anything", max_results=5), ())

    def test_provider_id_is_auto_derived_from_family(self):
        adapter = NullIranSourceAdapter(source_family="B2B_MARKETPLACE")
        self.assertEqual(adapter.provider_id, "null-b2b_marketplace")

    def test_explicit_provider_id_is_preserved(self):
        adapter = NullIranSourceAdapter(source_family="B2B_MARKETPLACE", provider_id="custom-id")
        self.assertEqual(adapter.provider_id, "custom-id")

    def test_invalid_source_family_is_rejected(self):
        with self.assertRaises(ValueError):
            NullIranSourceAdapter(source_family="NOT_A_REAL_FAMILY")


class BuildNullIranSourceRegistryTests(unittest.TestCase):
    def test_registry_has_exactly_one_entry_per_family(self):
        registry = build_null_iran_source_registry()
        self.assertEqual({a.source_family for a in registry.values()}, IRAN_SOURCE_FAMILIES)
        self.assertEqual(len(registry), len(IRAN_SOURCE_FAMILIES))

    def test_registry_keys_match_each_adapters_own_provider_id(self):
        registry = build_null_iran_source_registry()
        for key, adapter in registry.items():
            self.assertEqual(key, adapter.provider_id)

    def test_every_registry_entry_is_a_no_op(self):
        registry = build_null_iran_source_registry()
        for adapter in registry.values():
            self.assertEqual(adapter.search("q", max_results=3), ())


class RegistryWiresIntoRunResearchQueryTests(unittest.TestCase):
    """Proves the Null Iran adapters slot into the existing provider-routing mechanism
    end-to-end -- no live network call is made anywhere in this test, and none is possible:
    NullIranSourceAdapter.search() is a hardcoded no-op.
    """

    def test_a_null_iran_adapter_can_be_routed_and_called_via_run_research_query(self):
        registry = build_null_iran_source_registry()
        provider_id = "null-chamber_of_commerce"
        self.assertIn(provider_id, registry)
        record = search_provider_record(provider_id, production_approved=True, policy_verified=True)
        router = ResourceRouter(providers=(record,))
        result = run_research_query(router, "example query", providers=registry)
        self.assertIsInstance(result, ResearchQueryResult)
        self.assertTrue(result.provider_available)
        self.assertEqual(result.provider_id, provider_id)
        self.assertEqual(result.claims, ())


class IranSourceIntegrationStatusTests(unittest.TestCase):
    def test_valid_row_passes(self):
        status().validate()

    def test_invalid_source_family_is_rejected(self):
        with self.assertRaises(ValueError):
            status(source_family="NOT_A_REAL_FAMILY").validate()

    def test_invalid_provider_interface_status_is_rejected(self):
        with self.assertRaises(ValueError):
            status(provider_interface_status="MADE_UP_STATUS").validate()

    def test_live_read_verified_without_attempt_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "live_read_verified_requires_live_access_attempted"):
            status(live_read_verified=True, live_access_attempted=False).validate()

    def test_live_read_verified_true_requires_matching_status(self):
        with self.assertRaisesRegex(ValueError, "live_read_verified_flag_inconsistent_with_status"):
            status(live_read_verified=True, live_access_attempted=True,
                   provider_interface_status="INTERFACE_READY").validate()

    def test_live_read_verified_with_matching_status_and_attempt_is_accepted(self):
        status(live_read_verified=True, live_access_attempted=True,
               provider_interface_status="LIVE_READ_VERIFIED").validate()

    def test_blank_required_text_fields_are_rejected(self):
        for field_name in ("intended_commercial_use", "limitations", "next_integration_step"):
            with self.assertRaises(ValueError):
                status(**{field_name: "   "}).validate()


class IranSourceIntegrationReportTests(unittest.TestCase):
    def test_report_covers_every_known_family_exactly_once(self):
        report = iran_source_integration_report()
        families = [row.source_family for row in report]
        self.assertEqual(set(families), IRAN_SOURCE_FAMILIES)
        self.assertEqual(len(families), len(set(families)))

    def test_every_row_validates(self):
        for row in iran_source_integration_report():
            row.validate()  # must not raise

    def test_no_row_currently_claims_a_verified_live_read(self):
        # Honest maturity claim as of this slice: interface-ready and fixture-tested only.
        for row in iran_source_integration_report():
            self.assertFalse(row.live_read_verified)
            self.assertFalse(row.live_access_attempted)
            self.assertNotEqual(row.provider_interface_status, "LIVE_READ_VERIFIED")

    def test_every_row_is_fixture_tested(self):
        for row in iran_source_integration_report():
            self.assertTrue(row.fixture_tested)

    def test_every_status_value_used_is_a_recognized_status(self):
        for row in iran_source_integration_report():
            self.assertIn(row.provider_interface_status, PROVIDER_INTERFACE_STATUSES)


if __name__ == "__main__":
    unittest.main()
