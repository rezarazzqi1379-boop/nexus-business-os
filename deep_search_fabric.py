"""Deep Search Fabric v2: a recursive, provider-neutral, evidence-driven search
core built on top of discovery_pipeline.py's single-pass dedup/entity-
resolution/classification machinery. Optimizes for verified unique commercial
entities and actionable evidence, not URL count.

No live provider ships here. The recursive loop is driven by a caller-supplied
``provider_fn`` -- in this v0.1, tests supply a deterministic synthetic
function; a real adapter would be benchmarked and injected the same way
research_evidence.py/discovery_pipeline.py already require. No new
database -- every structure here is an in-memory, JSON-serializable dataclass.

Ten components, per the spec:
  1. QueryLattice / build_query_lattice        6. EvidenceGraph / EvidenceLink
  2. SearchFrontier                            7. expand_entity_relationships
  3. generate_expansion_queries                8. detect_coverage_gaps (negative-evidence plan)
  4. detect_coverage_gaps                      9. classify_temporal_state
  5. ProviderPerformanceTracker                10. allocate_budget

Anti-spin: a coverage gap tracks the distinct (query_family, provider) pairs
already attempted against it. Two attempts in the *same* family/provider that
add no new evidence forces the next attempt to change family or provider;
three distinct attempts that all add nothing marks the gap BLOCKED_UNKNOWN --
never quietly retried forever.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Callable, Mapping, Sequence

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from contracts import EvidenceClass  # noqa: E402
from discovery_pipeline import (  # noqa: E402
    BuyerClassification,
    DuplicateGroup,
    EntityResolutionCandidate,
    NormalizedDiscoveryResult,
    QueryExpansionPlan,
    _HIGH_QUALITY_URL_SIGNALS,
    _text_of,
    classify_buyer,
    group_duplicates,
    normalize_entity_name,
    resolve_entities,
)

SCHEMA_VERSION = "nexus.deep-search-fabric.v2"

FRONTIER_STATES = frozenset({"NEW", "QUEUED", "SEARCHED", "EXPAND", "VERIFY", "EXHAUSTED", "REJECTED"})
TEMPORAL_STATES = frozenset({"current", "recent", "stale", "expired_historical"})
STOP_REASONS = frozenset({
    "marginal_yield_below_threshold", "coverage_target_reached", "verification_target_reached",
    "budget_exhausted", "no_new_evidence_from_repeated_queries", "max_depth_reached",
})
GAP_STATES = frozenset({"OPEN", "BLOCKED_UNKNOWN"})
_MAX_ATTEMPTS_BEFORE_BLOCKED = 3

_RELATIONSHIP_KEYWORDS = (
    ("subsidiary_of", (" a subsidiary of ", " subsidiary of ", " part of ")),
    ("alias_of", (" formerly known as ", " trading as ", " f/k/a ", " a.k.a ", " also known as ")),
)


def make_query_id(query_text: str, parent_query_id: str | None, search_depth: int) -> str:
    return "q_" + sha256(f"{parent_query_id}:{search_depth}:{query_text}".encode()).hexdigest()[:16]


def query_family(query_text: str) -> str:
    """A coarse identity for a query, ignoring the language tag -- used for anti-spin tracking."""
    return re.sub(r"\[[a-zA-Z-]+\]", "", query_text).strip().lower()


# ---------------------------------------------------------------------------
# 1. QueryLattice
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class QueryNode:
    query_id: str
    query_text: str
    parent_query_id: str | None
    search_depth: int
    origin: str  # "initial" | "gap_expansion" | "relationship_expansion"
    provider_hint: str | None = None


@dataclass(frozen=True)
class QueryLattice:
    plan: QueryExpansionPlan
    root_nodes: tuple[QueryNode, ...]


def build_query_lattice(plan: QueryExpansionPlan, *, max_queries: int = 500) -> QueryLattice:
    plan.validate()
    texts = plan.expand(max_queries=max_queries)
    nodes = tuple(
        QueryNode(query_id=make_query_id(text, None, 0), query_text=text, parent_query_id=None,
                 search_depth=0, origin="initial")
        for text in texts
    )
    return QueryLattice(plan, nodes)


# ---------------------------------------------------------------------------
# 2. SearchFrontier
# ---------------------------------------------------------------------------

class SearchFrontier:
    """Idempotent query-node tracker: adding the same query_id twice is a no-op, so a query
    already queued/searched/exhausted is never duplicated or re-executed by accident.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, QueryNode] = {}
        self._states: dict[str, str] = {}

    def add(self, node: QueryNode) -> bool:
        if node.query_id in self._nodes:
            return False
        self._nodes[node.query_id] = node
        self._states[node.query_id] = "NEW"
        return True

    def set_state(self, query_id: str, state: str) -> None:
        if state not in FRONTIER_STATES:
            raise ValueError("invalid_frontier_state")
        if query_id not in self._nodes:
            raise KeyError("unknown_query_id")
        self._states[query_id] = state

    def state(self, query_id: str) -> str:
        return self._states[query_id]

    def node(self, query_id: str) -> QueryNode:
        return self._nodes[query_id]

    def nodes_in_state(self, state: str) -> tuple[QueryNode, ...]:
        return tuple(self._nodes[qid] for qid in self._nodes if self._states[qid] == state)

    def all_nodes(self) -> tuple[QueryNode, ...]:
        return tuple(self._nodes.values())

    def __len__(self) -> int:
        return len(self._nodes)


