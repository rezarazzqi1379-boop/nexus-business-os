import sqlite3
from pathlib import Path

import pytest

from unified_data_environment import BackupManager, DataAsset, EvidenceObservation, UnifiedDataHub


def test_hub_indexes_evidence_and_builds_verified_backup(tmp_path: Path):
    source = tmp_path / "source.db"
    with sqlite3.connect(source) as db:
        db.execute("CREATE TABLE sample(value TEXT)")
        db.execute("INSERT INTO sample VALUES ('ok')")
    hub = UnifiedDataHub(tmp_path / "hub.db", tmp_path)
    assert hub.register_asset(DataAsset("source", "P1", "sqlite", "source.db", "canonical"))
    item = EvidenceObservation("o1", "P1", "status", "Ready", ("source:1",),
                               "2026-09-12T00:00:00+00:00", .9)
    assert hub.record_observation(item)
    assert hub.project_view("P1")[0]["statement"] == "Ready"
    snapshot = BackupManager(hub, tmp_path / "backups").create_snapshot("snap-1")
    assert BackupManager.verify_snapshot(snapshot)


def test_registration_is_idempotent_and_collision_safe(tmp_path: Path):
    (tmp_path / "a.json").write_text("{}", encoding="utf-8")
    hub = UnifiedDataHub(tmp_path / "hub.db", tmp_path)
    asset = DataAsset("a", "P1", "json", "a.json", "canonical")
    assert hub.register_asset(asset)
    assert hub.register_asset(asset) is False
    with pytest.raises(ValueError, match="collision"):
        hub.register_asset(DataAsset("a", "P2", "json", "a.json", "canonical"))


def test_secret_and_path_escape_are_rejected(tmp_path: Path):
    (tmp_path / ".env").write_text("SECRET=x", encoding="utf-8")
    hub = UnifiedDataHub(tmp_path / "hub.db", tmp_path)
    with pytest.raises(PermissionError):
        hub.register_asset(DataAsset("secret", "P1", "other", ".env", "local"))
    with pytest.raises(ValueError):
        hub.register_asset(DataAsset("escape", "P1", "other", "../x", "local"))


def test_tampered_snapshot_fails_verification(tmp_path: Path):
    (tmp_path / "a.json").write_text("{}", encoding="utf-8")
    hub = UnifiedDataHub(tmp_path / "hub.db", tmp_path)
    hub.register_asset(DataAsset("a", "P1", "json", "a.json", "canonical"))
    snapshot = BackupManager(hub, tmp_path / "backups").create_snapshot("snap")
    (snapshot / "files" / "a.json").write_text("tampered", encoding="utf-8")
    assert BackupManager.verify_snapshot(snapshot) is False

