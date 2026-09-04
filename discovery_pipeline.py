"""Discovery Pipeline v0.1: turns Research Lab's storage into a deterministic,
project/lane-neutral discovery pipeline -- query expansion, normalization,
deduplication, conservative entity resolution, buyer classification, and
opportunity scoring, all over data already present in the record. No live
provider is shipped (``NullDiscoveryAdapter`` only, same rule as
research_evidence.py's ``NullSearchProvider``), no entity is ever auto-merged
across an ambiguity, and nothing here promotes a discovery to FACT or marks
anything as independently verified -- that requires a live, out-of-scope
verification step this module only queues candidates for.

Lane-neutral, same discipline as research_evidence.py/research_lab.py:
project_id/lane_id are carried through unchanged and never interpreted. The
only guard this module enforces is that a single dedup/entity-resolution
pass never silently mixes results declaring different project_id/lane_id --
not what those values are allowed to be.
"""

from __future__ import annotations

import itertools
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Mapping, Protocol, Sequence

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from contracts import EvidenceClass  # noqa: E402
from research_evidence import SearchResult  # noqa: E402
from research_lab import ResearchRunRecord, _unit_rate, _utc  # noqa: E402

SCHEMA_VERSION = "nexus.discovery-pipeline.v1"

BUYER_CATEGORIES = frozenset({
    "end_user_steel_mill", "foundry", "trader", "distributor", "importer",
    "procurement_authority", "unknown",
})
ENTITY_RESOLUTION_STATES = frozenset({"exact", "probable", "ambiguous", "unresolved"})
VERIFICATION_REQUIREMENTS = frozenset({"primary_source_required", "secondary_source_required"})

_PROCUREMENT_KEYWORDS = ("tender", "rfq", "procurement", "quotation", "bid ")
_TRADE_KEYWORDS = ("import", "export", "customs", "shipment", "trade")
_CONTACT_KEYWORDS = ("contact", "email", "phone", "inquiry", "enquiry")
_BUYER_CATEGORY_KEYWORDS = (
    ("end_user_steel_mill", ("steel mill", "steelmaker", "steel plant")),
    ("foundry", ("foundry", "casting plant")),
    ("distributor", ("distributor", "distribution")),
    ("importer", ("importer", "import company")),
    ("procurement_authority", ("procurement", "tender board", "purchasing authority")),
    ("trader", ("trader", "trading house", "trading company")),
)


def _text_of(result: "NormalizedDiscoveryResult") -> str:
    return f"{result.title} {result.snippet}".lower()


