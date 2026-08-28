import unittest

from runner_registry import NEXUS_MCP_BASELINE, activation_plan, activation_waves


class CapabilityPortfolioTests(unittest.TestCase):
    def test_portfolio_expands_without_auto_activation(self):
        plan = activation_plan()
        self.assertEqual(len(plan), 12)
        self.assertTrue(all(not row["enabled"] for row in plan))
        self.assertTrue(all(row["initial_scope"] == "read_only" for row in plan))

    def test_each_tool_has_health_and_rollback_contract(self):
        for row in activation_plan():
            self.assertTrue(row["health_probe"])
            self.assertTrue(row["fallback"])
            self.assertEqual(row["approval_rule"], "nexus_exact_scope_gate_for_any_write")

    def test_paid_tool_is_delayed(self):
        waves = activation_waves()
        self.assertIn("apollo", waves["later_or_metered"])
        self.assertNotIn("apollo", waves["now_read_only"])

    def test_project_specific_tools_do_not_claim_global_scope(self):
        rows = {row["server_id"]: row for row in activation_plan()}
        self.assertEqual(rows["canva"]["project_scopes"], ["portfolio_platform"])
        self.assertEqual(rows["supabase"]["project_scopes"], ["portfolio_platform"])
        self.assertIn("hydrostatic_tester", rows["gmail"]["project_scopes"])

    def test_activation_waves_cover_every_candidate_once(self):
        waves = activation_waves()
        flattened = sum(waves.values(), [])
        self.assertEqual(len(flattened), len(set(flattened)))
        self.assertEqual(set(flattened), {item.server_id for item in NEXUS_MCP_BASELINE})


if __name__ == "__main__":
    unittest.main()
