from __future__ import annotations

from dataclasses import dataclass

from .asset_memory import AssetRecord, validate_asset
from .chat_memory_mesh import ChatShard, validate_shard


@dataclass(frozen=True)
class CrossAssetBundle:
    asset_ids: tuple[str, ...]
    shard_ids: tuple[str, ...]
    project_refs: tuple[str, ...]
    goal_refs: tuple[str, ...]


def build_cross_asset_bundle(*, assets: tuple[AssetRecord, ...], shards: tuple[ChatShard, ...], project_refs: tuple[str, ...], goal_refs: tuple[str, ...]) -> CrossAssetBundle:
    for asset in assets:
        errors = validate_asset(asset)
        if errors:
            raise ValueError(",".join(errors))
    for shard in shards:
        errors = validate_shard(shard)
        if errors:
            raise ValueError(",".join(errors))

    selected_assets = tuple(
        a.asset_id for a in assets
        if set(a.project_refs) & set(project_refs) or set(a.goal_refs) & set(goal_refs)
    )
    selected_shards = tuple(
        s.shard_id for s in shards
        if set(s.project_refs) & set(project_refs) or set(s.goal_refs) & set(goal_refs)
    )
    return CrossAssetBundle(
        asset_ids=tuple(dict.fromkeys(selected_assets)),
        shard_ids=tuple(dict.fromkeys(selected_shards)),
        project_refs=project_refs,
        goal_refs=goal_refs,
    )
