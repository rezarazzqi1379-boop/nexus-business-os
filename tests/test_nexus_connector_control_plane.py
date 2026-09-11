import unittest

from nexus_connector_control_plane import (
    ActionScope,
    ApprovalScope,
    ConnectorControlPlane,
    ConnectorManifest,
    ConnectorSnapshot,
    ConnectorState,
    EvidenceClass,
    EvidenceEnvelope,
)


NOW = "2026-09-09T12:00:00+00:00"


def manifest(connector_id="gmail"):
    return ConnectorManifest(
        connector_id=connector_id,
        system=connector_id,
        authority_scope=("dynamic_evidence",),
        project_scope=("PRJ-HYD-01",),
        read_capable=True,
        write_capable=True,
        freshness_seconds=3600,
        credential_locator=f"env://{connector_id.upper()}_TOKEN",
    )


def snapshot(connector_id="gmail", state=ConnectorState.AVAILABLE, observed_at=NOW):
    return ConnectorSnapshot(connector_id, observed_at, state, "rev-1")


def evidence(evidence_id, value, *, project_id="PRJ-HYD-01", classification=EvidenceClass.CLAIM,
             connector_id="gmail", supersedes=()):
    return EvidenceEnvelope(
        evidence_id=evidence_id,
        connector_id=connector_id,
        project_id=project_id,
        semantic_key="commercial.price",
        value=value,
        classification=classification,
        source_locator=f"gmail://{evidence_id}",
        observed_at=NOW,
        supersedes=supersedes,
    )


