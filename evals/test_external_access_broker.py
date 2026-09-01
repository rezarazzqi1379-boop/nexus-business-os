import unittest

from external_access_broker import ExternalAccessBroker, Gate, ProviderManifest


class ExternalAccessBrokerTests(unittest.TestCase):
    def test_routine_free_signup_can_auto_plan(self):
        plan = ExternalAccessBroker().plan_signup("posthog")
        self.assertTrue(plan.allowed_automatically)
        self.assertEqual(plan.human_gates, ())

    def test_oauth_connect_surfaces_provider_handoff(self):
        plan = ExternalAccessBroker().plan_connect("n8n")
        self.assertIn(Gate.OAUTH_CONSENT, plan.human_gates)
        self.assertFalse(plan.allowed_automatically)

    def test_machine_only_provider_can_auto_plan(self):
        manifest = ProviderManifest("local", "http://localhost", "none", ())
        plan = ExternalAccessBroker([manifest]).plan_connect("local")
        self.assertTrue(plan.allowed_automatically)

    def test_fingerprint_changes_with_action(self):
        broker = ExternalAccessBroker()
        self.assertNotEqual(broker.plan_signup("n8n").approval_fingerprint, broker.plan_connect("n8n").approval_fingerprint)

    def test_unknown_provider_fails_closed(self):
        with self.assertRaises(KeyError):
            ExternalAccessBroker().plan_signup("unknown")

    def test_all_reel_tools_are_represented(self):
        providers = set(ExternalAccessBroker().providers())
        required = {"1password", "bitwarden", "deepl", "libretranslate", "intercom", "chatwoot", "loom", "obs", "mixpanel", "posthog", "typeform", "google_forms", "miro", "excalidraw", "otter", "granola", "airtable", "baserow", "figma", "penpot", "zapier", "n8n", "dropbox", "nextcloud", "notion", "obsidian", "calendly", "cal_diy"}
        self.assertTrue(required.issubset(providers))

    def test_local_tools_do_not_invent_human_gates(self):
        broker = ExternalAccessBroker()
        self.assertTrue(broker.plan_connect("obs").allowed_automatically)
        self.assertTrue(broker.plan_connect("excalidraw").allowed_automatically)
        self.assertTrue(broker.plan_connect("obsidian").allowed_automatically)

    def test_google_forms_requires_oauth_handoff(self):
        self.assertIn(Gate.OAUTH_CONSENT, ExternalAccessBroker().plan_connect("google_forms").human_gates)

    def test_payment_always_requires_explicit_approval(self):
        plan = ExternalAccessBroker().plan_payment("posthog")
        self.assertFalse(plan.allowed_automatically)
        self.assertEqual(plan.human_gates, (Gate.PAYMENT,))

    def test_material_commitment_always_requires_explicit_approval(self):
        plan = ExternalAccessBroker().plan_material_commitment("chatwoot")
        self.assertFalse(plan.allowed_automatically)
        self.assertEqual(plan.human_gates, (Gate.MATERIAL_COMMITMENT,))

    def test_n8n_is_orchestration_not_authority(self):
        self.assertEqual(ExternalAccessBroker().manifest("n8n").nexus_role, "orchestration")

    def test_baserow_is_not_promoted_to_canonical_database(self):
        self.assertEqual(ExternalAccessBroker().manifest("baserow").nexus_role, "optional_database_ui")


if __name__ == "__main__":
    unittest.main()
