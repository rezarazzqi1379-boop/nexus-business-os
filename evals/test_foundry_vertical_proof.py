from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from foundry_vertical_proof import REQUIRED_FACTORY_FIELDS, run_proof


class FoundryVerticalProofTests(unittest.TestCase):
    def test_incomplete_input_fails_safe_and_preserves_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            result = run_proof({"project_id": "steel_ingot_pilot"}, Path(temp),
                               "2026-09-08T00:00:00+00:00")
            self.assertEqual(result["status"], "READY_FOR_FACTORY_DATA")
            self.assertEqual(set(result["missing_fields"]), set(REQUIRED_FACTORY_FIELDS))
            self.assertTrue(result["chain_valid"])
            self.assertTrue(Path(result["snapshot"]).exists())

    def test_complete_input_advances_only_to_bounded_analysis(self):
        payload = {"project_id": "steel_ingot_pilot"}
        payload.update({field: "measured" for field in REQUIRED_FACTORY_FIELDS})
        with tempfile.TemporaryDirectory() as temp:
            result = run_proof(payload, Path(temp), "2026-09-08T00:00:00+00:00")
            self.assertEqual(result["status"], "READY_FOR_BOUNDED_ANALYSIS")
            self.assertIn("equipment control", result["prohibited"])


if __name__ == "__main__":
    unittest.main()
