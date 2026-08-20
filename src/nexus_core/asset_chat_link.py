from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .asset_memory import AssetRecord, validate_asset
from .chat_memory_mesh import ChatShard, validate_shard


@dataclass(frozen=True)
class AssetChatLink:
    shard_id: str
    asset_id: str
    relation: str
    evidence_ref: str


@dataclass(frozen=True)
class AssetContextBundle:
    shard_ids: tuple[str, ...]
    asset_ids: tuple[str, ...]
    links: tuple[AssetChatLink, ...]


def build_asset_context_bundle(shards: Iterable[ChatShard], assets: Iterable[AssetRecord], links: Iterable[AssetChatLink]) -> AssetContextBundle:
    shard_items = tuple(shards)
    asset_items = tuple(assets)
    link_items = tuple(links)
    shard_ids = {s.shard_id for s in shard_items}
    asset_ids = {a.asset_id for a in asset_items}
    if len(shard_ids) != len(shard_items):
        raise ValueError("duplicate_shard_id")
    if len(asset_ids) != len(asset_items):
        raise ValueError("duplicate_asset_id")
    for shard in shard_items:
        errors = validate_shard(shard)
        if errors: raise ValueError(",".join(errors))
    for asset in asset_items:
        errors = validate_asset(asset)
        if errors: raise ValueError(",".join(errors))
    seen_links: set[tuple[str, str, str]] = set()
    for link in link_items:
        if link.shard_id not in shard_ids:
            raise ValueError("unknown_shard_ref")
        if link.asset_id not in asset_ids:
            raise ValueError("unknown_asset_ref")
        if not isinstance(link.relation, str) or not link.relation.strip():
            raise ValueError("invalid_relation")
        if not isinstance(link.evidence_ref, str) or not link.evidence_ref.strip():
            raise ValueError("invalid_evidence_ref")
        key = (link.shard_id, link.asset_id, link.relation)
        if key in seen_links:
            raise ValueError("duplicate_asset_chat_link")
        seen_links.add(key)
    return AssetContextBundle(tuple(sorted(shard_ids)), tuple(sorted(asset_ids)), link_items)
