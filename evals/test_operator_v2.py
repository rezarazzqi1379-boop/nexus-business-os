from __future__ import annotations
import unittest
from decision_engine import DecisionOption, rank_options
from prompt_contract import INSTRUCTIONS, REQUIRED_OUTPUT_KEYS, validate_prompt_contract, prompt_contains_project_dynamic_facts

class PromptV3Tests(unittest.TestCase):
    def test_contract_contains_every_required_output(self):
        self.assertEqual(validate_prompt_contract(), ())
        for key in REQUIRED_OUTPUT_KEYS:self.assertIn(key,INSTRUCTIONS)

    def test_global_contract_recovers_authority_instead_of_baking_project_facts(self):
        self.assertIn("Recover the current Source Registry",INSTRUCTIONS)
        self.assertIn("relevant canonical project master",INSTRUCTIONS)
        self.assertIn("dynamic facts live",INSTRUCTIONS)
        self.assertIn("UNKNOWN never becomes PASS",INSTRUCTIONS)
        self.assertFalse(prompt_contains_project_dynamic_facts())

    def test_project_specific_legacy_literals_are_not_global_authority(self):
        for phrase in ("Heat Treatment remains HOLD","Boyu is excluded","Apollo is AUTH_BROKEN","120 MPa","40-60 pipes/minute"):
            self.assertNotIn(phrase,INSTRUCTIONS)

    def test_external_action_gate_is_explicit(self):
        self.assertIn("exact approval",INSTRUCTIONS)
        self.assertIn("External capabilities are sandboxed",INSTRUCTIONS)

    def test_high_value_evidenced_reversible_option_wins(self):
        ranked=rank_options((
            DecisionOption("verified_read_only_research",5,5,5,4,5,1,1),
            DecisionOption("speculative_outreach",4,3,1,4,1,2,5),
        ))
        self.assertEqual(ranked[0].option_id,"verified_read_only_research")
        self.assertEqual(ranked[0].disposition,"candidate_next_action")
        self.assertEqual(ranked[1].disposition,"collect_evidence_or_review")

    def test_blocked_option_never_becomes_next_action(self):
        ranked=rank_options((DecisionOption("blocked_outreach",5,5,5,5,5,0,0,blocked=True),))
        self.assertEqual(ranked[0].disposition,"blocked")

    def test_duplicate_options_fail_closed(self):
        item=DecisionOption("same",1,1,1,1,1,1,1)
        with self.assertRaisesRegex(ValueError,"duplicate_option_id"):rank_options((item,item))

if __name__=="__main__":unittest.main()
