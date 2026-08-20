from datetime import datetime, timezone

import pytest

from nexus_core.chat_memory_mesh import ChatShard
from nexus_core.memory_consolidation import consolidate_shards


def shard(shard_id: str, version: str, summary: str, supersedes=()):
    return ChatShard(
        shard_id=shard_id,
        chat_ref=f"chat://{shard_id}",
        created_at=datetime(2026, 8, 20, 10, 0, tzinfo=timezone.utc),
        source_version_ref=version,
        project_refs=("hydrotester",),
        goal_refs=("commercial",),
        tags=("quote",),
        summary=summary,
        evidence_refs=(f"e:{shard_id}",),
        supersedes=supersedes,
    )


def test_superseded_history_is_preserved_but_not_active():
    old = shard("old", "v1", "Quote pending")
    new = shard("new", "v2", "Quote received", supersedes=("old",))
    result = consolidate_shards(
        (old, new), consolidation_id="c1", created_at=datetime.now(timezone.utc)
    )
    assert result.active_shard_ids == ("new",)
    assert result.superseded_shard_ids == ("old",)
    assert "e:old" in result.evidence_refs


def test_conflicting_active_versions_are_preserved():
    a = shard("a", "v1", "Supplier quote pending")
    b = shard("b", "v2", "Supplier quote received")
    result = consolidate_shards(
        (a, b), consolidation_id="c2", created_at=datetime.now(timezone.utc)
    )
    assert result.conflict_pairs == (("a", "b"),)


def test_unknown_superseded_shard_fails_closed():
    bad = shard("new", "v2", "Updated", supersedes=("missing",))
    with pytest.raises(ValueError, match="unknown_superseded_shard"):
        consolidate_shards((bad,), consolidation_id="c3", created_at=datetime.now(timezone.utc))