# ---------------------------------------------------------------------------
# 5. ProviderPerformanceTracker  /  10. SearchBudgetAllocator
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProviderRoundStat:
    provider_id: str
    round_index: int
    new_unique_entities: int
    total_results: int


class ProviderPerformanceTracker:
    def __init__(self) -> None:
        self._stats: list[ProviderRoundStat] = []

    def record(self, provider_id: str, round_index: int, new_unique_entities: int, total_results: int) -> None:
        self._stats.append(ProviderRoundStat(provider_id, round_index, new_unique_entities, total_results))

    def marginal_yield(self, provider_id: str) -> float:
        rows = [s for s in self._stats if s.provider_id == provider_id]
        if not rows:
            return 0.0
        latest = rows[-1]
        return (latest.new_unique_entities / latest.total_results) if latest.total_results else 0.0

    def all_provider_ids(self) -> tuple[str, ...]:
        return tuple(sorted({s.provider_id for s in self._stats}))

    def history(self) -> tuple[ProviderRoundStat, ...]:
        return tuple(self._stats)


def allocate_budget(tracker: ProviderPerformanceTracker, provider_ids: Sequence[str], total_budget: int,
                    *, min_floor: int = 1) -> dict[str, int]:
    """Deterministic allocation: every provider gets at least ``min_floor``, remaining budget
    split proportionally to observed marginal yield (even split if nothing observed yet).
    Ties always break by sorted provider_id -- never by insertion order or randomness.
    """
    if not provider_ids or total_budget <= 0:
        return {pid: 0 for pid in provider_ids}
    sorted_ids = sorted(set(provider_ids))
    allocation = {pid: min(min_floor, total_budget) for pid in sorted_ids}
    remaining = total_budget - sum(allocation.values())
    if remaining <= 0:
        return allocation
    yields = {pid: tracker.marginal_yield(pid) for pid in sorted_ids}
    total_yield = sum(yields.values())
    if total_yield > 0:
        for pid in sorted_ids:
            allocation[pid] += int(remaining * (yields[pid] / total_yield))
    else:
        base = remaining // len(sorted_ids)
        for pid in sorted_ids:
            allocation[pid] += base
    return allocation


# ---------------------------------------------------------------------------
# 9. TemporalState classifier
# ---------------------------------------------------------------------------

def classify_temporal_state(retrieved_at: str, publication_date: str | None) -> str:
    """Expired evidence is never discarded -- it's labeled, not dropped, per the rule that
    an expired tender remains valid buyer-history evidence."""
    if publication_date is None:
        return "current"
    age_days = (datetime.fromisoformat(retrieved_at) - datetime.fromisoformat(publication_date)).days
    if age_days <= 30:
        return "current"
    if age_days <= 180:
        return "recent"
    if age_days <= 730:
        return "stale"
    return "expired_historical"


def _source_quality(url: str) -> float:
    hits = sum(1 for signal in _HIGH_QUALITY_URL_SIGNALS if signal in url.lower())
    return min(0.4 + 0.2 * hits, 1.0) if hits else 0.3


# ---------------------------------------------------------------------------
# 6/7. EvidenceGraph, EvidenceLink, EntityRelationshipExpander
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvidenceLink:
    from_candidate_id: str
    to_name_hint: str
    relationship_type: str
    evidence_url: str


