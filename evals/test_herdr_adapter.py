from __future__ import annotations

import unittest

from herdr_adapter import build_herdr_plan
from runner_registry import CapabilityRisk, WorkPacket


class HerdrAdapterTests(unittest.TestCase):
    def packet(self, **changes):
        values = dict(
            packet_id="packet-herdr-001",
            project_id="hydrotester",
            objective="Review verified proposal evidence and write a draft memo",
            capability=CapabilityRisk.READ,
            workspace_subpath="PROJECTS/hydrotester",
            inputs={"source_refs": ["nexus:hydrotester:decision-pack-v1"]},
        )
        values.update(changes)
        return WorkPacket(**values)

    def test_builds_prepare_only_plan_without_approval_delegation(self):
        plan = build_herdr_plan(self.packet(), workspace_root="/srv/nexus")
        self.assertEqual(plan.mode, "prepare_only")
        self.assertFalse(plan.external_action_authorized)
        self.assertFalse(plan.approval_delegated)
        self.assertEqual(plan.runner_id, "herdr")
        self.assertEqual(plan.workspace, "/srv/nexus/PROJECTS/hydrotester")
        self.assertEqual(len(plan.steps), 4)

    def test_never_executes_or_predicts_pane_id(self):
        plan = build_herdr_plan(self.packet(), workspace_root="/srv/nexus")
        self.assertEqual(plan.steps[0].capture, "root_pane_id")
        self.assertIn("{root_pane_id}", plan.steps[1].argv)
        self.assertEqual(plan.steps[1].requires, ("root_pane_id",))

    def test_blocks_non_read_packets(self):
        with self.assertRaisesRegex(ValueError, "runner_capability_not_allowed"):
            build_herdr_plan(
                self.packet(capability=CapabilityRisk.EXEC),
                workspace_root="/srv/nexus",
            )

    def test_blocks_secret_material(self):
        with self.assertRaisesRegex(ValueError, "secret_material_forbidden"):
            build_herdr_plan(
                self.packet(inputs={"token": "Bearer abcdefghijklmnopqrstuvwxyz123456"}),
                workspace_root="/srv/nexus",
            )

    def test_blocks_approval_delegation(self):
        with self.assertRaisesRegex(ValueError, "approval_delegation_forbidden"):
            build_herdr_plan(
                self.packet(approval_id="approval-1"),
                workspace_root="/srv/nexus",
            )

    def test_requires_absolute_workspace_root(self):
        with self.assertRaisesRegex(ValueError, "workspace_root_must_be_absolute"):
            build_herdr_plan(self.packet(), workspace_root="relative")

    def test_rejects_unknown_agent_and_unbounded_timeout(self):
        with self.assertRaisesRegex(ValueError, "unsupported_herdr_agent_kind"):
            build_herdr_plan(self.packet(), workspace_root="/srv/nexus", agent_kind="unknown")
        with self.assertRaisesRegex(ValueError, "invalid_herdr_timeout"):
            build_herdr_plan(self.packet(), workspace_root="/srv/nexus", timeout_ms=999_999)


if __name__ == "__main__":
    unittest.main()
