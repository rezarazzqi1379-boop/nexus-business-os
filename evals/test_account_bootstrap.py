import unittest

from account_bootstrap import AccountBootstrapPlanner, BootstrapState


class AccountBootstrapPlannerTests(unittest.TestCase):
    def setUp(self):
        self.planner = AccountBootstrapPlanner()

    def test_project_id_required(self):
        with self.assertRaises(ValueError):
            self.planner.plan("")

    def test_active_stack_contains_priority_tools(self):
        batch = self.planner.prioritized_active_stack("PRJ-NXO-01")
        providers = {item.provider for item in batch.items}
        required = {"bitwarden", "posthog", "n8n", "chatwoot", "nextcloud", "cal_diy", "libretranslate", "penpot"}
        self.assertTrue(required.issubset(providers))

    def test_local_tools_are_machine_ready(self):
        batch = self.planner.plan("PRJ-NXO-01", ("obs", "obsidian", "excalidraw"))
        self.assertTrue(all(item.state is BootstrapState.READY for item in batch.items))

    def test_oauth_tools_surface_handoff(self):
        batch = self.planner.plan("PRJ-NXO-01", ("n8n", "google_forms"))
        self.assertTrue(all(item.state is BootstrapState.HANDOFF_REQUIRED for item in batch.items))

    def test_comparison_only_tools_are_skipped(self):
        batch = self.planner.plan("PRJ-NXO-01", ("1password", "mixpanel", "zapier"))
        self.assertTrue(all(item.state is BootstrapState.SKIPPED for item in batch.items))

    def test_batch_separates_ready_and_handoffs(self):
        batch = self.planner.plan("PRJ-NXO-01", ("obs", "n8n"))
        self.assertEqual(tuple(item.provider for item in batch.ready), ("obs",))
        self.assertEqual(tuple(item.provider for item in batch.handoffs), ("n8n",))

    def test_planner_does_not_claim_execution(self):
        batch = self.planner.prioritized_active_stack("PRJ-NXO-01")
        reasons = {item.reason for item in batch.items}
        self.assertNotIn("connected", reasons)
        self.assertNotIn("account_created", reasons)


if __name__ == "__main__":
    unittest.main()
