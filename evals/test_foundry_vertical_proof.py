from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from foundry_vertical_proof import run_proof


def complete_payload():
    heat = {
        "equipment": {"furnace_id": "f1"}, "chemistry": {"sample": "lab:1"},
        "charge_and_additions": [{"material": "recorded"}],
        "thermal_timeline": [{"value": 1, "unit": "degC", "measured_at": "2026-01-01T00:00:00Z",
                              "source_locator": "historian:1", "uncertainty": 1}],
        "casting": {"method": "recorded"}, "quality_results": [{"result": "recorded"}],
        "maintenance_deviations": [{"status": "none_recorded"}],
        "operator_observations": [{"status": "interviewed"}],
        "raw_evidence": [{"locator": "file:record"}],
    }
    return {
        "project_id": "steel_ingot_pilot",
        "product": {"form": "ingot", "grade": "example", "acceptance_standard": "example"},
        "production_route": {"route_id": "route_1"},
        "heats": [dict(heat, heat_id="heat_good", outcome="ACCEPTABLE"),
                  dict(heat, heat_id="heat_bad", outcome="DEFECTIVE")],
    }


class FoundryVerticalProofTests(unittest.TestCase):
    def test_incomplete_input_fails_safe_and_preserves_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            result = run_proof({"project_id": "steel_ingot_pilot"}, Path(temp),
                               "2026-09-08T00:00:00+00:00")
            self.assertEqual(result["status"], "READY_FOR_FACTORY_DATA")
            self.assertIn("product", result["missing_fields"])
            self.assertIn("heats.requires_exactly_two_historical_records", result["missing_fields"])
            self.assertEqual(result["proof_stage"], "PHASE_0_PREFLIGHT")
            self.assertTrue(result["chain_valid"])
            self.assertTrue(Path(result["snapshot"]).exists())

    def test_complete_input_advances_only_to_bounded_analysis(self):
        payload = complete_payload()
        with tempfile.TemporaryDirectory() as temp:
            result = run_proof(payload, Path(temp), "2026-09-08T00:00:00+00:00")
            self.assertEqual(result["status"], "READY_FOR_RETROSPECTIVE_ANALYSIS")
            self.assertIn("equipment control", result["prohibited"])

    def test_truthy_placeholder_does_not_establish_readiness(self):
        payload = complete_payload()
        payload["heats"][0]["thermal_timeline"] = [{"value": "measured"}]
        with tempfile.TemporaryDirectory() as temp:
            result = run_proof(payload, Path(temp), "2026-09-08T00:00:00+00:00")
            self.assertIn("heats[0].thermal_timeline.measurement_contract", result["missing_fields"])


if __name__ == "__main__":
    unittest.main()
