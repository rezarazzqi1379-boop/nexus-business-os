from datetime import datetime, timezone

import pytest

from nexus_core.asset_memory import AssetRecord, build_asset_catalog, retainable_for_long_term


def asset(**overrides):
    base = dict(
        asset_id="asset-1",
        file_name="spec.pdf",
        source="file_library",
        kind="pdf",
        stable_ref="file:file_1",
        source_version_ref="v1",
        observed_at=datetime(2026, 8, 20, 0, 0, tzinfo=timezone.utc),
        project_refs=("hydrotester",),
        goal_refs=("commercial",),
        evidence_refs=("file:file_1",),
        sensitivity="internal",
        analysis_state="unseen",
    )
    base.update(overrides)
    return AssetRecord(**base)


def test_catalog_detects_hash_duplicates_without_dropping_assets():
    h = "a" * 64
    a = asset(asset_id="a", content_sha256=h)
    b = asset(asset_id="b", stable_ref="file:file_2", evidence_refs=("file:file_2",), content_sha256=h)
    catalog = build_asset_catalog((a, b))
    assert ("a", "b") in catalog.duplicate_groups
    assert len(catalog.assets) == 2


def test_secret_is_not_long_term_retainable():
    assert not retainable_for_long_term(asset(sensitivity="credential_secret"))


def test_project_linked_normal_asset_is_retainable():
    assert retainable_for_long_term(asset())


def test_missing_evidence_fails_closed():
    with pytest.raises(ValueError, match="missing_evidence_refs"):
        build_asset_catalog((asset(evidence_refs=()),))


def test_bad_hash_fails_closed():
    with pytest.raises(ValueError, match="invalid_content_sha256"):
        build_asset_catalog((asset(content_sha256="bad"),))
