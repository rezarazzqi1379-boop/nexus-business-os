from datetime import datetime, timezone

import pytest

from nexus_core.asset_chat_link import AssetChatLink, build_asset_context_bundle
from nexus_core.asset_memory import AssetRecord
from nexus_core.chat_memory_mesh import ChatShard


def test_cross_chat_asset_link_preserves_retrievable_reference():
    shard = ChatShard("chat-1", "chat://1", datetime(2026, 8, 20, tzinfo=timezone.utc), "chat-v1", ("hydrotester",), ("commercial",), ("image",), "Machine image supplied in prior chat.", ("chat:evidence",))
    asset = AssetRecord("asset-1", "machine.png", "file_library", "image", "file:file_1", "asset-v1", datetime(2026, 8, 20, tzinfo=timezone.utc), ("hydrotester",), ("commercial",), ("file:file_1",))
    link = AssetChatLink("chat-1", "asset-1", "referenced", "chat:evidence")
    bundle = build_asset_context_bundle((shard,), (asset,), (link,))
    assert bundle.asset_ids == ("asset-1",)


def test_unknown_asset_link_fails_closed():
    shard = ChatShard("chat-1", "chat://1", datetime(2026, 8, 20, tzinfo=timezone.utc), "chat-v1", ("hydrotester",), ("commercial",), ("image",), "Machine image supplied in prior chat.", ("chat:evidence",))
    with pytest.raises(ValueError, match="unknown_asset_ref"):
        build_asset_context_bundle((shard,), (), (AssetChatLink("chat-1", "missing", "referenced", "chat:evidence"),))
