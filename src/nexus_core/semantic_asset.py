from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Iterable

from .asset_memory import AssetRecord, validate_asset


@dataclass(frozen=True)
class AssetEmbedding:
    asset_id: str
    source_version_ref: str
    vector: tuple[float, ...]
    model_ref: str


@dataclass(frozen=True)
class RetrievedAsset:
    asset: AssetRecord
    score: float
    reasons: tuple[str, ...]


def _cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    if not a or not b or len(a) != len(b):
        raise ValueError("embedding_dimension_mismatch")
    if any(not isinstance(x, (int, float)) for x in (*a, *b)):
        raise ValueError("embedding_must_be_numeric")
    na = sqrt(sum(float(x) * float(x) for x in a))
    nb = sqrt(sum(float(x) * float(x) for x in b))
    if na == 0 or nb == 0:
        raise ValueError("zero_norm_embedding")
    return sum(float(x) * float(y) for x, y in zip(a, b)) / (na * nb)


def retrieve_assets_semantically(
    assets: Iterable[AssetRecord],
    embeddings: Iterable[AssetEmbedding],
    *,
    query_vector: tuple[float, ...],
    project_refs: tuple[str, ...] = (),
    goal_refs: tuple[str, ...] = (),
    limit: int = 10,
) -> tuple[RetrievedAsset, ...]:
    if limit < 1 or limit > 100:
        raise ValueError("invalid_limit")
    asset_items = tuple(assets)
    embedding_items = tuple(embeddings)
    by_id = {a.asset_id: a for a in asset_items}
    if len(by_id) != len(asset_items):
        raise ValueError("duplicate_asset_id")
    for asset in asset_items:
        errors = validate_asset(asset)
        if errors:
            raise ValueError(",".join(errors))

    seen_embedding_ids: set[str] = set()
    ranked: list[RetrievedAsset] = []
    for emb in embedding_items:
        if not isinstance(emb, AssetEmbedding):
            raise ValueError("embedding_must_be_asset_embedding")
        if emb.asset_id in seen_embedding_ids:
            raise ValueError("duplicate_embedding_asset_id")
        seen_embedding_ids.add(emb.asset_id)
        asset = by_id.get(emb.asset_id)
        if asset is None:
            raise ValueError("embedding_for_unknown_asset")
        if emb.source_version_ref != asset.source_version_ref:
            raise ValueError("stale_embedding_source_version")
        if not isinstance(emb.model_ref, str) or not emb.model_ref.strip():
            raise ValueError("invalid_embedding_model_ref")
        semantic = max(-1.0, min(1.0, _cosine(query_vector, emb.vector)))
        project_boost = 0.15 if set(project_refs) & set(asset.project_refs) else 0.0
        goal_boost = 0.15 if set(goal_refs) & set(asset.goal_refs) else 0.0
        stale_penalty = 0.25 if asset.analysis_state == "stale" else 0.0
        score = semantic + project_boost + goal_boost - stale_penalty
        reasons: list[str] = ["semantic_similarity"]
        if project_boost:
            reasons.append("project_match")
        if goal_boost:
            reasons.append("goal_match")
        if stale_penalty:
            reasons.append("stale_analysis_penalty")
        ranked.append(RetrievedAsset(asset, round(score, 6), tuple(reasons)))

    ranked.sort(key=lambda item: (-item.score, item.asset.observed_at, item.asset.asset_id))
    return tuple(ranked[:limit])
