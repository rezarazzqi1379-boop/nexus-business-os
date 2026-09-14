import json
import unittest
from pathlib import Path

from rolling_mill_intake import AMBIGUOUS_CLAIM_IDS, POSITIVE_NUMERIC_PATHS, REQUIRED_PATHS, TRUE_PATHS, assess


TEMPLATE = Path(".nexus/expert_foundry/ROLLING_MILL_ENGINEERING_INTAKE.json")


class RollingMillIntakeTests(unittest.TestCase):
    def test_current_voice_claims_fail_closed(self):
        result = assess(json.loads(TEMPLATE.read_text(encoding="utf-8")))
        self.assertEqual(result.status, "READY_FOR_ENGINEER_INTERVIEW")
        self.assertEqual(set(result.unresolved_claims), set(AMBIGUOUS_CLAIM_IDS))
        self.assertFalse(result.calculation_allowed)
        self.assertFalse(result.operation_change_allowed)

    def test_placeholders_do_not_count_as_evidence(self):
        payload = {"project_id": "TBD"}
        result = assess(payload)
        self.assertIn("project_id", result.missing_paths)

    def test_complete_verified_contract_allows_calculation_not_operation(self):
        payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        for path in REQUIRED_PATHS:
            target = payload
            parts = path.split(".")
            for part in parts[:-1]:
                target = target.setdefault(part, {})
            if path in POSITIVE_NUMERIC_PATHS:
                target[parts[-1]] = 1
            elif path in TRUE_PATHS:
                target[parts[-1]] = True
            elif path in {"mill.layout", "process.pass_schedule"}:
                target[parts[-1]] = ["measured"]
            elif path == "product.input_billet.cross_section_mm":
                target[parts[-1]] = {"width": 150, "height": 150}
            elif path == "drive.gearbox.ratio":
                target[parts[-1]] = {"input": 10, "output": 1}
            else:
                target[parts[-1]] = "measured"
        for claim in payload["initial_claims"]:
            claim.update(meaning="verified meaning", unit="verified unit", verification_state="VERIFIED", evidence_locator="photo:nameplate")
        result = assess(payload)
        self.assertEqual(result.status, "READY_FOR_RETROSPECTIVE_CALCULATION")
        self.assertTrue(result.calculation_allowed)
        self.assertFalse(result.operation_change_allowed)

    def test_text_cannot_satisfy_numeric_or_safety_limits(self):
        payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        payload["drive"]["motor"]["rated_power_kw"] = "125"
        payload["safety"]["guards_verified"] = "yes"
        result = assess(payload)
        self.assertIn("drive.motor.rated_power_kw:positive_number_required", result.missing_paths)
        self.assertIn("safety.guards_verified:explicit_true_required", result.missing_paths)


if __name__ == "__main__":
    unittest.main()
