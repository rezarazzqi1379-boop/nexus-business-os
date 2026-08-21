from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Literal

SourceKind = Literal["official", "regulatory", "academic", "company", "news", "web", "crm", "email"]
EvidenceTier = Literal["strong", "partial", "weak", "unverified"]
ClaimStance = Literal["support", "refute", "uncertain"]

_ALLOWED_SOURCE_KINDS = {"official", "regulatory", "academic", "company", "news", "web", "crm", "email"}
_TIER_WEIGHT = {"strong": 4, "partial": 3, "weak": 2, "unverified": 1}
_ALLOWED_STANCES = {"support", "refute", "uncertain"}
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
    stance: ClaimStance = "support"
    independence_key: str | None = None


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
    refuting_sources: tuple[str, ...]
    uncertain_sources: tuple[str, ...]
    contradiction: bool
    score: int


@dataclass(frozen=True)
class RetrievalBenchmark:
    single_source_score: int
    multi_source_score: int
    source_count: int
    contradiction_detected: bool
    improved: bool


@dataclass(frozen=True)
class RetrievalSchedule:
    query_id: str
    waves: tuple[tuple[str, ...], ...]
    max_parallel: int


@dataclass(frozen=True)
class ResearchOutcome:
    source_id: str
    useful: bool
    latency_ms: int


@dataclass(frozen=True)
class SourceLearning:
    source_id: str
    observations: int
    useful_count: int
    average_latency_ms: int
    recommendation: Literal["insufficient_evidence", "prefer", "hold", "review"]


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


def _source_rank_key(source: ResearchSource) -> tuple[float, float, int, str]:
    """Rank confidence first, then prefer fresher evidence before latency."""
    retrieved_at = _aware_iso(source.retrieved_at)
    if retrieved_at is None:
        raise ValueError("invalid_retrieved_at")
    return (-source.confidence, -retrieved_at.timestamp(), source.latency_ms, source.source_id)


def plan_sources(query: ResearchQuery, sources: Iterable[ResearchSource]) -> ResearchPlan:
    """Select a bounded, confidence-led, freshness-aware and source-diverse retrieval set."""
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

    ranked = sorted(pool, key=_source_rank_key)
    selected: list[ResearchSource] = []
    used_kinds: set[str] = set()
    used_domains: set[str] = set()

    for source in ranked:
        if len(selected) >= query.max_sources:
            break
        domain_key = source.domain.casefold()
        if source.kind in used_kinds or domain_key in used_domains:
            continue
        selected.append(source)
        used_kinds.add(source.kind)
        used_domains.add(domain_key)

    if len(selected) < query.max_sources:
        selected_ids = {item.source_id for item in selected}
        for source in ranked:
            if len(selected) >= query.max_sources:
                break
            domain_key = source.domain.casefold()
            if source.source_id in selected_ids or domain_key in used_domains:
                continue
            selected.append(source)
            selected_ids.add(source.source_id)
            used_domains.add(domain_key)

    if len(selected) < query.max_sources:
        selected_ids = {item.source_id for item in selected}
        for source in ranked:
            if len(selected) >= query.max_sources:
                break
            if source.source_id in selected_ids:
                continue
            selected.append(source)
            selected_ids.add(source.source_id)

    selected_ids = {item.source_id for item in selected}
    rejected = tuple(source.source_id for source in ranked if source.source_id not in selected_ids)
    return ResearchPlan(query.query_id, tuple(source.source_id for source in selected), rejected)


def _validate_hit(hit: object) -> ResearchHit:
    if not isinstance(hit, ResearchHit):
        raise ValueError("invalid_hit")
    if not all(_bounded_text(value) for value in (hit.query_id, hit.source_id, hit.canonical_key, hit.title, hit.raw_observation)):
        raise ValueError("invalid_hit_text")
    if hit.independence_key is not None and not _bounded_text(hit.independence_key):
        raise ValueError("invalid_independence_key")
    if hit.evidence_tier not in _TIER_WEIGHT:
        raise ValueError("invalid_evidence_tier")
    if not _valid_score(hit.relevance):
        raise ValueError("invalid_relevance")
    if hit.stance not in _ALLOWED_STANCES:
        raise ValueError("invalid_stance")
    return hit


def _independence_key(hit: ResearchHit) -> str:
    return hit.independence_key or hit.source_id


