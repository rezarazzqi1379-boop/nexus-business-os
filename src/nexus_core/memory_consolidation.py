from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from nexus_core.chat_memory_mesh import ChatShard, validate_shard


@dataclass(frozen=True)
class ConsolidatedMemory:
    consolidation_id: str
    created_at: datetime
    project_refs: tuple[str, ...]
    goal_refs: tuple[str, ...]
    active_shard_ids: tuple[str, ...]
    superseded_shard_ids: tuple[str, ...]
    conflict_pairs: tuple[tuple[str, str], ...]
    evidence_refs: tuple[str, ...]
    source_version_refs: tuple[str, ...]


def consolidate_shards(
    shards: Iterable[ChatShard],
    *,
    consolidation_id: str,
    created_at: datetime,
) -> ConsolidatedMemory:
    if not isinstance(consolidation_id, str) or not consolidation_id.strip():
        raise ValueError("invalid_consolidation_id")
    if not isinstance(created_at, datetime) or created_at.tzinfo is None:
        raise ValueError("created_at_must_be_timezone_aware")

    items = tuple(shards)
    if not items:
        raise ValueError("no_shards")

    seen: set[str] = set()
    superseded: set[str] = set()
    by_id: dict[str, ChatShard] = {}
    for shard in items:
        errors = validate_shard(shard)
        if errors:
            raise ValueError(",".join(errors))
        if shard.shard_id in seen:
            raise ValueError("duplicate_shard_id")
        seen.add(shard.shard_id)
        by_id[shard.shard_id] = shard
        superseded.update(shard.supersedes)

    unknown_supersedes = superseded - seen
    if unknown_supersedes:
        raise ValueError("unknown_superseded_shard")

    active = tuple(sorted(seen - superseded))
    conflicts: list[tuple[str, str]] = []
    active_shards = [by_id[shard_id] for shard_id in active]
    for i, left in enumerate(active_shards):
        for right in active_shards[i + 1:]:
            shared_scope = (set(left.project_refs) & set(right.project_refs)) or (set(left.goal_refs) & set(right.goal_refs))
            if not shared_scope:
                continue
            if left.summary != right.summary and left.source_version_ref != right.source_version_ref:
                conflicts.append((left.shard_id, right.shard_id))

    projects = tuple(sorted({ref for shard in items for ref in shard.project_refs}))
    goals = tuple(sorted({ref for shard in items for ref in shard.goal_refs}))
    evidence = tuple(dict.fromkeys(ref for shard in items for ref in shard.evidence_refs))
    versions = tuple(dict.fromkeys(shard.source_version_ref for shard in sorted(items, key=lambda x: (x.created_at, x.shard_id))))

    return ConsolidatedMemory(
        consolidation_id=consolidation_id,
        created_at=created_at,
        project_refs=projects,
        goal_refs=goals,
        active_shard_ids=active,
        superseded_shard_ids=tuple(sorted(superseded)),
        conflict_pairs=tuple(conflicts),
        evidence_refs=evidence,
        source_version_refs=versions,
    )
