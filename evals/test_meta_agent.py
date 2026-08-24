import unittest

from meta_agent import (
    Capability,
    CapabilityProfile,
    DEFAULT_CAPABILITY_PROFILES,
    Evidence,
    EvidenceKind,
    MetaAgent,
    Objective,
    Outcome,
    Risk,
)


class MetaAgentTests(unittest.TestCase):
    def setUp(self):
        self.agent = MetaAgent(DEFAULT_CAPABILITY_PROFILES)

    def test_fact_requires_source(self):
        with self.assertRaisesRegex(ValueError, "fact_requires_source"):
            self.agent.remember([Evidence("e1", "p1", "x", EvidenceKind.FACT, None, 1.0)])

    def test_memory_is_project_isolated(self):
        self.agent.remember(
            [
                Evidence("e1", "p1", "one", EvidenceKind.CLAIM, None, 0.5),
                Evidence("e2", "p2", "two", EvidenceKind.CLAIM, None, 0.5),
            ]
        )
        p1 = self.agent.plan(Objective("o1", "p1", "research", (Capability.RESEARCH,)))
        del self.agent.memory["e2"]
        p1_again = self.agent.plan(Objective("o1", "p1", "research", (Capability.RESEARCH,)))
        self.assertEqual(p1.evidence_digest, p1_again.evidence_digest)

    def test_collision_fails_closed(self):
        self.agent.remember([Evidence("e1", "p1", "one", EvidenceKind.CLAIM, None, 0.5)])
        with self.assertRaisesRegex(ValueError, "evidence_id_collision"):
            self.agent.remember([Evidence("e1", "p1", "changed", EvidenceKind.CLAIM, None, 0.5)])

    def test_best_admissible_tool_is_selected_deterministically(self):
        tools = DEFAULT_CAPABILITY_PROFILES + (
            CapabilityProfile(Capability.RESEARCH, "weak", "community", Risk.READ, 0.4, 0.8, 0.8),
        )
        plan = MetaAgent(tools).plan(Objective("o1", "p1", "research", (Capability.RESEARCH,)))
        self.assertEqual(plan.steps[0].tool_id, "authorized_web_research")

    def test_risk_ceiling_blocks_external_action(self):
        plan = self.agent.plan(Objective("o1", "p1", "send", (Capability.EXTERNAL_ACTION,), Risk.READ))
        self.assertEqual(plan.blocked, (Capability.EXTERNAL_ACTION,))
        self.assertFalse(plan.external_action_authorized)

    def test_external_profile_never_self_authorizes(self):
        plan = self.agent.plan(Objective("o1", "p1", "send", (Capability.EXTERNAL_ACTION,), Risk.EXTERNAL))
        self.assertEqual(plan.steps[0].tool_id, "human_approval_gate")
        self.assertFalse(plan.external_action_authorized)

    def test_duplicate_capability_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate_required_capability"):
            self.agent.plan(Objective("o1", "p1", "x", (Capability.RESEARCH, Capability.RESEARCH)))

    def test_improvement_never_auto_promotes(self):
        self.agent.record_outcome(Outcome("o1", False, {"accuracy": 0.5}, ("add_contradiction_check",)))
        proposal = self.agent.propose_improvement("o1")
        self.assertEqual(proposal["disposition"], "experiment_only")
        self.assertFalse(proposal["auto_promote"])

    def test_success_keeps_baseline(self):
        self.agent.record_outcome(Outcome("o1", True, {"accuracy": 1.0}))
        self.assertEqual(self.agent.propose_improvement("o1")["disposition"], "retain_baseline")


if __name__ == "__main__":
    unittest.main()
