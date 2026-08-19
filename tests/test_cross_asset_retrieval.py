from datetime import datetime, timezone

from nexus_core.asset_memory import AssetRecord
from nexus_core.chat_memory_mesh import ChatShard
from nexus_core.cross_asset_retrieval import build_cross_asset_bundle


def test_bundle_selects_shared_project_and_goal_context():
    asset = AssetRecord(
        asset_id="a1", file_name="rfq.pdf", source="file_library", kind="pdf",
        stable_ref="file://rfq", source_version_ref="v1",
        observed_at=datetime(2026, 8, 20, tzinfo=timezone.utc),
        project_refs=("kcl",), goal_refs=("commercial",), evidence_refs=("e1",),
    )
    shard = ChatShard(
        shard_id="s1", chat_ref="chat-1", created_at=datetime(2026, 8, 20, tzinfo=timezone.utc),
        source_version_ref="sv1", project_refs=("kcl",), goal_refs=("commercial",),
        tags=("rfq",), summary="KCl supplier work", evidence_refs=("e2",),
    )
    bundle = build_cross_asset_bundle(
        assets=(asset,), shards=(shard,), project_refs=("kcl",), goal_refs=(),
    )
    assert bundle.asset_ids == ("a1",)
    assert bundle.shard_ids == ("s1",)
