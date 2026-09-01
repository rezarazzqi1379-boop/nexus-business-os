import unittest

from capability_mesh import (
    CapabilityMesh,
    CapabilityState,
    ProbeRecord,
    RouteRequest,
    live_probe_snapshot,
)


class CapabilityMeshTests(unittest.TestCase):
    def setUp(self):
        self.mesh = CapabilityMesh(live_probe_snapshot())

    def test_live_verified_provider_routes_read(self):
        decision = self.mesh.route(RouteRequest("PRJ-NXO-01", "read", ("observability",)))
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.providers, ("posthog",))

    def test_blocked_probe_is_not_routable(self):
        decision = self.mesh.route(RouteRequest("PRJ-NXO-01", "read", ("lead_discovery",)))
        self.assertFalse(decision.allowed)
        self.assertIn("missing_role", decision.reason)

    def test_write_requires_write_enabled(self):
        decision = self.mesh.route(RouteRequest("PRJ-NXO-01", "write", ("knowledge_ops",)))
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.approval_required)

    def test_production_requires_production_approved(self):
        decision = self.mesh.route(RouteRequest("PRJ-NXO-01", "deploy", ("observability",)))
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.approval_required)

    def test_payment_gate_precedes_routing(self):
        decision = self.mesh.route(RouteRequest("PRJ-NXO-01", "read", ("crm",), payment_required=True))
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.approval_required)
        self.assertEqual(decision.reason, "payment_or_material_commitment_gate")

    def test_material_commitment_gate_precedes_routing(self):
        decision = self.mesh.route(RouteRequest("PRJ-NXO-01", "read", ("crm",), material_commitment=True))
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.approval_required)

    def test_cross_project_transfer_denied(self):
        decision = self.mesh.route(RouteRequest(
            "PRJ-HYD-01", "read", ("knowledge_ops",),
            source_project_id="PRJ-HYD-01", target_project_id="PRJ-KCL-01"
        ))
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "cross_project_transfer_denied")

    def test_project_id_is_required(self):
        decision = self.mesh.route(RouteRequest("", "read", ("observability",)))
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "project_id_required")

    def test_blocked_provider_cannot_self_promote(self):
        with self.assertRaises(ValueError):
            self.mesh.promote("apollo", CapabilityState.WRITE_ENABLED)

    def test_state_regression_rejected(self):
        with self.assertRaises(ValueError):
            self.mesh.promote("posthog", CapabilityState.CONNECTED)

    def test_least_privileged_provider_selected(self):
        mesh = CapabilityMesh((
            ProbeRecord("a", CapabilityState.PRODUCTION_APPROVED, "research", "2026-09-02T00:00:00Z", "a"),
            ProbeRecord("b", CapabilityState.READ_VERIFIED, "research", "2026-09-02T00:00:00Z", "b"),
        ))
        decision = mesh.route(RouteRequest("PRJ-NXO-01", "read", ("research",)))
        self.assertEqual(decision.providers, ("b",))

    def test_mesh_keeps_adapters_as_capabilities_not_authority(self):
        roles = {record.role for record in live_probe_snapshot()}
        self.assertNotIn("canonical_authority", roles)


if __name__ == "__main__":
    unittest.main()
