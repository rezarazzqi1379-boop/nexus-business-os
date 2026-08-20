from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Iterable, Mapping

from nexus_core.chat_memory_mesh import ChatShard, validate_shard


@dataclass(frozen=True)
class SemanticHit:
    shard: ChatShard
    score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class SemanticMemoryBundle:
    query: str
    hits: tuple[SemanticHit, ...]
    source_version_refs: tuple[str, ...]


def _validate_vector(name: str, vector: object) -> tuple[float, ...]:
    if not isinstance(vector, tuple) or not vector:
        raise ValueError(f"{name}_must_be_nonempty_tuple")
    values: list[float] = []
    for value in vector:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name}_must_be_numeric")
        number = float(value)
        if number != number or number in (float("inf"), float("-inf")):
            raise ValueError(f"{name}_must_be_finite")
        values.append(number)
    magnitude = sqrt(sum(v * v for v in values))
    if magnitude == 0:
        raise ValueError(f"{name}_must_be_nonzero")
    return tuple(values)


def cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    a = _validate_vector("left", left)
    b = _validate_vector("right", right)
    if len(a) != len(b):
        raise ValueError("vector_dimension_mismatch")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    mag_a = sqrt(sum(x * x for x in a))
    mag_b = sqrt(sum(y * y for y in b))
    return dot / (mag_a * mag_b)


def retrieve_semantic_context(
    shards: Iterable[ChatShard],
    *,
    query: str,
    query_embedding: tuple[float, ...],
    shard_embeddings: Mapping[str, tuple[float, ...]],
    project_refs: tuple[str, ...] = (),
    goal_refs: tuple[str, ...] = (),
    limit: int = 10,
    minimum_score: float = 0.15,
) -> SemanticMemoryBundle:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("invalid_query")
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1 or limit > 50:
        raise ValueError("invalid_limit")
    if not isinstance(minimum_score, (int, float)) or isinstance(minimum_score, bool):
        raise ValueError("invalid_minimum_score")
    if minimum_score < -1 or minimum_score > 1:
        raise ValueError("invalid_minimum_score")
    q = _validate_vector("query_embedding", query_embedding)

    seen_ids: set[str] = set()
    ranked: list[SemanticHit] = []
    for shard in tuple(shards):
        errors = validate_shard(shard)
        if errors:
            raise ValueError(",".join(errors))
        if shard.shard_id in seen_ids:
            raise ValueError("duplicate_shard_id")
        seen_ids.add(shard.shard_id)
        if shard.shard_id not in shard_embeddings:
            continue
        vector = _validate_vector(f"embedding:{shard.shard_id}", shard_embeddings[shard.shard_id])
        if len(vector) != len(q):
            raise ValueError("vector_dimension_mismatch")
        semantic = cosine_similarity(q, vector)
        project_boost = 0.12 if set(project_refs) & set(shard.project_refs) else 0.0
        goal_boost = 0.12 if set(goal_refs) & set(shard.goal_refs) else 0.0
        score = min(1.0, semantic + project_boost + goal_boost)
        if score < minimum_score:
            continue
        reasons: list[str] = ["semantic_similarity"]
        if project_boost:
            reasons.append("project_match")
        if goal_boost:
            reasons.append("goal_match")
        ranked.append(SemanticHit(shard=shard, score=round(score, 6), reasons=tuple(reasons)))

    ranked.sort(key=lambda item: (-item.score, -item.shard.created_at.timestamp(), item.shard.shard_id))
    selected = tuple(ranked[:limit])
    versions = tuple(dict.fromkeys(item.shard.source_version_ref for item in selected))
    return SemanticMemoryBundle(query=query, hits=selected, source_version_refs=versions)
