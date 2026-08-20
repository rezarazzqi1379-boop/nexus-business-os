from datetime import datetime, timezone

import pytest

from nexus_core.chat_memory_mesh import ChatShard
from nexus_core.semantic_memory import cosine_similarity, retrieve_semantic_context


def shard(shard_id: str, project: str) -> ChatShard:
    return ChatShard(
        shard_id=shard_id,
        chat_ref=f"chat://{shard_id}",
        created_at=datetime(2026, 8, 20, 10, 0, tzinfo=timezone.utc),
        source_version_ref=f"v:{shard_id}",
        project_refs=(project,),
        goal_refs=("commercial",),
        tags=(project,),
        summary=f"Context for {project}",
        evidence_refs=(f"e:{shard_id}",),
    )


def test_semantic_similarity_and_project_boost():
    a = shard("a", "kcl")
    b = shard("b", "hydrotester")
    result = retrieve_semantic_context(
        (a, b),
        query="potassium supplier",
        query_embedding=(1.0, 0.0),
        shard_embeddings={"a": (0.9, 0.1), "b": (0.0, 1.0)},
        project_refs=("kcl",),
    )
    assert result.hits[0].shard.shard_id == "a"
    assert "project_match" in result.hits[0].reasons


def test_missing_embedding_is_not_fabricated():
    a = shard("a", "kcl")
    result = retrieve_semantic_context(
        (a,), query="kcl", query_embedding=(1.0, 0.0), shard_embeddings={}
    )
    assert result.hits == ()


def test_dimension_mismatch_fails_closed():
    with pytest.raises(ValueError, match="vector_dimension_mismatch"):
        cosine_similarity((1.0, 0.0), (1.0,))


def test_zero_vector_fails_closed():
    with pytest.raises(ValueError, match="must_be_nonzero"):
        cosine_similarity((0.0, 0.0), (1.0, 0.0))
