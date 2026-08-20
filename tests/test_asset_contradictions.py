import pytest

from nexus_core.asset_contradictions import AssetClaim, detect_asset_contradictions


def claim(claim_id, asset_id, version, value, project="hydrotester"):
    return AssetClaim(
        claim_id=claim_id,
        asset_id=asset_id,
        source_version_ref=version,
        project_ref=project,
        subject="maximum pressure",
        predicate="rated_mpa",
        value=value,
        evidence_ref=f"file:{asset_id}",
    )


def test_detects_cross_asset_conflict():
    result = detect_asset_contradictions((claim("c1", "photo", "v1", "120"), claim("c2", "catalog", "v1", "70")))
    assert len(result) == 1
    assert {result[0].left_value, result[0].right_value} == {"120", "70"}


def test_same_value_is_not_conflict():
    assert detect_asset_contradictions((claim("c1", "a", "v1", "120"), claim("c2", "b", "v1", "120"))) == ()


def test_same_asset_same_version_is_not_self_conflict():
    assert detect_asset_contradictions((claim("c1", "a", "v1", "120"), claim("c2", "a", "v1", "70"))) == ()


def test_duplicate_claim_id_fails_closed():
    with pytest.raises(ValueError, match="duplicate_claim_id"):
        detect_asset_contradictions((claim("c1", "a", "v1", "120"), claim("c1", "b", "v1", "70")))