@dataclass(frozen=True)
class EvidenceGraph:
    links: tuple[EvidenceLink, ...] = ()

    def links_from(self, candidate_id: str) -> tuple[EvidenceLink, ...]:
        return tuple(l for l in self.links if l.from_candidate_id == candidate_id)

    def merge(self, more: Sequence[EvidenceLink]) -> "EvidenceGraph":
        return EvidenceGraph(tuple(dict.fromkeys((*self.links, *more))))


def expand_entity_relationships(candidate: EntityResolutionCandidate,
                                groups_by_id: Mapping[str, DuplicateGroup]) -> tuple[EvidenceLink, ...]:
    """Deterministic keyword-based relationship detection over text already present -- never a
    fabricated corporate-structure fact. "subsidiary_of"/"alias_of" hints become follow-up
    query candidates for RecursiveQueryGenerator, not asserted facts.
    """
    links: list[EvidenceLink] = []
    for group_id in candidate.supporting_group_ids:
        for member in groups_by_id[group_id].members:
            text = _text_of(member)
            for relationship_type, keywords in _RELATIONSHIP_KEYWORDS:
                for keyword in keywords:
                    index = text.find(keyword)
                    if index == -1:
                        continue
                    tail = text[index + len(keyword):index + len(keyword) + 60].strip()
                    target_hint = re.split(r"[.,;]", tail)[0].strip()
                    if target_hint:
                        links.append(EvidenceLink(candidate.candidate_id, target_hint, relationship_type, member.url))
    return tuple(dict.fromkeys(links))


# ---------------------------------------------------------------------------
# 4/8. CoverageGapDetector / NegativeEvidenceSearchPlan
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CoverageGap:
    gap_id: str
    dimension: str
    reason: str
    attempted: tuple[tuple[str, str], ...] = ()  # (query_family, provider) pairs already tried
    state: str = "OPEN"

    def validate(self) -> None:
        if self.state not in GAP_STATES:
            raise ValueError("invalid_gap_state")

    def record_failed_attempt(self, family: str, provider: str) -> "CoverageGap":
        attempted = (*self.attempted, (family, provider))
        distinct = len({pair for pair in attempted})
        state = "BLOCKED_UNKNOWN" if distinct >= _MAX_ATTEMPTS_BEFORE_BLOCKED else self.state
        return CoverageGap(self.gap_id, self.dimension, self.reason, attempted, state)


def detect_coverage_gaps(plan: QueryExpansionPlan, groups: Sequence[DuplicateGroup]) -> tuple[CoverageGap, ...]:
    """A negative-evidence plan: every plan dimension (geography term) with zero matching
    discoveries becomes an explicit, trackable gap -- never silently ignored.
    """
    covered = set()
    for group in groups:
        for member in group.members:
            if member.country_hint:
                covered.add(normalize_entity_name(member.country_hint))
    gaps = []
    for geography in plan.geography_terms:
        if normalize_entity_name(geography) not in covered:
            gaps.append(CoverageGap(
                gap_id="gap_" + sha256(f"geography:{geography}".encode()).hexdigest()[:12],
                dimension=f"geography:{geography}", reason="no discovery matched this geography term",
            ))
    return tuple(gaps)


# ---------------------------------------------------------------------------
# 3. RecursiveQueryGenerator
# ---------------------------------------------------------------------------

def generate_expansion_queries(entities: Sequence[EntityResolutionCandidate],
                               groups_by_id: Mapping[str, DuplicateGroup], gaps: Sequence[CoverageGap],
                               links: Sequence[EvidenceLink], *, search_depth: int,
                               parent_query_id: str | None) -> tuple[QueryNode, ...]:
    """Two sources of next-round queries: (a) a targeted confirmation query for every
    "probable" (single-source) entity, to try to reach "exact"; (b) a follow-up query for
    every relationship-expansion hint (subsidiary/alias name) discovered this round.
    """
    seen_texts: set[str] = set()
    nodes: list[QueryNode] = []

    for candidate in entities:
        if candidate.resolution_state != "probable" or not candidate.normalized_name:
            continue
        text = f"{candidate.normalized_name} confirm"
        if text in seen_texts:
            continue
        seen_texts.add(text)
        nodes.append(QueryNode(make_query_id(text, parent_query_id, search_depth), text, parent_query_id,
                               search_depth, "gap_expansion"))

    for link in links:
        text = link.to_name_hint.strip()
        if not text or text in seen_texts:
            continue
        seen_texts.add(text)
        nodes.append(QueryNode(make_query_id(text, parent_query_id, search_depth), text, parent_query_id,
                               search_depth, "relationship_expansion"))

    for gap in gaps:
        if gap.state == "BLOCKED_UNKNOWN":
            continue
        text = f"{gap.dimension} alternate search"
        if text in seen_texts:
            continue
        seen_texts.add(text)
        nodes.append(QueryNode(make_query_id(text, parent_query_id, search_depth), text, parent_query_id,
                               search_depth, "gap_expansion"))

    return tuple(nodes)


