from __future__ import annotations

import unittest

from runner_registry import OPENWORKER, OPENCODE_SHADOW, CapabilityRisk, RunnerManifest, RunnerStatus, WorkPacket, activation_plan, validate_runner_packet


class RunnerRegistryTests(unittest.TestCase):
    def packet(self, **changes):
        values = dict(packet_id="packet-001", project_id="can_forming", objective="Summarize verified supplier evidence", capability=CapabilityRisk.READ, workspace_subpath="PROJECTS/can_forming", inputs={"source_refs": ["gmail:message-123"]})
        values.update(changes)
        return WorkPacket(**values)

    def test_openworker_is_experimental_and_fail_closed(self):
        self.assertEqual(OPENWORKER.status, RunnerStatus.EXPERIMENTAL)
        self.assertFalse(OPENWORKER.signed_binary)
        self.assertEqual(OPENWORKER.allowed_capabilities, (CapabilityRisk.READ,))

    def test_read_packet_can_only_prepare(self):
        result = validate_runner_packet(self.packet())
        self.assertEqual(result["disposition"], "prepare_only")
        self.assertFalse(result["external_action_authorized"])
        self.assertTrue(result["nexus_approval_remains_authoritative"])
        self.assertFalse(result["runner_is_authority"])

    def test_write_exec_and_external_are_blocked_for_openworker(self):
        for capability in (CapabilityRisk.WRITE_LOCAL, CapabilityRisk.EXEC, CapabilityRisk.EXTERNAL):
            with self.assertRaisesRegex(ValueError, "runner_capability_not_allowed"):
                validate_runner_packet(self.packet(capability=capability))

    def test_nexus_approval_cannot_be_delegated_to_runner(self):
        with self.assertRaisesRegex(ValueError, "approval_delegation_forbidden"):
            validate_runner_packet(self.packet(approval_id="approval-123"))

    def test_secret_material_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "secret_material_forbidden"):
            validate_runner_packet(self.packet(inputs={"api_key": "sk-1234567890abcdefghijklmnop"}))

    def test_workspace_escape_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "workspace_scope_escape"):
            validate_runner_packet(self.packet(workspace_subpath="../secrets"))

    def test_blocked_runner_cannot_receive_read_packet(self):
        blocked = RunnerManifest("unsafe", "1", RunnerStatus.BLOCKED, False, False, True, ("blocked",))
        with self.assertRaisesRegex(ValueError, "runner_blocked"):
            validate_runner_packet(self.packet(), blocked)

    def test_mcp_baseline_is_disabled_and_read_only(self):
        plan = activation_plan()
        self.assertEqual(len(plan), 12)
        self.assertTrue(all(not row["enabled"] for row in plan))
        self.assertTrue(all(row["initial_scope"] == "read_only" for row in plan))

    def test_opencode_is_experimental_not_authority(self):
        self.assertEqual(OPENCODE_SHADOW.status, RunnerStatus.EXPERIMENTAL)
        self.assertTrue(OPENCODE_SHADOW.sandbox_required)
        self.assertFalse(OPENCODE_SHADOW.network_allowed)
        self.assertFalse(OPENCODE_SHADOW.can_receive_secrets)
        self.assertNotIn(CapabilityRisk.EXTERNAL, OPENCODE_SHADOW.allowed_capabilities)

    def test_opencode_can_write_or_exec_only_inside_sandbox(self):
        for capability in (CapabilityRisk.WRITE_LOCAL, CapabilityRisk.EXEC):
            with self.assertRaisesRegex(ValueError, "sandbox_scope_required"):
                validate_runner_packet(
                    self.packet(capability=capability, workspace_subpath="PROJECTS/can_forming"),
                    OPENCODE_SHADOW,
                )
            result = validate_runner_packet(
                self.packet(capability=capability, workspace_subpath="SANDBOX/can_forming/task-001"),
                OPENCODE_SHADOW,
            )
            self.assertEqual(result["disposition"], "sandbox_only")
            self.assertFalse(result["network_authorized"])
            self.assertFalse(result["external_action_authorized"])

    def test_opencode_network_and_external_capability_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "runner_network_not_allowed"):
            validate_runner_packet(
                self.packet(workspace_subpath="SANDBOX/can_forming", inputs={"network_enabled": True}),
                OPENCODE_SHADOW,
            )
        with self.assertRaisesRegex(ValueError, "runner_capability_not_allowed"):
            validate_runner_packet(
                self.packet(capability=CapabilityRisk.EXTERNAL, workspace_subpath="SANDBOX/can_forming"),
                OPENCODE_SHADOW,
            )

    def test_opencode_cannot_receive_approval_or_secret_access_marker(self):
        with self.assertRaisesRegex(ValueError, "approval_delegation_forbidden"):
            validate_runner_packet(
                self.packet(workspace_subpath="SANDBOX/can_forming", approval_id="approval-001"),
                OPENCODE_SHADOW,
            )
        with self.assertRaisesRegex(ValueError, "runner_secret_access_not_allowed"):
            validate_runner_packet(
                self.packet(workspace_subpath="SANDBOX/can_forming", inputs={"contains_secrets": True}),
                OPENCODE_SHADOW,
            )


if __name__ == "__main__":
    unittest.main()
