from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Literal

SourceKind = Literal["official", "regulatory", "academic", "company", "news", "web", "crm", "email"]
EvidenceTier = Literal["strong", "partial", "weak", "unverified"]

_ALLOWED_SOURCE_KINDS = {"official", "regulatory", "academic", "company", "news", "web", "crm", "email"}
_TIER_WEIGHT = {"strong": 4, "partial": 3, "weak": 2, "unverified": 1}
_MAX_TEXT = 512


@dataclass(frozen=True)
class ResearchQuery:
    query_id: str
    text: str
    intent: str
    max_sources: int = 6


@dataclass(frozen=True)
class ResearchSource:
    source_id: str
    kind: SourceKind
    domain: str
    retrieved_at: str
    evidence_ref: str
    latency_ms: int
    confidence: int


@dataclass(frozen=True)
class ResearchHit:
    query_id: str
    source_id: str
    canonical_key: str
    title: str
    raw_observation: str
    evidence_tier: EvidenceTier
    relevance: int


@dataclass(frozen=True)
class ResearchPlan:
    query_id: str
    selected_sources: tuple[str, ...]
    rejected_sources: tuple[str, ...]


@dataclass(frozen=True)
class FusedFinding:
    canonical_key: str
    title: str
    best_observation: str
    evidence_tier: EvidenceTier
    supporting_sources: tuple[str, ...]
    score: int


def _bounded_text(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value == value.strip() and len(value) <= _MAX_TEXT


def _aware_iso(value: object) -> datetime | None:
    if not isinstance(value, str) or not value or value != value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def _valid_score(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 100


def validate_query(query: object) -> None:
    if not isinstance(query, ResearchQuery):
        raise ValueError("invalid_query")
    if not _bounded_text(query.query_id) or not _bounded_text(query.text) or not _bounded_text(query.intent):
        raise ValueError("invalid_query_text")
    if not isinstance(query.max_sources, int) or isinstance(query.max_sources, bool) or not 1 <= query.max_sources <= 12:
        raise ValueError("invalid_max_sources")


def validate_source(source: object) -> None:
    if not isinstance(source, ResearchSource):
        raise ValueError("invalid_source")
    if not _bounded_text(source.source_id) or not _bounded_text(source.domain) or not _bounded_text(source.evidence_ref):
        raise ValueError("invalid_source_identity")
    if source.kind not in _ALLOWED_SOURCE_KINDS:
        raise ValueError("invalid_source_kind")
    if _aware_iso(source.retrieved_at) is None:
        raise ValueError("invalid_retrieved_at")
    if not isinstance(source.latency_ms, int) or isinstance(source.latency_ms, bool) or source.latency_ms < 0:
        raise ValueError("invalid_latency")
    if not _valid_score(source.confidence):
        raise ValueError("invalid_confidence")


def plan_sources(query: ResearchQuery, sources: Iterable[ResearchSource]) -> ResearchPlan:
    validate_query(query)
    try:
        pool = tuple(sources)
    except TypeError as exc:
        raise ValueError("sources_must_be_iterable") from exc
    seen: set[str] = set()
    for source in pool:
        validate_source(source)
        if source.source_id in seen:
            raise ValueError("duplicate_source")
        seen.add(source.source_id)
    ranked = sorted(pool, key=lambda s: (-s.confidence, s.latency_ms, s.source_id))
    selected = tuple(s.source_id for s in ranked[: query.max_sources])
    rejected = tuple(s.source_id for s in ranked[query.max_sources :])
    return ResearchPlan(query.query_id, selected, rejected)


def fuse_hits(hits: Iterable[ResearchHit]) -> tuple[FusedFinding, ...]:
    try:
        items = tuple(hits)
    except TypeError as exc:
        raise ValueError("hits_must_be_iterable") from exc
    grouped: dict[str, list[ResearchHit]] = {}
    for hit in items:
        if not isinstance(hit, ResearchHit):
            raise ValueError("invalid_hit")
        if not all(_bounded_text(value) for value in (hit.query_id, hit.source_id, hit.canonical_key, hit.title, hit.raw_observation)):
            raise ValueError("invalid_hit_text")
        if hit.evidence_tier not in _TIER_WEIGHT:
            raise ValueError("invalid_evidence_tier")
        if not _valid_score(hit.relevance):
            raise ValueError("invalid_relevance")
        grouped.setdefault(hit.canonical_key, []).append(hit)

    fused: list[FusedFinding] = []
    for key, group in grouped.items():
        unique_sources = sorted({item.source_id for item in group})
        ranked = sorted(
            group,
            key=lambda h: (-_TIER_WEIGHT[h.evidence_tier], -h.relevance, h.source_id),
        )
        best = ranked[0]
        corroboration_bonus = min(20, (len(unique_sources) - 1) * 5)
        score = min(100, best.relevance + corroboration_bonus)
        fused.append(
            FusedFinding(
                canonical_key=key,
                title=best.title,
                best_observation=best.raw_observation,
                evidence_tier=best.evidence_tier,
                supporting_sources=tuple(unique_sources),
                score=score,
            )
        )
    return tuple(sorted(fused, key=lambda item: (-item.score, item.canonical_key)))