# ---------------------------------------------------------------------------
# Stop conditions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StopDecision:
    should_stop: bool
    reason: str | None

    def validate(self) -> None:
        if self.reason is not None and self.reason not in STOP_REASONS:
            raise ValueError("invalid_stop_reason")


def evaluate_stop_conditions(*, round_index: int, new_unique_entities_this_round: int,
                            total_unique_entities: int, coverage_ratio: float, coverage_target: float,
                            verified_ratio: float, verification_target: float, queries_executed: int,
                            query_budget: int, marginal_yield_threshold: float = 0.02) -> StopDecision:
    if queries_executed >= query_budget:
        return StopDecision(True, "budget_exhausted")
    if coverage_ratio >= coverage_target:
        return StopDecision(True, "coverage_target_reached")
    if verified_ratio >= verification_target:
        return StopDecision(True, "verification_target_reached")
    if round_index > 0 and new_unique_entities_this_round == 0:
        return StopDecision(True, "no_new_evidence_from_repeated_queries")
    if round_index > 0 and total_unique_entities > 0:
        if (new_unique_entities_this_round / total_unique_entities) < marginal_yield_threshold:
            return StopDecision(True, "marginal_yield_below_threshold")
    return StopDecision(False, None)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RoundOutcome:
    round_index: int
    executed_query_ids: tuple[str, ...]
    new_result_count: int
    groups: tuple[DuplicateGroup, ...]
    entities: tuple[EntityResolutionCandidate, ...]
    new_entity_ids: tuple[str, ...]
    stop: StopDecision


@dataclass(frozen=True)
class RecursiveSearchOutcome:
    run_id: str
    rounds: tuple[RoundOutcome, ...]
    all_results: tuple[NormalizedDiscoveryResult, ...]
    entities_by_id: Mapping[str, EntityResolutionCandidate]
    classifications_by_id: Mapping[str, BuyerClassification]
    evidence_graph: EvidenceGraph
    coverage_gaps: tuple[CoverageGap, ...]
    frontier: SearchFrontier
    tracker: ProviderPerformanceTracker
    stop_reason: str

    @property
    def qualified_buyer_ids(self) -> tuple[str, ...]:
        return tuple(sorted(
            cid for cid, c in self.classifications_by_id.items() if c.is_buyer_opportunity
        ))


