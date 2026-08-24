from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from business_os import BusinessOSVault, VAULT_DIRECTORIES, VaultRequest


class BusinessOSVaultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "vault"
        self.vault = BusinessOSVault(self.root)
        self.vault.initialize()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def request(self, **overrides) -> VaultRequest:
        values = {
            "request_id": "research-001", "kind": "research", "project_id": "kcl_mop",
            "title": "Verify import rule", "instructions": "Use official sources only.",
            "requested_by": "reza", "created_at": datetime.now(timezone.utc).isoformat(),
        }
        values.update(overrides)
        return VaultRequest(**values)

    def test_initialize_creates_complete_portable_structure(self):
        for directory in VAULT_DIRECTORIES:
            self.assertTrue((self.root / directory).is_dir(), directory)

    def test_enqueue_is_idempotent_and_detects_collision(self):
        request = self.request()
        first = self.vault.enqueue(request)
        second = self.vault.enqueue(request)
        self.assertEqual(first, second)
        with self.assertRaisesRegex(ValueError, "request_id_collision"):
            self.vault.enqueue(self.request(title="Different request"))

    def test_claim_is_exactly_once(self):
        self.vault.enqueue(self.request())
        claimed = self.vault.claim("research-001")
        self.assertEqual(claimed.project_id, "kcl_mop")
        with self.assertRaisesRegex(ValueError, "request_not_pending"):
            self.vault.claim("research-001")

    def test_tampered_request_fails_closed(self):
        path = self.vault.enqueue(self.request())
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["project_id"] = "can_forming"
        path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "request_digest_mismatch"):
            self.vault.claim("research-001")
        self.assertTrue((self.root / "QUEUE/failed/research-001.json").exists())

    def test_complete_preserves_provenance_and_never_authorizes_action(self):
        request = self.request()
        self.vault.enqueue(request)
        self.vault.claim(request.request_id)
        output = self.vault.complete(request, "# Result\nEvidence reviewed.")
        text = output.read_text(encoding="utf-8")
        self.assertIn(f"source_digest: {request.digest}", text)
        self.assertIn("external_action_authorized: false", text)
        self.assertEqual(self.vault.status()["completed"], 1)

    def test_path_traversal_and_unknown_project_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_request_id"):
            self.vault.enqueue(self.request(request_id="../../escape"))
        with self.assertRaisesRegex(ValueError, "unknown_project"):
            self.vault.enqueue(self.request(project_id="invented"))

    def test_project_index_uses_canonical_registry_and_constraints(self):
        text = self.vault.write_project_index().read_text(encoding="utf-8")
        self.assertIn("hydrostatic_tester", text)
        self.assertIn("heat_treatment", text)
        self.assertIn("outreach_boyu", text)

    def test_daily_pulse_preserves_hold_and_generates_audit(self):
        pulse = self.vault.generate_daily_pulse().read_text(encoding="utf-8")
        self.assertIn("heat_treatment", pulse)
        self.assertIn("Status: **hold**", pulse)
        audit = tuple((self.root / "AUDIT").glob("*.jsonl"))
        self.assertEqual(len(audit), 1)

    def test_status_is_read_only_and_counts_generated_outputs(self):
        self.vault.write_project_index()
        self.vault.generate_daily_pulse()
        status = self.vault.status()
        self.assertIs(status["external_writes_enabled"], False)
        self.assertGreaterEqual(status["generated"], 1)


if __name__ == "__main__":
    unittest.main()