class ConnectorControlPlaneTests(unittest.TestCase):
    def action(self):
        return ActionScope("send", "Fiona", "whatsapp:+86", "sha256:text", "sha256:none", "v1")

    def approval(self):
        return ApprovalScope("approval-123", "send", "Fiona", "whatsapp:+86", "sha256:text", "sha256:none", "v1")
    def test_safe_preflight_builds_chat_bootstrap(self):
        plane = ConnectorControlPlane([manifest()])
        result = plane.preflight(
        project_id="PRJ-HYD-01",
        snapshots=[snapshot()],
        evidence=[evidence("e1", {"amount": 542800, "currency": "USD"})],
        required_connectors=["gmail"],
        now=NOW,
    )
        self.assertEqual(result["gate"], "SAFE")
        self.assertTrue(result["chat_bootstrap"]["fail_closed"])


    def test_cross_project_evidence_is_blocked_and_excluded(self):
        plane = ConnectorControlPlane([manifest()])
        result = plane.preflight(
        project_id="PRJ-HYD-01", snapshots=[snapshot()],
        evidence=[evidence("e1", 10, project_id="PRJ-KCL-01")],
        required_connectors=["gmail"], now=NOW,
    )
        self.assertEqual(result["gate"], "BLOCK")
        self.assertEqual(result["evidence_count"], 0)
        self.assertEqual(result["findings"][0]["code"], "CROSS_PROJECT_EVIDENCE")


    def test_stale_required_connector_blocks(self):
        plane = ConnectorControlPlane([manifest()])
        result = plane.preflight(
        project_id="PRJ-HYD-01",
        snapshots=[snapshot(observed_at="2026-09-09T10:00:00+00:00")],
        evidence=[], required_connectors=["gmail"], now=NOW,
    )
        self.assertEqual(result["gate"], "BLOCK")
        self.assertEqual(result["findings"][0]["code"], "STALE_CONNECTOR_SNAPSHOT")


    def test_fact_conflict_blocks_but_claim_conflict_requires_review(self):
        plane = ConnectorControlPlane([manifest()])
        fact_result = plane.preflight(
        project_id="PRJ-HYD-01", snapshots=[snapshot()],
        evidence=[evidence("e1", 70, classification=EvidenceClass.FACT),
                  evidence("e2", 120, classification=EvidenceClass.CLAIM)],
        required_connectors=["gmail"], now=NOW,
    )
        claim_result = plane.preflight(
        project_id="PRJ-HYD-01", snapshots=[snapshot()],
        evidence=[evidence("e1", 70), evidence("e2", 120)],
        required_connectors=["gmail"], now=NOW,
    )
        self.assertEqual(fact_result["gate"], "BLOCK")
        self.assertEqual(claim_result["gate"], "REVIEW")


    def test_explicit_supersession_removes_old_value_and_conflict(self):
        plane = ConnectorControlPlane([manifest()])
        result = plane.preflight(
        project_id="PRJ-HYD-01", snapshots=[snapshot()],
        evidence=[evidence("old", 70), evidence("new", 120, supersedes=("old",))],
        required_connectors=["gmail"], now=NOW,
    )
        self.assertEqual(result["gate"], "SAFE")
        self.assertEqual(result["evidence_count"], 1)


    def test_external_action_needs_exact_approval(self):
        plane = ConnectorControlPlane([manifest()])
        denied = plane.preflight(
        project_id="PRJ-HYD-01", snapshots=[snapshot()], evidence=[],
        required_connectors=["gmail"], now=NOW, external_action_requested=True,
        requested_action=self.action(),
    )
        allowed = plane.preflight(
        project_id="PRJ-HYD-01", snapshots=[snapshot()], evidence=[],
        required_connectors=["gmail"], now=NOW, external_action_requested=True,
        requested_action=self.action(),
        exact_approval=self.approval(),
    )
        self.assertEqual(denied["gate"], "BLOCK")
        self.assertFalse(denied["external_action_authorized"])
        self.assertEqual(allowed["gate"], "SAFE")
        self.assertTrue(allowed["external_action_authorized"])

    def test_duplicate_snapshots_and_evidence_ids_block(self):
        plane = ConnectorControlPlane([manifest()])
        result = plane.preflight(
            project_id="PRJ-HYD-01", snapshots=[snapshot(), snapshot()],
            evidence=[evidence("e1", 70), evidence("e1", 70)],
            required_connectors=["gmail"], now=NOW,
        )
        self.assertEqual(result["gate"], "BLOCK")
        codes = {item["code"] for item in result["findings"]}
        self.assertIn("DUPLICATE_CONNECTOR_SNAPSHOT", codes)
        self.assertIn("DUPLICATE_EVIDENCE_ID", codes)

    def test_stale_evidence_blocks_even_with_fresh_connector(self):
        plane = ConnectorControlPlane([manifest()])
        stale = EvidenceEnvelope(
            evidence_id="e1", connector_id="gmail", project_id="PRJ-HYD-01",
            semantic_key="commercial.price", value=70, classification=EvidenceClass.CLAIM,
            source_locator="gmail://e1", observed_at="2026-09-09T10:00:00+00:00",
        )
        result = plane.preflight(
            project_id="PRJ-HYD-01", snapshots=[snapshot()], evidence=[stale],
            required_connectors=["gmail"], now=NOW,
        )
        self.assertEqual(result["gate"], "BLOCK")
        self.assertIn("STALE_EVIDENCE", [item["code"] for item in result["findings"]])

    def test_cross_key_supersession_is_rejected(self):
        plane = ConnectorControlPlane([manifest()])
        old = evidence("old", 70)
        new = EvidenceEnvelope(
            evidence_id="new", connector_id="gmail", project_id="PRJ-HYD-01",
            semantic_key="technical.pressure", value=120, classification=EvidenceClass.CLAIM,
            source_locator="gmail://new", observed_at=NOW, supersedes=("old",),
        )
        result = plane.preflight(
            project_id="PRJ-HYD-01", snapshots=[snapshot()], evidence=[old, new],
            required_connectors=["gmail"], now=NOW,
        )
        self.assertEqual(result["gate"], "BLOCK")
        self.assertIn("INVALID_CROSS_KEY_SUPERSESSION", [item["code"] for item in result["findings"]])

    def test_incomplete_approval_scope_does_not_authorize(self):
        plane = ConnectorControlPlane([manifest()])
        incomplete = ApprovalScope("approval-123", "send", "", "whatsapp:+86", "sha256:text", "sha256:none", "v1")
        result = plane.preflight(
            project_id="PRJ-HYD-01", snapshots=[snapshot()], evidence=[],
            required_connectors=["gmail"], now=NOW, external_action_requested=True,
            requested_action=self.action(),
            exact_approval=incomplete,
        )
        self.assertEqual(result["gate"], "BLOCK")
        self.assertFalse(result["external_action_authorized"])

    def test_approval_must_match_exact_action_scope(self):
        plane = ConnectorControlPlane([manifest()])
        changed_text = ActionScope("send", "Fiona", "whatsapp:+86", "sha256:changed", "sha256:none", "v1")
        result = plane.preflight(
            project_id="PRJ-HYD-01", snapshots=[snapshot()], evidence=[],
            required_connectors=["gmail"], now=NOW, external_action_requested=True,
            requested_action=changed_text, exact_approval=self.approval(),
        )
        self.assertEqual(result["gate"], "BLOCK")
        self.assertFalse(result["external_action_authorized"])
        self.assertIn("EXACT_APPROVAL_MISMATCH", [item["code"] for item in result["findings"]])


    def test_credentials_must_be_references_not_values(self):
        with self.assertRaisesRegex(ValueError, "credential_value_forbidden_use_locator_only"):
            ConnectorManifest(
            connector_id="bad", system="bad", authority_scope=("x",), project_scope=("*",),
            read_capable=True, write_capable=False, freshness_seconds=10,
            credential_locator="token=plaintext",
            )


if __name__ == "__main__":
    unittest.main()
