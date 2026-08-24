from __future__ import annotations

import base64
import importlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from canonical_sources import CanonicalStore, hydrostatic_hold_points
from ops import backup, restore_backup, verify_backup
from security import _authorized, auth_config_valid
from canonical_sources import MAX_COMPRESSION_RATIO, extract_docx_text
from business_os import BusinessOSVault, VaultRequest
import threading
import zipfile


ROOT = Path(__file__).resolve().parents[1]


class CanonicalCloudTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_six_canonical_sources_ingest_idempotently(self):
        store = CanonicalStore(self.root / "canonical.db")
        first = store.ingest_directory(ROOT / "canonical_source_files")
        second = store.ingest_directory(ROOT / "canonical_source_files")
        self.assertEqual(len(first), 6)
        self.assertEqual(store.status()["count"], 6)
        self.assertTrue(all(item["inserted"] for item in first))
        self.assertTrue(all(not item["inserted"] for item in second))
        global_sources = [item for item in store.status()["sources"] if item["source_id"].startswith("NEXUS-")]
        self.assertTrue(all(item["project_id"] is None for item in global_sources))

    def test_hydro_workflow_is_source_bound_and_never_authorizes_action(self):
        store = CanonicalStore(self.root / "canonical.db")
        store.ingest_directory(ROOT / "canonical_source_files")
        result = hydrostatic_hold_points(store)
        self.assertEqual(result["source_id"], "PRJ-HYD-01-ENG")
        self.assertFalse(result["external_action_authorized"])
        self.assertEqual({item["code"] for item in result["findings"]},
                         {"HYD-PRESSURE", "HYD-THROUGHPUT", "HYD-CAPABILITY-MATRIX", "HYD-FAT"})

    def test_backup_is_verified_and_tampering_is_detected(self):
        store = CanonicalStore(self.root / "data" / "canonical.db")
        store.ingest_directory(ROOT / "canonical_source_files")
        result = backup(self.root / "data", self.root / "backups")
        target = Path(result["backup"])
        self.assertTrue(verify_backup(target)["valid"])
        with (target / "canonical.db").open("ab") as stream:
            stream.write(b"tamper")
        self.assertFalse(verify_backup(target)["valid"])

    def test_backup_round_trip_restores_database_and_vault(self):
        data = self.root / "data"
        store = CanonicalStore(data / "canonical.db")
        store.ingest_directory(ROOT / "canonical_source_files")
        vault = BusinessOSVault(data / "nexus_vault")
        vault.initialize()
        target = Path(backup(data, self.root / "backups")["backup"])
        restored = self.root / "restored"
        result = restore_backup(target, restored)
        self.assertTrue(result["restored"])
        self.assertEqual(CanonicalStore(restored / "canonical.db").status()["count"], 6)
        self.assertTrue((restored / "nexus_vault" / "SYSTEM" / "README.md").is_file())
        with self.assertRaisesRegex(ValueError, "not_empty"):
            restore_backup(target, restored)

    def test_docx_expansion_bomb_is_rejected(self):
        bomb = self.root / "bomb.docx"
        xml = b"<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>" + b" " * 500_000 + b"</w:document>"
        with zipfile.ZipFile(bomb, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", xml)
        with self.assertRaisesRegex(ValueError, "archive_expansion"):
            extract_docx_text(bomb)

    def test_concurrent_vault_collision_has_one_winner(self):
        vault = BusinessOSVault(self.root / "vault")
        vault.initialize()
        requests = [VaultRequest("same-id", "research", "hydrostatic_tester", title, "instructions", "tester", "2026-08-24T00:00:00+00:00") for title in ("A", "B")]
        outcomes = []
        def run(item):
            try:
                vault.enqueue(item); outcomes.append("created")
            except ValueError as exc:
                outcomes.append(str(exc))
        threads = [threading.Thread(target=run, args=(item,)) for item in requests]
        [thread.start() for thread in threads]
        [thread.join() for thread in threads]
        self.assertEqual(outcomes.count("request_id_collision"), 1)


class SecurityTests(unittest.TestCase):
    def test_production_auth_requires_long_token(self):
        with patch.dict(os.environ, {"NEXUS_AUTH_REQUIRED": "1", "NEXUS_ACCESS_TOKEN": "short"}, clear=False):
            self.assertFalse(auth_config_valid())

    def test_auth_is_required_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(auth_config_valid())

    def test_bearer_and_basic_use_same_secret(self):
        token = "a" * 32
        basic = base64.b64encode(f"nexus:{token}".encode()).decode()
        with patch.dict(os.environ, {"NEXUS_ACCESS_TOKEN": token}, clear=False):
            self.assertTrue(_authorized(f"Bearer {token}"))
            self.assertTrue(_authorized(f"Basic {basic}"))
            self.assertFalse(_authorized("Bearer wrong"))

    def test_api_fails_closed_and_returns_security_headers(self):
        token = "b" * 32
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
            "NEXUS_AUTH_REQUIRED": "1", "NEXUS_ACCESS_TOKEN": token,
            "NEXUS_STATE_DB": str(Path(directory) / "state.db"),
            "NEXUS_CANONICAL_DB": str(Path(directory) / "canonical.db"),
            "NEXUS_VAULT_ROOT": str(Path(directory) / "vault"),
        }, clear=False):
            import api
            importlib.reload(api)
            client = TestClient(api.app)
            self.assertEqual(client.get("/console").status_code, 401)
            self.assertEqual(client.get("/console").headers["x-frame-options"], "DENY")
            response = client.get("/console", auth=("nexus", token))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["x-frame-options"], "DENY")
            self.assertEqual(client.get("/health").status_code, 200)
            self.assertEqual(client.get("/ready").status_code, 200)
            oversized = client.post("/v1/events", content=b"x" * 1_048_577,
                                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
            self.assertEqual(oversized.status_code, 413)

    def test_unknown_project_cannot_pollute_event_store(self):
        token = "d" * 32
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
            "NEXUS_AUTH_REQUIRED": "1", "NEXUS_ACCESS_TOKEN": token,
            "NEXUS_STATE_DB": str(Path(directory) / "state.db"),
            "NEXUS_CANONICAL_DB": str(Path(directory) / "canonical.db"),
            "NEXUS_VAULT_ROOT": str(Path(directory) / "vault"),
        }, clear=False):
            import api
            importlib.reload(api)
            client = TestClient(api.app)
            body = {"event_id": "evt-unknown", "project_id": "attacker-project", "event_type": "message",
                    "source": "test", "occurred_at": "2026-08-24T00:00:00Z",
                    "received_at": "2026-08-24T00:00:01Z", "payload": {}}
            response = client.post("/v1/events", json=body, headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