def fuse_hits(hits: Iterable[ResearchHit]) -> tuple[FusedFinding, ...]:
    """Fuse evidence without collapsing contradictions or correlated evidence into false consensus."""
    try:
        items = tuple(hits)
    except TypeError as exc:
        raise ValueError("hits_must_be_iterable") from exc
    grouped: dict[str, list[ResearchHit]] = {}
    query_ids: set[str] = set()
    for raw_hit in items:
        hit = _validate_hit(raw_hit)
        query_ids.add(hit.query_id)
        grouped.setdefault(hit.canonical_key, []).append(hit)
    if len(query_ids) > 1:
        raise ValueError("fuse_requires_one_query")

    fused: list[FusedFinding] = []
    for key, group in grouped.items():
        supporting = sorted({item.source_id for item in group if item.stance == "support"})
        refuting = sorted({item.source_id for item in group if item.stance == "refute"})
        uncertain = sorted({item.source_id for item in group if item.stance == "uncertain"})
        contradiction = bool(supporting and refuting)

        ranked = sorted(group, key=lambda h: (-_TIER_WEIGHT[h.evidence_tier], -h.relevance, h.source_id))
        best = ranked[0]
        independent_origins = {_independence_key(item) for item in group}
        corroboration_bonus = min(20, max(0, len(independent_origins) - 1) * 5)
        contradiction_penalty = 20 if contradiction else 0
        uncertainty_penalty = min(10, len(uncertain) * 3)
        score = max(0, min(100, best.relevance + corroboration_bonus - contradiction_penalty - uncertainty_penalty))

        fused.append(
            FusedFinding(
                canonical_key=key,
                title=best.title,
                best_observation=best.raw_observation,
                evidence_tier=best.evidence_tier,
                supporting_sources=tuple(supporting),
                refuting_sources=tuple(refuting),
                uncertain_sources=tuple(uncertain),
                contradiction=contradiction,
                score=score,
            )
        )
    return tuple(sorted(fused, key=lambda item: (-item.score, item.canonical_key)))


def benchmark_retrieval(hits: Iterable[ResearchHit]) -> RetrievalBenchmark:
    """Compare a naive best-single-source baseline with contradiction-aware fusion.

    This is a deterministic retrieval-quality proxy, not a claim about final LLM answer quality.
    """
    try:
        items = tuple(hits)
    except TypeError as exc:
        raise ValueError("hits_must_be_iterable") from exc
    if not items:
        raise ValueError("benchmark_requires_hits")
    validated = tuple(_validate_hit(item) for item in items)
    if len({item.canonical_key for item in validated}) != 1:
        raise ValueError("benchmark_requires_one_claim")

    single = max(validated, key=lambda h: (_TIER_WEIGHT[h.evidence_tier], h.relevance, h.source_id))
    fused = fuse_hits(validated)[0]
    return RetrievalBenchmark(
        single_source_score=single.relevance,
        multi_source_score=fused.score,
        source_count=len({_independence_key(item) for item in validated}),
        contradiction_detected=fused.contradiction,
        improved=fused.score > single.relevance and not fused.contradiction,
    )


def schedule_retrieval(plan: ResearchPlan, *, max_parallel: int = 4) -> RetrievalSchedule:
    """Split a validated source plan into deterministic bounded parallel waves."""
    if not isinstance(plan, ResearchPlan) or not _bounded_text(plan.query_id):
        raise ValueError("invalid_research_plan")
    if (
        not isinstance(plan.selected_sources, tuple)
        or any(not _bounded_text(source_id) for source_id in plan.selected_sources)
        or len(set(plan.selected_sources)) != len(plan.selected_sources)
    ):
        raise ValueError("invalid_selected_sources")
    if not isinstance(max_parallel, int) or isinstance(max_parallel, bool) or not 1 <= max_parallel <= 6:
        raise ValueError("invalid_max_parallel")
    waves = tuple(tuple(plan.selected_sources[index:index + max_parallel]) for index in range(0, len(plan.selected_sources), max_parallel))
    return RetrievalSchedule(plan.query_id, waves, max_parallel)


def summarize_source_outcomes(outcomes: Iterable[ResearchOutcome]) -> tuple[SourceLearning, ...]:
    """Create reviewable source-learning signals without auto-changing trust scores."""
    try:
        items = tuple(outcomes)
    except TypeError as exc:
        raise ValueError("outcomes_must_be_iterable") from exc
    grouped: dict[str, list[ResearchOutcome]] = {}
    for outcome in items:
        if not isinstance(outcome, ResearchOutcome) or not _bounded_text(outcome.source_id):
            raise ValueError("invalid_outcome")
        if not isinstance(outcome.useful, bool):
            raise ValueError("invalid_outcome_useful")
        if not isinstance(outcome.latency_ms, int) or isinstance(outcome.latency_ms, bool) or outcome.latency_ms < 0:
            raise ValueError("invalid_outcome_latency")
        grouped.setdefault(outcome.source_id, []).append(outcome)

    learned: list[SourceLearning] = []
    for source_id, group in grouped.items():
        count = len(group)
        useful_count = sum(item.useful for item in group)
        average_latency = sum(item.latency_ms for item in group) // count
        if count < 3:
            recommendation = "insufficient_evidence"
        elif useful_count * 4 >= count * 3:
            recommendation = "prefer"
        elif useful_count * 2 >= count:
            recommendation = "hold"
        else:
            recommendation = "review"
        learned.append(SourceLearning(source_id, count, useful_count, average_latency, recommendation))
    return tuple(sorted(learned, key=lambda item: item.source_id))
