from __future__ import annotations

import unittest

from decision_engine import DecisionOption, rank_options
from prompt_contract import INSTRUCTIONS, REQUIRED_OUTPUT_KEYS, validate_prompt_contract


class PromptV2Tests(unittest.TestCase):
    def test_contract_contains_every_required_output(self):
        self.assertEqual(validate_prompt_contract(), ())
        for key in REQUIRED_OUTPUT_KEYS:
            self.assertIn(key, INSTRUCTIONS)

    def test_guardrails_are_explicit(self):
        for phrase in ("Heat Treatment remains HOLD", "Boyu is excluded", "Apollo is AUTH_BROKEN",
                       "UNKNOWN never becomes PASS", "research approval never authorizes outreach"):
            self.assertIn(phrase, INSTRUCTIONS)

    def test_high_value_evidenced_reversible_option_wins(self):
        ranked = rank_options((
            DecisionOption("verified_read_only_research", 5, 5, 5, 4, 5, 1, 1),
            DecisionOption("speculative_outreach", 4, 3, 1, 4, 1, 2, 5),
        ))
        self.assertEqual(ranked[0].option_id, "verified_read_only_research")
        self.assertEqual(ranked[0].disposition, "candidate_next_action")
        self.assertEqual(ranked[1].disposition, "collect_evidence_or_review")

    def test_blocked_option_never_becomes_next_action(self):
        ranked = rank_options((DecisionOption("boyu_outreach", 5, 5, 5, 5, 5, 0, 0, blocked=True),))
        self.assertEqual(ranked[0].disposition, "blocked")

    def test_duplicate_options_fail_closed(self):
        item = DecisionOption("same", 1, 1, 1, 1, 1, 1, 1)
        with self.assertRaisesRegex(ValueError, "duplicate_option_id"):
            rank_options((item, item))


if __name__ == "__main__":
    unittest.main()
