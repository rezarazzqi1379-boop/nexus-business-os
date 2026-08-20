from datetime import datetime, timezone

import pytest

from nexus_core.chat_memory_mesh import ChatShard, build_cross_chat_bootstrap, retrieve_chat_context


def shard(**overrides):
    base = dict(
        shard_id="chat-a",
        chat_ref="chat://a",
        created_at=datetime(2026, 8, 20, 10, 0, tzinfo=timezone.utc),
        source_version_ref="v1",
        project_refs=("hydrotester",),
        goal_refs=("commercial",),
        tags=("quote", "supplier"),
        summary="Hydrotester quote blocker is pipe length and wall thickness.",
        evidence_refs=("gmail:thread-1",),
        supersedes=(),
    )
    base.update(overrides)
    return ChatShard(**base)


def test_retrieves_relevant_project_context():
    result = retrieve_chat_context((shard(),), query="hydrotester supplier quote", project_refs=("hydrotester",))
    assert result.retrieved[0].shard.shard_id == "chat-a"
    assert "project_match" in result.retrieved[0].reasons


def test_superseded_shard_is_preserved_but_discounted():
    old = shard(shard_id="old", source_version_ref="v1")
    new = shard(shard_id="new", source_version_ref="v2", supersedes=("old",), summary="Hydrotester blocker has been resolved by engineering.")
    result = retrieve_chat_context((old, new), query="hydrotester blocker", project_refs=("hydrotester",))
    ids = [item.shard.shard_id for item in result.retrieved]
    assert "old" in ids and "new" in ids
    assert next(x.score for x in result.retrieved if x.shard.shard_id == "new") > next(x.score for x in result.retrieved if x.shard.shard_id == "old")


def test_conflicting_versions_are_not_silently_merged():
    a = shard(shard_id="a", source_version_ref="v1", summary="Supplier quote pending.")
    b = shard(shard_id="b", source_version_ref="v2", summary="Supplier quote received.")
    result = retrieve_chat_context((a, b), query="supplier quote", project_refs=("hydrotester",))
    assert result.conflicts


def test_duplicate_shard_identity_fails_closed():
    with pytest.raises(ValueError, match="duplicate_shard_id"):
        retrieve_chat_context((shard(), shard()), query="hydrotester")


def test_missing_evidence_fails_closed():
    with pytest.raises(ValueError, match="missing_evidence_refs"):
        retrieve_chat_context((shard(evidence_refs=()),), query="hydrotester")


def test_bootstrap_requires_live_verification():
    result = retrieve_chat_context((shard(),), query="hydrotester")
    text = build_cross_chat_bootstrap(result)
    assert "continuity evidence only" in text
    assert "live-verify mutable systems" in text
