import unittest

from provider_resolution import ControlGate, ProviderResolutionPlanner, ResolutionMode


class ProviderResolutionTests(unittest.TestCase):
    def setUp(self):
        self.planner = ProviderResolutionPlanner()

    def test_healthy_connector_wins(self):
        decision = self.planner.resolve("posthog", connector_healthy=True)
        self.assertTrue(decision.can_continue_machine_side)
        self.assertEqual(decision.mode, ResolutionMode.EXISTING_CONNECTOR)

    def test_self_host_preferred_when_target_exists(self):
        decision = self.planner.resolve("n8n", deployment_target=True)
        self.assertTrue(decision.can_continue_machine_side)
        self.assertEqual(decision.mode, ResolutionMode.SELF_HOST)

    def test_self_host_waits_for_deployment_target(self):
        decision = self.planner.resolve("nextcloud", deployment_target=False)
        self.assertFalse(decision.can_continue_machine_side)
        self.assertEqual(decision.human_gate, ControlGate.PRODUCTION)

    def test_granola_surfaces_verification_handoff(self):
        decision = self.planner.resolve("granola")
        self.assertFalse(decision.can_continue_machine_side)
        self.assertEqual(decision.mode, ResolutionMode.HUMAN_HANDOFF)
        self.assertEqual(decision.human_gate, ControlGate.EMAIL_VERIFICATION)

    def test_apollo_invalid_connector_does_not_self_promote(self):
        decision = self.planner.resolve("apollo", connector_healthy=False)
        self.assertFalse(decision.can_continue_machine_side)
        self.assertEqual(decision.mode, ResolutionMode.HUMAN_HANDOFF)
        self.assertEqual(decision.human_gate, ControlGate.OAUTH)

    def test_unknown_provider_fails_closed(self):
        decision = self.planner.resolve("mystery")
        self.assertFalse(decision.can_continue_machine_side)
        self.assertEqual(decision.mode, ResolutionMode.BLOCKED)

    def test_batch_keeps_connected_and_selfhost_paths_distinct(self):
        decisions = self.planner.batch(("posthog", "n8n", "granola"), healthy_connectors=frozenset({"posthog"}), deployment_target=True)
        modes = {d.provider: d.mode for d in decisions}
        self.assertEqual(modes["posthog"], ResolutionMode.EXISTING_CONNECTOR)
        self.assertEqual(modes["n8n"], ResolutionMode.SELF_HOST)
        self.assertEqual(modes["granola"], ResolutionMode.HUMAN_HANDOFF)


if __name__ == "__main__":
    unittest.main()