def _any_keyword(text: str, keywords: Sequence[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _recency_subscore(retrieved_at: str, published_at: str | None) -> float:
    if published_at is None:
        return 0.5
    age_days = (datetime.fromisoformat(retrieved_at) - datetime.fromisoformat(published_at)).days
    return 1.0 if age_days <= 30 else (0.6 if age_days <= 180 else 0.2)


@dataclass(frozen=True)
class QueryExpansionPlan:
    """A deterministic recipe for turning a commercial objective into concrete query strings.
    No live call is involved -- ``expand()`` is pure string combination.
    """

    objective: str
    product_terms: tuple[str, ...]
    buyer_role_terms: tuple[str, ...]
    procurement_terms: tuple[str, ...]
    industry_terms: tuple[str, ...]
    geography_terms: tuple[str, ...]
    language_variants: tuple[str, ...]
    query_set_version: str

    def validate(self) -> None:
        if not self.objective.strip():
            raise ValueError("invalid_objective")
        if not self.query_set_version.strip():
            raise ValueError("invalid_query_set_version")
        if not self.product_terms:
            raise ValueError("product_terms_required")
        if not self.geography_terms:
            raise ValueError("geography_terms_required")
        if not self.language_variants:
            raise ValueError("language_variants_required")
        for name, terms in (
            ("product_terms", self.product_terms), ("buyer_role_terms", self.buyer_role_terms),
            ("procurement_terms", self.procurement_terms), ("industry_terms", self.industry_terms),
            ("geography_terms", self.geography_terms), ("language_variants", self.language_variants),
        ):
            if any(not isinstance(t, str) or not t.strip() for t in terms):
                raise ValueError(f"invalid_{name}_entry")
            if len(set(terms)) != len(terms):
                raise ValueError(f"duplicate_{name}")

    def expand(self, *, max_queries: int = 500) -> tuple[str, ...]:
        """Deterministic, bounded, order-stable expansion. Combines each product term with a
        modifier drawn from buyer-role/procurement/industry terms and a geography term, then
        appends a language tag for any non-English variant.
        """
        self.validate()
        modifiers = tuple(dict.fromkeys((*self.buyer_role_terms, *self.procurement_terms, *self.industry_terms)))
        modifiers = modifiers or ("",)
        seen: set[str] = set()
        queries: list[str] = []
        for product, modifier, geography, language in itertools.product(
            self.product_terms, modifiers, self.geography_terms, self.language_variants
        ):
            base = " ".join(part for part in (product, modifier, geography) if part).strip()
            query = base if language.strip().lower() in ("en", "english") else f"{base} [{language}]"
            if query not in seen:
                seen.add(query)
                queries.append(query)
            if len(queries) >= max_queries:
                return tuple(queries)
        return tuple(queries)


class DiscoveryAdapter(Protocol):
    provider_id: str

    def discover(self, query: str, *, limit: int) -> tuple[SearchResult, ...]: ...


class NullDiscoveryAdapter:
    """The only adapter shipped in v0.1: no live credentials, no provider-specific logic here."""

    provider_id = "null-discovery-adapter"

    def discover(self, query: str, *, limit: int) -> tuple[SearchResult, ...]:
        return ()


def default_discovery_adapters() -> dict[str, DiscoveryAdapter]:
    """A fresh registry each call -- no shared mutable global, same rule as research_evidence.py."""
    return {NullDiscoveryAdapter.provider_id: NullDiscoveryAdapter()}


@dataclass(frozen=True)
class NormalizedDiscoveryResult:
    """One discovery hit immediately after normalization -- before entity extraction/resolution.
    evidence_class/verification_state are structurally locked to CLAIM/unverified: this stage
    has performed no verification, so it cannot claim otherwise.
    """

    provider: str
    url: str
    title: str
    snippet: str
    retrieved_at: str
    published_at: str | None
    project_id: str | None
    lane_id: str | None
    raw_query: str
    entity_hint: str | None
    evidence_class: EvidenceClass = EvidenceClass.CLAIM
    verification_state: str = "unverified"

    def validate(self) -> None:
        if not self.provider.strip():
            raise ValueError("invalid_provider")
        if not self.url.lower().startswith(("https://", "http://")):
            raise ValueError("invalid_url")
        if not self.title.strip():
            raise ValueError("invalid_title")
        if not self.snippet.strip():
            raise ValueError("invalid_snippet")
        _utc(self.retrieved_at, "retrieved_at")
        if self.published_at is not None:
            _utc(self.published_at, "published_at")
        if not self.raw_query.strip():
            raise ValueError("invalid_raw_query")
        if EvidenceClass(self.evidence_class) is not EvidenceClass.CLAIM:
            raise ValueError("normalized_discovery_result_must_be_claim")
        if self.verification_state != "unverified":
            raise ValueError("normalized_discovery_result_must_be_unverified")

    def to_research_run_record(self, *, run_id: str, query_set_version: str, source_type: str = "search_engine",
                               country: str | None = None, buyer_type: str | None = None,
                               product_signal: str | None = None) -> ResearchRunRecord:
        """Upgrade into research_lab.py's persisted, fully-enriched record shape once
        entity/buyer information (from a later stage) is available. Never sets FACT/verified.
        """
        return ResearchRunRecord(
            run_id=run_id, project_id=self.project_id, lane_id=self.lane_id,
            query_set_version=query_set_version, provider=self.provider, query=self.raw_query,
            url=self.url, source_type=source_type, retrieved_at=self.retrieved_at,
            published_at=self.published_at, entity_name=self.entity_hint, country=country,
            buyer_type=buyer_type, product_signal=product_signal, evidence_class=self.evidence_class,
            verification_state=self.verification_state,
        )


def _canonical_url(url: str) -> str:
    """Lowercase scheme/host, drop default scheme, strip trailing slash and fragment."""
    match = re.match(r"^(https?)://([^/]+)(/[^#?]*)?", url.strip(), re.IGNORECASE)
    if not match:
        return url.strip().lower()
    scheme, host, path = match.group(1).lower(), match.group(2).lower(), (match.group(3) or "").rstrip("/")
    return f"{scheme}://{host}{path}"


def normalize_entity_name(name: str | None) -> str:
    if not name:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", name.strip().lower()).strip()


def _assert_single_scope(results: Sequence[NormalizedDiscoveryResult]) -> None:
    scopes = {(r.project_id, r.lane_id) for r in results}
    if len(scopes) > 1:
        raise ValueError("cross_run_contamination:mixed_project_or_lane_scope")


@dataclass(frozen=True)
class DuplicateGroup:
    group_id: str
    canonical_key: str
    members: tuple[NormalizedDiscoveryResult, ...]

    @property
    def source_count(self) -> int:
        return len(self.members)


def group_duplicates(results: Sequence[NormalizedDiscoveryResult]) -> tuple[DuplicateGroup, ...]:
    """Deterministic dedup by canonicalized URL (fallback: normalized entity name). Every source
    reference is preserved in ``members`` -- nothing is discarded, even within one group.
    """
    _assert_single_scope(results)
    buckets: dict[str, list[NormalizedDiscoveryResult]] = {}
    order: list[str] = []
    for result in results:
        result.validate()
        key = _canonical_url(result.url) or f"entity:{normalize_entity_name(result.entity_hint)}"
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(result)
    return tuple(
        DuplicateGroup(group_id="dupgrp_" + sha256(key.encode()).hexdigest()[:16], canonical_key=key,
                       members=tuple(buckets[key]))
        for key in order
    )


def dedup_rate(groups: Sequence[DuplicateGroup]) -> float:
    total = sum(g.source_count for g in groups)
    if total == 0:
        return 0.0
    return 1 - (len(groups) / total)


def source_diversity(groups: Sequence[DuplicateGroup]) -> dict:
    members = [m for g in groups for m in g.members]
    return {"distinct_providers": len({m.provider for m in members}), "total_raw_results": len(members)}


@dataclass(frozen=True)
class EntityResolutionCandidate:
    """Conservative entity resolution: never auto-merges an ambiguity into a single identity."""

    candidate_id: str
    normalized_name: str
    supporting_group_ids: tuple[str, ...]
    resolution_state: str
    reason: str

    def validate(self) -> None:
        if self.resolution_state not in ENTITY_RESOLUTION_STATES:
            raise ValueError("invalid_resolution_state")


def resolve_entities(groups: Sequence[DuplicateGroup]) -> tuple[EntityResolutionCandidate, ...]:
    """- unresolved: no group member carries an entity_hint.
    - ambiguous: a single duplicate group's members carry more than one distinct normalized
      entity_hint -- conflicting evidence within one group is never merged into a guess.
    - exact: the same normalized name is independently supported by >= 2 duplicate groups.
    - probable: the normalized name is supported by exactly one duplicate group.
    """
    by_name: dict[str, list[DuplicateGroup]] = {}
    ambiguous: list[tuple[DuplicateGroup, tuple[str, ...]]] = []
    unresolved: list[DuplicateGroup] = []
    for group in groups:
        hints = tuple(dict.fromkeys(
            normalize_entity_name(m.entity_hint) for m in group.members if m.entity_hint and m.entity_hint.strip()
        ))
        if not hints:
            unresolved.append(group)
        elif len(hints) > 1:
            ambiguous.append((group, hints))
        else:
            by_name.setdefault(hints[0], []).append(group)

    candidates: list[EntityResolutionCandidate] = []
    for name in sorted(by_name):
        supporting = by_name[name]
        state = "exact" if len(supporting) >= 2 else "probable"
        candidates.append(EntityResolutionCandidate(
            candidate_id="ent_" + sha256(name.encode()).hexdigest()[:16], normalized_name=name,
            supporting_group_ids=tuple(g.group_id for g in supporting), resolution_state=state,
            reason=f"{len(supporting)} duplicate group(s) independently share this normalized name",
        ))
    for group, hints in sorted(ambiguous, key=lambda item: item[0].group_id):
        candidates.append(EntityResolutionCandidate(
            candidate_id="ent_" + sha256((group.group_id + "|ambiguous").encode()).hexdigest()[:16],
            normalized_name="|".join(sorted(hints)), supporting_group_ids=(group.group_id,),
            resolution_state="ambiguous",
            reason=f"conflicting entity hints within one duplicate group: {sorted(hints)}",
        ))
    for group in sorted(unresolved, key=lambda g: g.group_id):
        candidates.append(EntityResolutionCandidate(
            candidate_id="ent_" + sha256((group.group_id + "|unresolved").encode()).hexdigest()[:16],
            normalized_name="", supporting_group_ids=(group.group_id,), resolution_state="unresolved",
            reason="no entity hint present on any member",
        ))
    return tuple(candidates)


@dataclass(frozen=True)
class BuyerClassification:
    entity_candidate_id: str
    category: str
    confidence: float
    basis: str

    def validate(self) -> None:
        if self.category not in BUYER_CATEGORIES:
            raise ValueError("invalid_buyer_category")
        _unit_rate(self.confidence, "confidence")
        if not self.basis.strip():
            raise ValueError("invalid_basis")


def classify_buyer(candidate: EntityResolutionCandidate, groups_by_id: Mapping[str, DuplicateGroup]) -> BuyerClassification:
    """Deterministic keyword classification over text the results already carry -- never an
    invented fact about a real company. No keyword match means "unknown", confidence 0.0.
    """
    members = [m for gid in candidate.supporting_group_ids for m in groups_by_id[gid].members]
    text = " ".join(_text_of(m) for m in members)
    for category, keywords in _BUYER_CATEGORY_KEYWORDS:
        matches = sum(1 for keyword in keywords if keyword in text)
        if matches:
            confidence = min(0.5 + 0.1 * matches, 0.9)
            return BuyerClassification(candidate.candidate_id, category, confidence,
                                       f"keyword match in title/snippet: {category}")
    return BuyerClassification(candidate.candidate_id, "unknown", 0.0, "no buyer-category keyword matched")


_RESOLUTION_DEPTH = {"exact": 1.0, "probable": 0.5, "ambiguous": 0.2, "unresolved": 0.0}


@dataclass(frozen=True)
class DiscoveryScoreWeights:
    procurement_recency: float
    product_fit: float
    buyer_role: float
    trade_signal: float
    source_diversity: float
    verification_depth: float
    geography_fit: float
    contactability: float
    evidence_freshness: float

    def validate(self) -> None:
        values = (self.procurement_recency, self.product_fit, self.buyer_role, self.trade_signal,
                 self.source_diversity, self.verification_depth, self.geography_fit,
                 self.contactability, self.evidence_freshness)
        if not abs(sum(values) - 1.0) < 1e-9:
            raise ValueError("weights_must_sum_to_one")
        for value in values:
            _unit_rate(value, "discovery_score_weight")


DEFAULT_DISCOVERY_SCORE_WEIGHTS = DiscoveryScoreWeights(
    procurement_recency=0.15, product_fit=0.2, buyer_role=0.15, trade_signal=0.1,
    source_diversity=0.1, verification_depth=0.15, geography_fit=0.05, contactability=0.05,
    evidence_freshness=0.05,
)


@dataclass(frozen=True)
class ScoredEntity:
    entity_candidate_id: str
    score: float
    breakdown: Mapping[str, float]


def score_entity(candidate: EntityResolutionCandidate, groups_by_id: Mapping[str, DuplicateGroup],
                classification: BuyerClassification, *, geography_terms: tuple[str, ...] = (),
                weights: DiscoveryScoreWeights = DEFAULT_DISCOVERY_SCORE_WEIGHTS) -> ScoredEntity:
    """Every sub-score is computed only from fields already present -- never a fabricated
    number. Deterministic: identical inputs always yield the identical score and breakdown.
    """
    weights.validate()
    members = [m for gid in candidate.supporting_group_ids for m in groups_by_id[gid].members]
    if not members:
        raise ValueError("no_supporting_members_for_scoring")

    procurement_members = [m for m in members if _any_keyword(_text_of(m), _PROCUREMENT_KEYWORDS)]
    procurement_recency = (
        max(_recency_subscore(m.retrieved_at, m.published_at) for m in procurement_members)
        if procurement_members else 0.0
    )
    query_tokens = {t for m in members for t in re.findall(r"[a-z0-9]+", m.raw_query.lower())}
    text_tokens = {t for m in members for t in re.findall(r"[a-z0-9]+", _text_of(m))}
    product_fit = (len(query_tokens & text_tokens) / len(query_tokens)) if query_tokens else 0.0
    buyer_role = classification.confidence if classification.category != "unknown" else 0.0
    trade_signal = sum(1 for m in members if _any_keyword(_text_of(m), _TRADE_KEYWORDS)) / len(members)
    diversity = min(len({m.provider for m in members}) / 3, 1.0)
    verification_depth = _RESOLUTION_DEPTH[candidate.resolution_state]
    geography_fit = (
        (sum(1 for m in members if _any_keyword(_text_of(m), tuple(t.lower() for t in geography_terms))) / len(members))
        if geography_terms else 0.5
    )
    contactability = sum(1 for m in members if _any_keyword(_text_of(m), _CONTACT_KEYWORDS)) / len(members)
    evidence_freshness = max(_recency_subscore(m.retrieved_at, m.published_at) for m in members)

    breakdown = {
        "procurement_recency": procurement_recency, "product_fit": product_fit, "buyer_role": buyer_role,
        "trade_signal": trade_signal, "source_diversity": diversity, "verification_depth": verification_depth,
        "geography_fit": geography_fit, "contactability": contactability, "evidence_freshness": evidence_freshness,
    }
    score = sum(getattr(weights, name) * value for name, value in breakdown.items())
    return ScoredEntity(candidate.candidate_id, score, breakdown)


@dataclass(frozen=True)
class VerificationQueueItem:
    entity_candidate_id: str
    score: float
    requirement: str
    reason: str

    def validate(self) -> None:
        if self.requirement not in VERIFICATION_REQUIREMENTS:
            raise ValueError("invalid_verification_requirement")


def build_verification_queue(scored: Sequence[ScoredEntity], *, top_n: int = 20,
                            primary_threshold: float = 0.7) -> tuple[VerificationQueueItem, ...]:
    """Every top-ranked candidate requires verification before being treated as actionable --
    this only assigns which TIER is required. It never performs verification and never marks
    anything as verified; that is a separate, live, out-of-scope step.
    """
    ranked = sorted(scored, key=lambda s: (-s.score, s.entity_candidate_id))[:max(top_n, 0)]
    items = []
    for entity in ranked:
        requirement = "primary_source_required" if entity.score >= primary_threshold else "secondary_source_required"
        items.append(VerificationQueueItem(entity.entity_candidate_id, entity.score, requirement,
                                           f"ranked in top {top_n} by opportunity score ({entity.score:.3f})"))
    return tuple(items)
