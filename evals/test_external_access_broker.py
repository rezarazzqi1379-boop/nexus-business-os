import unittest

from external_access_broker import ExternalAccessBroker, Gate, ProviderManifest


class ExternalAccessBrokerTests(unittest.TestCase):
    def test_signup_stops_at_terms_gate(self):
        plan = ExternalAccessBroker().plan_signup("posthog")
        self.assertFalse(plan.allowed_automatically)
        self.assertEqual(plan.human_gates, (Gate.TERMS,))

    def test_oauth_connect_is_gated(self):
        plan = ExternalAccessBroker().plan_connect("hubspot")
        self.assertIn(Gate.OAUTH_CONSENT, plan.human_gates)
        self.assertFalse(plan.allowed_automatically)

    def test_machine_only_provider_can_auto_plan(self):
        manifest = ProviderManifest("local", "http://localhost", "none", ())
        plan = ExternalAccessBroker([manifest]).plan_connect("local")
        self.assertTrue(plan.allowed_automatically)

    def test_fingerprint_changes_with_action(self):
        broker = ExternalAccessBroker()
        self.assertNotEqual(
            broker.plan_signup("n8n").approval_fingerprint,
            broker.plan_connect("n8n").approval_fingerprint,
        )

    def test_unknown_provider_fails_closed(self):
        with self.assertRaises(KeyError):
            ExternalAccessBroker().plan_signup("unknown")


if __name__ == "__main__":
    unittest.main()