def run_recursive_search(plan: QueryExpansionPlan, provider_fn: Callable[[str, int], tuple[NormalizedDiscoveryResult, ...]],
                        *, run_id: str, max_depth: int = 3, query_budget: int = 1000, results_per_query: int = 10,
                        coverage_target: float = 0.8, verification_target: float = 0.3,
                        marginal_yield_threshold: float = 0.02) -> RecursiveSearchOutcome:
    """The full loop: OBJECTIVE -> lattice -> discovery -> normalize (assumed done by
    ``provider_fn``, which must already return validated NormalizedDiscoveryResult) -> dedup ->
    entity resolution -> evidence graph -> coverage gaps -> new queries -> next round -> ...
    -> a measurable stop condition. Every ``provider_fn`` call is deterministic given the
    same query text and depth; nothing here performs a live call itself.
    """
    lattice = build_query_lattice(plan, max_queries=query_budget)
    frontier = SearchFrontier()
    for node in lattice.root_nodes:
        frontier.add(node)

    tracker = ProviderPerformanceTracker()
    all_results: list[NormalizedDiscoveryResult] = []
    entities_by_id: dict[str, EntityResolutionCandidate] = {}
    evidence_graph = EvidenceGraph()
    gaps_by_id: dict[str, CoverageGap] = {}
    rounds: list[RoundOutcome] = []
    queries_executed = 0
    round_index = 0
    stop = StopDecision(False, None)

    while True:
        pending = frontier.nodes_in_state("NEW")
        if not pending:
            stop = StopDecision(True, "no_new_evidence_from_repeated_queries")
            rounds.append(RoundOutcome(round_index, (), 0, group_duplicates(tuple(all_results)) if all_results else (),
                                       tuple(entities_by_id.values()), (), stop))
            break

        executed_ids: list[str] = []
        round_results: list[NormalizedDiscoveryResult] = []
        for node in pending:
            if queries_executed >= query_budget:
                break
            frontier.set_state(node.query_id, "QUEUED")
            hits = provider_fn(node.query_text, results_per_query)
            for hit in hits:
                hit.validate()
            round_results.extend(hits)
            frontier.set_state(node.query_id, "SEARCHED")
            executed_ids.append(node.query_id)
            queries_executed += 1

        all_results.extend(round_results)
        groups = group_duplicates(tuple(all_results)) if all_results else ()
        groups_by_id = {g.group_id: g for g in groups}
        entities = resolve_entities(groups)
        classifications = tuple(classify_buyer(e, groups_by_id) for e in entities)
        classifications_by_id = {c.entity_candidate_id: c for c in classifications}

        new_entity_ids = tuple(sorted(e.candidate_id for e in entities if e.candidate_id not in entities_by_id))
        for entity in entities:
            entities_by_id[entity.candidate_id] = entity

        provider_result_counts: dict[str, int] = {}
        for result in round_results:
            provider_result_counts[result.provider] = provider_result_counts.get(result.provider, 0) + 1
        new_entity_set = set(new_entity_ids)
        for provider_id, total in provider_result_counts.items():
            contributed = sum(
                1 for entity_id in new_entity_set
                for group_id in entities_by_id[entity_id].supporting_group_ids
                if any(m.provider == provider_id for m in groups_by_id[group_id].members)
            )
            tracker.record(provider_id, round_index, contributed, total)

        gaps = detect_coverage_gaps(plan, groups)
        for gap in gaps:
            gaps_by_id.setdefault(gap.gap_id, gap)
        for query_node_id in executed_ids:
            family = query_family(frontier.node(query_node_id).query_text)
            for gap_id, gap in list(gaps_by_id.items()):
                if gap.dimension.split(":", 1)[-1].strip().lower() in family:
                    gaps_by_id[gap_id] = gap.record_failed_attempt(family, "synthetic")

        links: list[EvidenceLink] = []
        for entity in entities:
            links.extend(expand_entity_relationships(entity, groups_by_id))
        evidence_graph = evidence_graph.merge(tuple(links))

        coverage_ratio = 1 - (len([g for g in gaps_by_id.values() if g.state == "OPEN"]) /
                              max(len(plan.geography_terms), 1))
        verified_ratio = (sum(1 for e in entities if e.resolution_state == "exact") / len(entities)) if entities else 0.0

        stop = evaluate_stop_conditions(
            round_index=round_index, new_unique_entities_this_round=len(new_entity_ids),
            total_unique_entities=len(entities), coverage_ratio=coverage_ratio, coverage_target=coverage_target,
            verified_ratio=verified_ratio, verification_target=verification_target,
            queries_executed=queries_executed, query_budget=query_budget,
            marginal_yield_threshold=marginal_yield_threshold,
        )
        rounds.append(RoundOutcome(round_index, tuple(executed_ids), len(round_results), groups, entities,
                                   new_entity_ids, stop))

        if stop.should_stop or round_index + 1 >= max_depth:
            if not stop.should_stop:
                stop = StopDecision(True, "max_depth_reached")
            break

        next_nodes = generate_expansion_queries(
            entities, groups_by_id, tuple(gaps_by_id.values()), links,
            search_depth=round_index + 1, parent_query_id=executed_ids[0] if executed_ids else None,
        )
        added_any = False
        for node in next_nodes:
            if frontier.add(node):
                added_any = True
        if not added_any:
            stop = StopDecision(True, "no_new_evidence_from_repeated_queries")
            break
        round_index += 1

    final_groups = group_duplicates(tuple(all_results)) if all_results else ()
    final_groups_by_id = {g.group_id: g for g in final_groups}
    final_entities = resolve_entities(final_groups)
    final_classifications = {c.entity_candidate_id: c for c in
                             (classify_buyer(e, final_groups_by_id) for e in final_entities)}

    return RecursiveSearchOutcome(
        run_id=run_id, rounds=tuple(rounds), all_results=tuple(all_results),
        entities_by_id={e.candidate_id: e for e in final_entities}, classifications_by_id=final_classifications,
        evidence_graph=evidence_graph, coverage_gaps=tuple(gaps_by_id.values()), frontier=frontier, tracker=tracker,
        stop_reason=stop.reason or "no_new_evidence_from_repeated_queries",
    )
