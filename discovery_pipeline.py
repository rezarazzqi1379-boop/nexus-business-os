"""Discovery Pipeline v0.1: turns Research Lab's storage into a deterministic,
project/lane-neutral discovery pipeline -- query expansion, normalization,
a two-stage deduplication/entity-resolution engine, buyer classification
(logistics intermediaries included, and never conflated with buyers), 9-input
opportunity scoring, and a verification-tier queue. No live provider is
shipped (``NullDiscoveryAdapter`` only, same rule as research_evidence.py's
``NullSearchProvider``), no entity is ever auto-merged across an ambiguity,
and nothing here promotes a discovery to FACT or marks anything as
independently verified -- that requires a live, out-of-scope step this
module only queues candidates for.

Two distinct, deliberately different concepts:
  * "dedup category" (exact_duplicate/probable_duplicate/ambiguous/unique) is
    a per-record-group judgment: do these specific raw hits describe the
    same underlying discovery?
  * "resolution state" (exact/probable/ambiguous/unresolved) is a
    per-entity judgment made *after* dedup: is the company behind these
    (possibly several) groups the same real-world entity?

Lane-neutral, same discipline as research_evidence.py/research_lab.py:
project_id/lane_id are carried through unchanged and never interpreted. The
only guard this module enforces is that a single pipeline run never
silently mixes results declaring different project_id/lane_id.
"""

from __future__ import annotations

import itertools
import json
import re
import sys
import time
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
from research_lab import ResearchLabStore, ResearchRun, ResearchRunRecord, _unit_rate, _utc  # noqa: E402

SCHEMA_VERSION = "nexus.discovery-pipeline.v2"

BUYER_CATEGORIES = frozenset({
    "steel_mill", "foundry", "importer", "trader", "distributor",
    "procurement_authority", "logistics_intermediary", "unknown",
})
DEDUP_CATEGORIES = frozenset({"exact_duplicate", "probable_duplicate", "ambiguous", "unique"})
ENTITY_RESOLUTION_STATES = frozenset({"exact", "probable", "ambiguous", "unresolved"})
VERIFICATION_REQUIREMENTS = frozenset({"primary_source_required", "secondary_source_required"})

_PROCUREMENT_KEYWORDS = ("tender", "rfq", "procurement", "quotation", "bid ")
_IMPORT_SIGNAL_KEYWORDS = ("import", "export", "customs", "shipment", "trade")
_CONTACT_KEYWORDS = ("contact", "email", "phone", "inquiry", "enquiry")
_HIGH_QUALITY_URL_SIGNALS = ("gov", "customs", "tender", "procurement", "chamber")
_STALE_AGE_DAYS = 365

