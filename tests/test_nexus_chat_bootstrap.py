import unittest

from nexus_chat_bootstrap import ChatIntent, bootstrap_chat, load_manifests
from nexus_connector_control_plane import (
    ConnectorSnapshot,
    ConnectorState,
    EvidenceClass,
    EvidenceEnvelope,
)


NOW = "2026-09-09T12:00:00+00:00"


def item(evidence_id, key, value):
    return EvidenceEnvelope(
        evidence_id=evidence_id,
        connector_id="github",
        project_id="PRJ-HYD-01",
        semantic_key=key,
        value=value,
        classification=EvidenceClass.FACT,
        source_locator=f"github://{evidence_id}",
        observed_at=NOW,
    )


class ChatBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.manifests = load_manifests("config/connectors.json")
        self.snapshot = ConnectorSnapshot(
            "github", NOW, ConnectorState.AVAILABLE, "commit-1"
        )

    def test_consequential_chat_requires_both_authorities(self):
        result = bootstrap_chat(
            intent=ChatIntent("chat-1", "PRJ-HYD-01"),
            manifests=self.manifests,
            snapshots=[self.snapshot],
            evidence=[item("registry", "authority.source_registry", "v1.8")],
            required_connectors=["github"],
            now=NOW,
        )
        self.assertEqual(result["gate"], "BLOCK")
        self.assertIn("REQUIRED_AUTHORITY_MISSING", [x["code"] for x in result["findings"]])

    def test_complete_authority_bootstrap_is_safe(self):
        result = bootstrap_chat(
            intent=ChatIntent("chat-1", "PRJ-HYD-01"),
            manifests=self.manifests,
            snapshots=[self.snapshot],
            evidence=[
                item("registry", "authority.source_registry", "v1.8"),
                item("master", "authority.project_master", "hyd-v1.1"),
            ],
            required_connectors=["github"],
            now=NOW,
        )
        self.assertEqual(result["gate"], "SAFE")
        self.assertEqual(result["chat_id"], "chat-1")


if __name__ == "__main__":
    unittest.main()
