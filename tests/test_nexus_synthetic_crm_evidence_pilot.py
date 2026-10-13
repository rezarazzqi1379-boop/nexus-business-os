"""Synthetic CRM pilot acceptance and regression tests."""
import unittest

from nexus_synthetic_crm_evidence_pilot import (
    ProjectBoundaryError, SyntheticOpportunity, synthetic_pilot,
)


class SyntheticCRMPilotTests(unittest.TestCase):
    def setUp(self):
        self.record = SyntheticOpportunity("SANDBOX", "ACCOUNT-1", "CONTACT-1", "OPP-1")

    def test_create_read_export_evidence_is_deterministic(self):
        a = synthetic_pilot([self.record], project_id="SANDBOX")
        b = synthetic_pilot([self.record], project_id="SANDBOX")
        self.assertEqual(a, b)
        self.assertEqual(a["record_count"], 1)
        self.assertEqual(a["records"][0]["account_id"], "ACCOUNT-1")
        self.assertEqual(len(a["evidence_sha256"]), 64)
        self.assertFalse(a["external_crm_installed"])
        self.assertFalse(a["live_write_authorized"])
        self.assertFalse(a["records"][0]["live_write_authorized"])

    def test_cross_project_isolation(self):
        with self.assertRaisesRegex(ProjectBoundaryError, "cross_project_record_blocked"):
            synthetic_pilot([self.record], project_id="PRJ-HYD-01-ENG")

    def test_duplicate_opportunity_blocked(self):
        with self.assertRaisesRegex(ValueError, "duplicate_opportunity_blocked"):
            synthetic_pilot([self.record, self.record], project_id="SANDBOX")

    def test_malformed_records_rejected(self):
        for bad in [None, {}, SyntheticOpportunity("SANDBOX", "", "C", "O")]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    synthetic_pilot([bad], project_id="SANDBOX")

    def test_invalid_project_rejected(self):
        for bad in ["", None, 42]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    synthetic_pilot([self.record], project_id=bad)

    def test_empty_input_is_explicit(self):
        report = synthetic_pilot([], project_id="SANDBOX")
        self.assertEqual(report["record_count"], 0)
        self.assertEqual(report["records"], [])


if __name__ == "__main__":
    unittest.main()
