from datetime import datetime, timezone

import pytest

from nexus_core.asset_memory import AssetRecord
from nexus_core.semantic_asset import AssetEmbedding, retrieve_assets_semantically


def asset(asset_id="a1", version="v1", project="hydrotester", state="analyzed"):
    return AssetRecord(
        asset_id=asset_id,
        file_name=f"{asset_id}.pdf",
        source="file_library",
        kind="pdf",
        stable_ref=f"file://{asset_id}",
        source_version_ref=version,
        observed_at=datetime(2026, 8, 20, 10, 0, tzinfo=timezone.utc),
        project_refs=(project,),
        goal_refs=("commercial",),
        evidence_refs=(f"file:{asset_id}",),
        analysis_state=state,
    )


def test_semantic_similarity_and_project_match_rank_asset():
    assets = (asset("a1", project="hydrotester"), asset("a2", project="kcl"))
    embeddings = (
        AssetEmbedding("a1", "v1", (1.0, 0.0), "model:v1"),
        AssetEmbedding("a2", "v1", (0.8, 0.2), "model:v1"),
    )
    result = retrieve_assets_semantically(assets, embeddings, query_vector=(1.0, 0.0), project_refs=("hydrotester",))
    assert result[0].asset.asset_id == "a1"
    assert "project_match" in result[0].reasons


def test_stale_embedding_version_fails_closed():
    with pytest.raises(ValueError, match="stale_embedding_source_version"):
        retrieve_assets_semantically((asset(),), (AssetEmbedding("a1", "v0", (1.0, 0.0), "model:v1"),), query_vector=(1.0, 0.0))


def test_dimension_mismatch_fails_closed():
    with pytest.raises(ValueError, match="embedding_dimension_mismatch"):
        retrieve_assets_semantically((asset(),), (AssetEmbedding("a1", "v1", (1.0, 0.0), "model:v1"),), query_vector=(1.0, 0.0, 0.0))


def test_unknown_asset_embedding_fails_closed():
    with pytest.raises(ValueError, match="embedding_for_unknown_asset"):
        retrieve_assets_semantically((asset(),), (AssetEmbedding("missing", "v1", (1.0, 0.0), "model:v1"),), query_vector=(1.0, 0.0))
