from __future__ import annotations

import unittest

from runner_registry import OPENWORKER, CapabilityRisk, RunnerManifest, RunnerStatus, WorkPacket, activation_plan, validate_runner_packet


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

    def test_write_exec_and_external_are_blocked(self):
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
        self.assertEqual(len(plan), 6)
        self.assertTrue(all(not row["enabled"] for row in plan))
        self.assertTrue(all(row["initial_scope"] == "read_only" for row in plan))


if __name__ == "__main__":
    unittest.main()
