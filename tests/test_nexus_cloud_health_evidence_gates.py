"""Regression checks: synthetic cloud CI is not persistent deployment proof."""
import unittest
from dataclasses import replace

from nexus_lab_health import LabHealth, evaluate_lab_health, self_test
from nexus_windows_lab_readiness import WindowsLabReadiness, readiness_errors


class CloudEvidenceGatesTests(unittest.TestCase):
    def test_synthetic_self_test_never_claims_deployment(self):
        report = self_test()
        self.assertTrue(report["ci_checks_passed"])
        self.assertFalse(report["local_install_verified"])
        self.assertFalse(report["persistent_service_verified"])
        self.assertFalse(report["production_ready"])

    def test_failure_injection_blocks_ci_evidence(self):
        for mapping, readiness in [(False, True), (True, False), (False, False)]:
            with self.subTest(mapping=mapping, readiness=readiness):
                report = evaluate_lab_health(LabHealth(mapping, readiness))
                self.assertFalse(report["ci_checks_passed"])
                self.assertFalse(report["production_ready"])

    def test_non_boolean_evidence_is_rejected(self):
        for invalid in [None, 1, "true", []]:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    evaluate_lab_health(LabHealth(invalid, True))

    def test_every_windows_gate_has_independent_failure(self):
        fields = tuple(WindowsLabReadiness.__dataclass_fields__)
        self.assertEqual(len(fields), 10)
        all_true = WindowsLabReadiness(**{key: True for key in fields})
        self.assertEqual(readiness_errors(all_true), ())
        for field in fields:
            with self.subTest(field=field):
                failed = replace(all_true, **{field: False})
                self.assertEqual(len(readiness_errors(failed)), 1)

    def test_windows_evidence_rejects_non_boolean_values(self):
        self.assertEqual(
            readiness_errors(WindowsLabReadiness(exact_host_approval="yes")),
            ("invalid_readiness_evidence",),
        )


if __name__ == "__main__":
    unittest.main()
