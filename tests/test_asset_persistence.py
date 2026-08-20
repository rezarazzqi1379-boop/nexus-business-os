from dataclasses import replace
from datetime import datetime, timezone

import pytest

from nexus_core.asset_memory import AssetRecord
from nexus_core.asset_persistence import InMemoryAssetPersistence


def make_asset(version: str = "v1") -> AssetRecord:
    return AssetRecord(
        asset_id="asset-1",
        file_name="spec.pdf",
        source="file_library",
        kind="pdf",
        stable_ref="file://spec",
        source_version_ref=version,
        observed_at=datetime(2026, 8, 20, tzinfo=timezone.utc),
        project_refs=("hydrotester",),
        goal_refs=("commercial",),
        evidence_refs=("e1",),
    )


def test_round_trip_and_project_listing():
    repo = InMemoryAssetPersistence()
    ref = repo.put(make_asset())
    assert ref.asset_id == "asset-1"
    assert repo.get("asset-1") is not None
    assert [a.asset_id for a in repo.list_project("hydrotester")] == ["asset-1"]


def test_asset_id_cannot_silently_change_version():
    repo = InMemoryAssetPersistence()
    repo.put(make_asset("v1"))
    with pytest.raises(ValueError, match="asset_id_version_collision"):
        repo.put(make_asset("v2"))


def test_exact_repeat_is_idempotent_but_same_version_drift_is_rejected():
    repo = InMemoryAssetPersistence()
    original = make_asset("v1")
    repo.put(original)
    repo.put(original)

    changed = replace(original, file_name="changed.pdf")
    with pytest.raises(ValueError, match="asset_identity_collision"):
        repo.put(changed)

    assert repo.get("asset-1") == original
