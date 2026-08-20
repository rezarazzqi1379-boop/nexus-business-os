from datetime import datetime, timezone

import pytest

from nexus_core.asset_manifest import AssetBackupState, AssetManifestEntry, build_asset_manifest, verified_copy
from nexus_core.asset_memory import AssetRecord


def asset(**overrides):
    base = dict(
        asset_id="a1",
        file_name="spec.pdf",
        source="file_library",
        kind="pdf",
        stable_ref="file://spec",
        source_version_ref="v1",
        observed_at=datetime(2026, 8, 20, 10, 0, tzinfo=timezone.utc),
        project_refs=("hydrotester",),
        goal_refs=("commercial",),
        evidence_refs=("file:spec",),
        content_sha256="a" * 64,
    )
    base.update(overrides)
    return AssetRecord(**base)


def test_reference_only_is_not_verified_backup():
    a = asset(content_sha256=None)
    state = AssetBackupState("a1", "v1", "reference_only", None, None, None)
    manifest = build_asset_manifest("m1", datetime.now(timezone.utc), (AssetManifestEntry(a, state),))
    assert verified_copy("a1", manifest) is False


def test_verified_copy_requires_matching_restore_digest():
    state = AssetBackupState("a1", "v1", "copied_verified", "drive:1", datetime.now(timezone.utc), datetime.now(timezone.utc), "a"*64, "b"*64)
    with pytest.raises(ValueError, match="restore_digest_mismatch"):
        build_asset_manifest("m1", datetime.now(timezone.utc), (AssetManifestEntry(asset(), state),))


def test_verified_copy_succeeds_only_with_exact_version_and_digest():
    now = datetime.now(timezone.utc)
    state = AssetBackupState("a1", "v1", "copied_verified", "drive:1", now, now, "a"*64, "a"*64)
    manifest = build_asset_manifest("m1", now, (AssetManifestEntry(asset(), state),))
    assert verified_copy("a1", manifest) is True


def test_manifest_rejects_asset_version_mismatch():
    state = AssetBackupState("a1", "v2", "reference_only", None, None, None)
    with pytest.raises(ValueError, match="asset_backup_version_mismatch"):
        build_asset_manifest("m1", datetime.now(timezone.utc), (AssetManifestEntry(asset(), state),))
