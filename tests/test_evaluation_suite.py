import unittest

from nexus_core.evaluation_constitution import EvalCase, EvalObservation
from nexus_core.evaluation_suite import evaluate_suite


class EvaluationSuiteTests(unittest.TestCase):
    def _case(self, case_id="C1", project_id="P1"):
        return EvalCase(
            case_id=case_id,
            eval_class="CANONICAL",
            project_id=project_id,
            prompt="test",
            expected_rules=("rule-ok",),
            forbidden_rules=("rule-bad",),
            source_refs=("SRC:1",),
            frozen_version="0.1",
        )

    def _obs(self, case_id="C1", project_id="P1", satisfied=("rule-ok",), violated=(), source_refs=("SRC:1",), corrections=0):
        return EvalObservation(
            case_id=case_id,
            satisfied_rules=satisfied,
            violated_rules=violated,
            project_id=project_id,
            source_refs_used=source_refs,
            human_corrections=corrections,
        )

    def test_all_pass_only_reaches_adoption_gate_not_production(self):
        result = evaluate_suite("candidate-a", (self._case(),), (self._obs(),))
        self.assertTrue(result.promotable_to_adoption_gate)
        self.assertEqual(result.passed_cases, 1)
        self.assertIn("Adoption Gate only", result.reasons[0])

    def test_missing_case_observation_fails_closed(self):
        result = evaluate_suite("candidate-a", (self._case(),), ())
        self.assertFalse(result.promotable_to_adoption_gate)
        self.assertEqual(result.invalid_cases, 1)
        self.assertTrue(any("missing observations" in reason for reason in result.reasons))

    def test_cross_project_contamination_blocks_suite(self):
        result = evaluate_suite("candidate-a", (self._case(),), (self._obs(project_id="P2"),))
        self.assertFalse(result.promotable_to_adoption_gate)
        self.assertEqual(result.invalid_cases, 1)

    def test_forbidden_rule_blocks_suite(self):
        result = evaluate_suite(
            "candidate-a",
            (self._case(),),
            (self._obs(satisfied=("rule-ok", "rule-bad")),),
        )
        self.assertFalse(result.promotable_to_adoption_gate)
        self.assertEqual(result.failed_cases, 1)

    def test_unknown_observation_blocks_suite(self):
        result = evaluate_suite(
            "candidate-a",
            (self._case(),),
            (self._obs(), self._obs(case_id="UNKNOWN")),
        )
        self.assertFalse(result.promotable_to_adoption_gate)
        self.assertTrue(any("unknown cases" in reason for reason in result.reasons))

    def test_human_corrections_are_measured_not_hidden(self):
        result = evaluate_suite("candidate-a", (self._case(),), (self._obs(corrections=3),))
        self.assertEqual(result.total_human_corrections, 3)


if __name__ == "__main__":
    unittest.main()