# Logistics/forwarding keywords are checked FIRST, before any other buyer category, so a
# high-shipment-count freight forwarder (e.g. "Bsm Forwarding") is never misclassified as an
# end buyer merely because it appears often in trade data.
_BUYER_CATEGORY_KEYWORDS = (
    ("logistics_intermediary", ("forwarding", "freight", "logistics", "shipping agent", "customs broker", "3pl")),
    ("steel_mill", ("steel mill", "steelmaker", "steel plant")),
    ("foundry", ("foundry", "casting plant")),
    ("importer", ("importer", "import company")),
    ("distributor", ("distributor", "distribution")),
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


def _is_stale(retrieved_at: str, published_at: str | None) -> bool:
    if published_at is None:
        return False
    age_days = (datetime.fromisoformat(retrieved_at) - datetime.fromisoformat(published_at)).days
    return age_days > _STALE_AGE_DAYS


@dataclass(frozen=True)
class QueryExpansionPlan:
    """A deterministic recipe for turning a commercial objective into concrete query strings.
    No live call is involved -- ``expand()`` is pure string combination. project_id/lane_id
    are carried through unchanged, same lane-neutral discipline as the rest of this module.
    """

    objective: str
    project_id: str | None
    lane_id: str | None
    query_set_version: str
    product_terms: tuple[str, ...]
    buyer_terms: tuple[str, ...]
    procurement_terms: tuple[str, ...]
    industry_terms: tuple[str, ...]
    geography_terms: tuple[str, ...]
    language_terms: tuple[str, ...]

    def validate(self) -> None:
        if not self.objective.strip():
            raise ValueError("invalid_objective")
        if not self.query_set_version.strip():
            raise ValueError("invalid_query_set_version")
        if not self.product_terms:
            raise ValueError("product_terms_required")
        if not self.geography_terms:
            raise ValueError("geography_terms_required")
        if not self.language_terms:
            raise ValueError("language_terms_required")
        for name, terms in (
            ("product_terms", self.product_terms), ("buyer_terms", self.buyer_terms),
            ("procurement_terms", self.procurement_terms), ("industry_terms", self.industry_terms),
            ("geography_terms", self.geography_terms), ("language_terms", self.language_terms),
        ):
            if any(not isinstance(t, str) or not t.strip() for t in terms):
                raise ValueError(f"invalid_{name}_entry")
            if len(set(terms)) != len(terms):
                raise ValueError(f"duplicate_{name}")

    def expand(self, *, max_queries: int = 500) -> tuple[str, ...]:
        """Deterministic, bounded, order-stable expansion: each product term combined with a
        modifier (buyer/procurement/industry terms) and a geography term, tagged with any
        non-English language variant.
        """
        self.validate()
        modifiers = tuple(dict.fromkeys((*self.buyer_terms, *self.procurement_terms, *self.industry_terms))) or ("",)
        seen: set[str] = set()
        queries: list[str] = []
        for product, modifier, geography, language in itertools.product(
            self.product_terms, modifiers, self.geography_terms, self.language_terms
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

    source_is_multi_entity_listing defaults to False (a URL is assumed to describe one entity,
    the historical assumption). Set it True only when the URL is known to be a directory/listing
    page that legitimately names several distinct entities (a customs importer list, a B2B buyer
    directory, a marketplace search-results page) -- see group_duplicates() for how this changes
    dedup behavior for that URL.
    """

    provider: str
    query: str
    url: str
    title: str
    snippet: str
    retrieved_at: str
    published_at: str | None
    project_id: str | None
    lane_id: str | None
    entity_name_hint: str | None
    country_hint: str | None
    buyer_type_hint: str | None
    source_is_multi_entity_listing: bool = False
    evidence_class: EvidenceClass = EvidenceClass.CLAIM
    verification_state: str = "unverified"

    def validate(self) -> None:
        if not self.provider.strip():
            raise ValueError("invalid_provider")
        if not self.query.strip():
            raise ValueError("invalid_query")
        if not self.url.lower().startswith(("https://", "http://")):
            raise ValueError("invalid_url")
        if not self.title.strip():
            raise ValueError("invalid_title")
        if not self.snippet.strip():
            raise ValueError("invalid_snippet")
        _utc(self.retrieved_at, "retrieved_at")
        if self.published_at is not None:
            _utc(self.published_at, "published_at")
        if self.buyer_type_hint is not None and self.buyer_type_hint not in BUYER_CATEGORIES:
            raise ValueError("invalid_buyer_type_hint")
        if EvidenceClass(self.evidence_class) is not EvidenceClass.CLAIM:
            raise ValueError("normalized_discovery_result_must_be_claim")
        if self.verification_state != "unverified":
            raise ValueError("normalized_discovery_result_must_be_unverified")

    def to_research_run_record(self, *, run_id: str, query_set_version: str, source_type: str = "search_engine",
                               buyer_type: str | None = None, product_signal: str | None = None) -> ResearchRunRecord:
        """Upgrade into research_lab.py's persisted, fully-enriched record shape once
        entity/buyer information (from a later stage) is available. Never sets FACT/verified.
        """
        return ResearchRunRecord(
            run_id=run_id, project_id=self.project_id, lane_id=self.lane_id,
            query_set_version=query_set_version, provider=self.provider, query=self.query,
            url=self.url, source_type=source_type, retrieved_at=self.retrieved_at,
            published_at=self.published_at, entity_name=self.entity_name_hint, country=self.country_hint,
            buyer_type=buyer_type or self.buyer_type_hint, product_signal=product_signal,
            evidence_class=self.evidence_class, verification_state=self.verification_state,
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
    dedup_category: str
    members: tuple[NormalizedDiscoveryResult, ...]
    related_group_ids: tuple[str, ...] = ()

    @property
    def source_count(self) -> int:
        return len(self.members)

    def validate(self) -> None:
        if self.dedup_category not in DEDUP_CATEGORIES:
            raise ValueError("invalid_dedup_category")


def group_duplicates(results: Sequence[NormalizedDiscoveryResult]) -> tuple[DuplicateGroup, ...]:
    """Two-signal dedup, never losing a provenance record:

    1. Records sharing the exact same canonicalized URL become one group, category
       "exact_duplicate" (or "unique" if it's the only member) -- UNLESS the URL is explicitly
       flagged by the caller as a multi-entity listing (source_is_multi_entity_listing=True on
       at least one member) AND its members carry more than one distinct normalized
       entity_name_hint. In that case the URL bucket is split into one group per distinct name
       (plus one singleton group per member with no name at all), because a shared listing or
       directory URL does not mean the records describe the same entity. Without that explicit
       flag, conflicting name hints under one shared URL are never guessed at -- they stay one
       group and fall through to (2)/resolve_entities' "ambiguous" handling, exactly as before,
       because from the data alone a same-URL name conflict could just as easily be a data-entry
       mismatch about a single entity as a real multi-entity listing.
    2. Across *different* URL groups, a shared normalized entity_name_hint links them as
       "probable_duplicate" -- unless their country_hint values disagree, in which case both
       become "ambiguous" instead. A group already "exact_duplicate" keeps that label; URL
       identity is the stronger signal.
    """
    _assert_single_scope(results)
    for result in results:
        result.validate()

    url_order: list[str] = []
    url_buckets: dict[str, list[NormalizedDiscoveryResult]] = {}
    for index, result in enumerate(results):
        key = _canonical_url(result.url) or f"__no_url__:{index}"
        if key not in url_buckets:
            url_buckets[key] = []
            url_order.append(key)
        url_buckets[key].append(result)

    groups: list[dict] = []
    for key in url_order:
        members = url_buckets[key]
        distinct_names = {
            normalize_entity_name(m.entity_name_hint) for m in members
            if m.entity_name_hint and normalize_entity_name(m.entity_name_hint)
        }
        is_flagged_listing = any(m.source_is_multi_entity_listing for m in members)
        if is_flagged_listing and len(distinct_names) > 1:
            by_name: dict[str, list[NormalizedDiscoveryResult]] = {}
            unnamed: list[NormalizedDiscoveryResult] = []
            for m in members:
                name = normalize_entity_name(m.entity_name_hint) if m.entity_name_hint else ""
                if name:
                    by_name.setdefault(name, []).append(m)
                else:
                    unnamed.append(m)
            for name in sorted(by_name):
                named_members = by_name[name]
                groups.append({"key": key, "members": tuple(named_members),
                               "category": "exact_duplicate" if len(named_members) > 1 else "unique",
                               "related": set()})
            for m in unnamed:
                groups.append({"key": key, "members": (m,), "category": "unique", "related": set()})
        else:
            groups.append({"key": key, "members": tuple(members),
                           "category": "exact_duplicate" if len(members) > 1 else "unique",
                           "related": set()})

    name_to_group_indices: dict[str, list[int]] = {}
    for index, group in enumerate(groups):
        names = {normalize_entity_name(m.entity_name_hint) for m in group["members"] if m.entity_name_hint}
        for name in names:
            if name:
                name_to_group_indices.setdefault(name, []).append(index)

    for indices in name_to_group_indices.values():
        if len(indices) < 2:
            continue
        countries = {
            normalize_entity_name(m.country_hint)
            for i in indices for m in groups[i]["members"] if m.country_hint
        }
        conflict = len(countries) > 1
        for i in indices:
            groups[i]["related"].update(j for j in indices if j != i)
            if groups[i]["category"] == "exact_duplicate":
                continue
            groups[i]["category"] = "ambiguous" if conflict else "probable_duplicate"

    finalized: list[DuplicateGroup] = []
    ids_by_index = [f"dupgrp_{sha256((g['key'] + str(i)).encode()).hexdigest()[:16]}" for i, g in enumerate(groups)]
    for index, group in enumerate(groups):
        finalized.append(DuplicateGroup(
            group_id=ids_by_index[index], canonical_key=group["key"], dedup_category=group["category"],
            members=group["members"], related_group_ids=tuple(sorted(ids_by_index[j] for j in group["related"])),
        ))
    return tuple(finalized)


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
    """Conservative entity resolution over dedup groups: never auto-merges an ambiguity."""

    candidate_id: str
    normalized_name: str
    supporting_group_ids: tuple[str, ...]
    resolution_state: str
    reason: str

    def validate(self) -> None:
        if self.resolution_state not in ENTITY_RESOLUTION_STATES:
            raise ValueError("invalid_resolution_state")


def resolve_entities(groups: Sequence[DuplicateGroup]) -> tuple[EntityResolutionCandidate, ...]:
    """- unresolved: no group member carries an entity_name_hint.
    - ambiguous: a single duplicate group's members carry more than one distinct normalized
      entity_name_hint -- conflicting evidence within one group is never merged into a guess.
    - exact: the same normalized name is independently supported by >= 2 duplicate groups.
    - probable: the normalized name is supported by exactly one duplicate group.
    """
    by_name: dict[str, list[DuplicateGroup]] = {}
    ambiguous: list[tuple[DuplicateGroup, tuple[str, ...]]] = []
    unresolved: list[DuplicateGroup] = []
    for group in groups:
        hints = tuple(dict.fromkeys(
            normalize_entity_name(m.entity_name_hint) for m in group.members
            if m.entity_name_hint and m.entity_name_hint.strip()
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

    @property
    def is_buyer_opportunity(self) -> bool:
        """A logistics intermediary (or unknown) is never treated as an end-buyer opportunity,
        regardless of how many sources/shipments support the candidate."""
        return self.category not in {"unknown", "logistics_intermediary"}


def classify_buyer(candidate: EntityResolutionCandidate, groups_by_id: Mapping[str, DuplicateGroup]) -> BuyerClassification:
    """Deterministic keyword classification over text the results already carry -- never an
    invented fact about a real company, and never influenced by mention/shipment volume:
    logistics/forwarding keywords are checked first so a frequently-appearing freight
    forwarder is classified as an intermediary, not promoted to a buyer category just
    because it has many supporting records.
    """
    members = [m for gid in candidate.supporting_group_ids for m in groups_by_id[gid].members]
    text = " ".join(_text_of(m) for m in members)
    for category, keywords in _BUYER_CATEGORY_KEYWORDS:
        matches = sum(1 for keyword in keywords if keyword in text)
        if matches:
            confidence = min(0.5 + 0.1 * matches, 0.9)
            return BuyerClassification(candidate.candidate_id, category, confidence,
                                       f"keyword match in title/snippet: {category}")
    hinted = {m.buyer_type_hint for m in members if m.buyer_type_hint}
    if len(hinted) == 1:
        return BuyerClassification(candidate.candidate_id, next(iter(hinted)), 0.3, "single consistent buyer_type_hint")
    return BuyerClassification(candidate.candidate_id, "unknown", 0.0, "no buyer-category keyword or hint matched")


_RESOLUTION_DEPTH = {"exact": 1.0, "probable": 0.5, "ambiguous": 0.2, "unresolved": 0.0}


@dataclass(frozen=True)
class DiscoveryScoreWeights:
    product_fit: float
    procurement_recency: float
    import_signal: float
    source_diversity: float
    source_quality: float
    verification_depth: float
    geography_fit: float
    contactability: float
    evidence_freshness: float

    def validate(self) -> None:
        values = (self.product_fit, self.procurement_recency, self.import_signal, self.source_diversity,
                 self.source_quality, self.verification_depth, self.geography_fit, self.contactability,
                 self.evidence_freshness)
        if not abs(sum(values) - 1.0) < 1e-9:
            raise ValueError("weights_must_sum_to_one")
        for value in values:
            _unit_rate(value, "discovery_score_weight")


DEFAULT_DISCOVERY_SCORE_WEIGHTS = DiscoveryScoreWeights(
    product_fit=0.2, procurement_recency=0.15, import_signal=0.1, source_diversity=0.1,
    source_quality=0.1, verification_depth=0.15, geography_fit=0.1, contactability=0.05,
    evidence_freshness=0.05,
)


@dataclass(frozen=True)
class ScoredEntity:
    entity_candidate_id: str
    score: float
    breakdown: Mapping[str, float]


def score_entity(candidate: EntityResolutionCandidate, groups_by_id: Mapping[str, DuplicateGroup],
                *, geography_terms: tuple[str, ...] = (),
                weights: DiscoveryScoreWeights = DEFAULT_DISCOVERY_SCORE_WEIGHTS) -> ScoredEntity:
    """Every sub-score is computed only from fields already present -- never a fabricated
    number. Deterministic: identical inputs always yield the identical score and breakdown.
    """
    weights.validate()
    members = [m for gid in candidate.supporting_group_ids for m in groups_by_id[gid].members]
    if not members:
        raise ValueError("no_supporting_members_for_scoring")

    query_tokens = {t for m in members for t in re.findall(r"[a-z0-9]+", m.query.lower())}
    text_tokens = {t for m in members for t in re.findall(r"[a-z0-9]+", _text_of(m))}
    product_fit = (len(query_tokens & text_tokens) / len(query_tokens)) if query_tokens else 0.0

    procurement_members = [m for m in members if _any_keyword(_text_of(m), _PROCUREMENT_KEYWORDS)]
    procurement_recency = (
        max(_recency_subscore(m.retrieved_at, m.published_at) for m in procurement_members)
        if procurement_members else 0.0
    )
    import_signal = sum(1 for m in members if _any_keyword(_text_of(m), _IMPORT_SIGNAL_KEYWORDS)) / len(members)
    diversity = min(len({m.provider for m in members}) / 3, 1.0)
    quality_hits = sum(1 for m in members if any(sig in m.url.lower() for sig in _HIGH_QUALITY_URL_SIGNALS))
    source_quality = min(0.4 + 0.2 * quality_hits, 1.0) if quality_hits else 0.3
    verification_depth = _RESOLUTION_DEPTH[candidate.resolution_state]
    geography_fit = (
        (sum(1 for m in members if _any_keyword(_text_of(m), tuple(t.lower() for t in geography_terms))) / len(members))
        if geography_terms else 0.5
    )
    contactability = sum(1 for m in members if _any_keyword(_text_of(m), _CONTACT_KEYWORDS)) / len(members)
    evidence_freshness = max(_recency_subscore(m.retrieved_at, m.published_at) for m in members)

    breakdown = {
        "product_fit": product_fit, "procurement_recency": procurement_recency, "import_signal": import_signal,
        "source_diversity": diversity, "source_quality": source_quality, "verification_depth": verification_depth,
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


def build_verification_queue(scored: Sequence[ScoredEntity], classifications_by_id: Mapping[str, BuyerClassification],
                            *, top_n: int = 20, primary_threshold: float = 0.7) -> tuple[VerificationQueueItem, ...]:
    """Every top-ranked BUYER candidate requires verification before promotion from candidate
    to verified opportunity -- this only assigns which TIER is required, never performs
    verification, and never marks anything verified. A candidate classified as
    logistics_intermediary (or unknown) is excluded here: it is not a buyer opportunity to
    verify, regardless of its raw score.
    """
    buyer_scored = [
        s for s in scored
        if s.entity_candidate_id in classifications_by_id
        and classifications_by_id[s.entity_candidate_id].is_buyer_opportunity
    ]
    ranked = sorted(buyer_scored, key=lambda s: (-s.score, s.entity_candidate_id))[:max(top_n, 0)]
    items = []
    for entity in ranked:
        requirement = "primary_source_required" if entity.score >= primary_threshold else "secondary_source_required"
        items.append(VerificationQueueItem(entity.entity_candidate_id, entity.score, requirement,
                                           f"ranked in top {top_n} by opportunity score ({entity.score:.3f})"))
    return tuple(items)


@dataclass(frozen=True)
class RunMetrics:
    schema_version: str
    run_id: str
    raw_count: int
    unique_count: int
    duplicate_rate: float
    source_diversity: Mapping[str, int]
    plausible_buyer_count: int
    verified_buyer_count: int
    false_positive_rate: float | None
    stale_result_rate: float
    processing_time: float


def compute_run_metrics(run_id: str, results: Sequence[NormalizedDiscoveryResult],
                        groups: Sequence[DuplicateGroup], classifications: Sequence[BuyerClassification],
                        *, processing_time: float) -> RunMetrics:
    """Every field here is computed only from data already produced by this pipeline.
    false_positive_rate is None, not a fabricated number: it requires an actual verification
    outcome, which no stage in this module performs.
    """
    plausible_buyers = sum(1 for c in classifications if c.is_buyer_opportunity and c.confidence > 0)
    verified_buyers = sum(1 for r in results if r.verification_state == "verified")
    stale_count = sum(1 for r in results if _is_stale(r.retrieved_at, r.published_at))
    return RunMetrics(
        schema_version=SCHEMA_VERSION, run_id=run_id, raw_count=len(results), unique_count=len(groups),
        duplicate_rate=dedup_rate(groups), source_diversity=source_diversity(groups),
        plausible_buyer_count=plausible_buyers, verified_buyer_count=verified_buyers,
        false_positive_rate=None, stale_result_rate=(stale_count / len(results)) if results else 0.0,
        processing_time=processing_time,
    )


@dataclass(frozen=True)
class DiscoveryRunOutcome:
    run: ResearchRun
    groups: tuple[DuplicateGroup, ...]
    entities: tuple[EntityResolutionCandidate, ...]
    classifications: tuple[BuyerClassification, ...]
    scored: tuple[ScoredEntity, ...]
    verification_queue: tuple[VerificationQueueItem, ...]
    metrics: RunMetrics


def process_discovery_batch(run: ResearchRun, results: Sequence[NormalizedDiscoveryResult], *,
                            weights: DiscoveryScoreWeights = DEFAULT_DISCOVERY_SCORE_WEIGHTS,
                            geography_terms: tuple[str, ...] = (), top_n: int = 20,
                            primary_threshold: float = 0.7,
                            store: ResearchLabStore | None = None) -> DiscoveryRunOutcome:
    """The full deterministic pipeline over an already-collected batch of normalized results --
    no live call anywhere in this function. If ``store`` is given, persists the run, its raw
    candidates (upgraded to ResearchRunRecord), its entities, its ranked scores, and its final
    report under research_lab/.
    """
    run.validate()
    started = time.perf_counter()

    groups = group_duplicates(results)
    entities = resolve_entities(groups)
    groups_by_id = {g.group_id: g for g in groups}
    classifications = tuple(classify_buyer(entity, groups_by_id) for entity in entities)
    classifications_by_id = {c.entity_candidate_id: c for c in classifications}
    scored = tuple(
        score_entity(entity, groups_by_id, geography_terms=geography_terms, weights=weights)
        for entity in entities
    )
    verification_queue = build_verification_queue(scored, classifications_by_id, top_n=top_n,
                                                   primary_threshold=primary_threshold)
    processing_time = time.perf_counter() - started
    metrics = compute_run_metrics(run.run_id, results, groups, classifications, processing_time=processing_time)

    if store is not None:
        if store.read_run(run.run_id) is None:
            store.create_run(run)
        records = tuple(
            r.to_research_run_record(
                run_id=run.run_id, query_set_version=run.query_set_version,
                buyer_type=next((c.category for e, c in zip(entities, classifications)
                                if r.entity_name_hint and normalize_entity_name(r.entity_name_hint) == e.normalized_name), None),
            )
            for r in results
        )
        store.append_candidates(run.run_id, records)
        store.write_entities(run.run_id, [
            {"candidate_id": e.candidate_id, "normalized_name": e.normalized_name,
             "supporting_group_ids": list(e.supporting_group_ids), "resolution_state": e.resolution_state,
             "reason": e.reason, "classification": vars(classifications_by_id[e.candidate_id])}
            for e in entities
        ])
        score_report = {
            "schema_version": SCHEMA_VERSION, "run_id": run.run_id,
            "ranked": [
                {"entity_candidate_id": item.entity_candidate_id, "score": item.score,
                 "requirement": item.requirement, "reason": item.reason}
                for item in verification_queue
            ],
        }
        store.write_score_report(run.run_id, score_report)
        store.write_report(run.run_id, vars(metrics) | {"source_diversity": dict(metrics.source_diversity)})

    return DiscoveryRunOutcome(run, groups, entities, classifications, scored, verification_queue, metrics)


_INGEST_REQUIRED_FIELDS = ("provider", "query", "url", "title", "snippet", "retrieved_at")


def ingest_external_discoveries(path: Path, *, project_id: str | None,
                                lane_id: str | None) -> tuple[NormalizedDiscoveryResult, ...]:
    """Ingest an externally-produced JSONL file (e.g. from a live research pass done outside
    this pipeline) into this module's own normalized shape.

    ``project_id``/``lane_id`` are always the caller's declared values for the whole batch --
    never read from the file -- so external input can never claim its own project/lane scope.
    Likewise, ``evidence_class``/``verification_state`` are never read from the file even if
    present: every ingested row is forced to CLAIM/unverified, exactly like any other
    NormalizedDiscoveryResult, because an external source's own confidence claim is not this
    pipeline's evidence to promote. A malformed row fails the whole batch closed -- nothing is
    partially ingested.
    """
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    results = []
    for line_number, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid_jsonl_at_line_{line_number}") from exc
        missing = [field for field in _INGEST_REQUIRED_FIELDS if field not in raw]
        if missing:
            raise ValueError(f"missing_fields_at_line_{line_number}:{','.join(missing)}")
        result = NormalizedDiscoveryResult(
            provider=str(raw["provider"]), query=str(raw["query"]), url=str(raw["url"]),
            title=str(raw["title"]), snippet=str(raw["snippet"]), retrieved_at=str(raw["retrieved_at"]),
            published_at=(str(raw["published_at"]) if raw.get("published_at") else None),
            project_id=project_id, lane_id=lane_id,
            entity_name_hint=(str(raw["entity_name_hint"]) if raw.get("entity_name_hint") else None),
            country_hint=(str(raw["country_hint"]) if raw.get("country_hint") else None),
            buyer_type_hint=(str(raw["buyer_type_hint"]) if raw.get("buyer_type_hint") else None),
            source_is_multi_entity_listing=bool(raw.get("source_is_multi_entity_listing", False)),
        )
        try:
            result.validate()
        except ValueError as exc:
            raise ValueError(f"invalid_row_at_line_{line_number}:{exc}") from exc
        results.append(result)
    return tuple(results)


RECOMMENDED_ACTIONS = frozenset({"recommend_verification", "watch", "reject"})


@dataclass(frozen=True)
class ApprovalPackItem:
    """One entity's entry in the human-approval-facing shortlist. ``requires_human_approval``
    is structurally locked True -- this is the funnel's "Human Approval" step boundary, not an
    autonomous decision, and this module never sends anything to anyone regardless of action.
    """

    entity_candidate_id: str
    normalized_name: str
    buyer_category: str
    score: float
    verification_requirement: str
    recommended_action: str
    supporting_urls: tuple[str, ...]
    reason: str
    requires_human_approval: bool = True

    def validate(self) -> None:
        if self.buyer_category not in BUYER_CATEGORIES:
            raise ValueError("invalid_buyer_category")
        if self.recommended_action not in RECOMMENDED_ACTIONS:
            raise ValueError("invalid_recommended_action")
        if not self.requires_human_approval:
            raise ValueError("approval_pack_item_must_require_human_approval")
        _unit_rate(self.score, "score")
        if not self.supporting_urls:
            raise ValueError("approval_pack_item_requires_supporting_urls")


def build_approval_pack(outcome: DiscoveryRunOutcome, *,
                        min_score_to_recommend: float = 0.6) -> tuple[ApprovalPackItem, ...]:
    """The funnel's Recommend/Watch/Reject step, over an already-computed run outcome.

    A logistics intermediary or unknown-category entity never appears here, regardless of
    score -- it was never a buyer opportunity in the first place. An entity that didn't make
    the verification queue is recommended "reject" (not enough signal to pursue); one that did
    but scored below threshold is "watch" (revisit later, don't act now); only a queued entity
    at or above threshold is "recommend_verification". Nothing here sends a message to anyone.
    """
    classifications_by_id = {c.entity_candidate_id: c for c in outcome.classifications}
    entities_by_id = {e.candidate_id: e for e in outcome.entities}
    groups_by_id = {g.group_id: g for g in outcome.groups}
    queue_by_id = {item.entity_candidate_id: item for item in outcome.verification_queue}

    items = []
    for scored in outcome.scored:
        classification = classifications_by_id.get(scored.entity_candidate_id)
        if classification is None or not classification.is_buyer_opportunity:
            continue
        entity = entities_by_id[scored.entity_candidate_id]
        urls = tuple(sorted({m.url for gid in entity.supporting_group_ids for m in groups_by_id[gid].members}))
        queued = queue_by_id.get(scored.entity_candidate_id)
        if queued is None:
            action, requirement = "reject", "secondary_source_required"
        elif scored.score >= min_score_to_recommend:
            action, requirement = "recommend_verification", queued.requirement
        else:
            action, requirement = "watch", queued.requirement
        items.append(ApprovalPackItem(
            entity_candidate_id=scored.entity_candidate_id, normalized_name=entity.normalized_name,
            buyer_category=classification.category, score=scored.score, verification_requirement=requirement,
            recommended_action=action, supporting_urls=urls,
            reason=f"resolution={entity.resolution_state}; classification_basis={classification.basis}",
        ))
    return tuple(sorted(items, key=lambda item: (-item.score, item.entity_candidate_id)))
