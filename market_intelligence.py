"""Generic, project-neutral market-intelligence infrastructure:

  * an extended entity-role taxonomy that never lets a logistics intermediary, market-price
    row, government tendering notice, or unknown-signal entity become a "buyer" merely by
    appearing often;
  * an evidence-adaptive geography/market-tier reranking mechanism -- an initial tier list is
    a *prior*, never a permanent decision, and real measured evidence can promote or demote
    any market;
  * a market-aware search-budget allocator that reuses deep_search_fabric.py's own
    ProviderPerformanceTracker/allocate_budget mechanism (same shape, same guarantees) rather
    than building a second one;
  * a lane-direction binding that keeps "home market role" and "foreign market role"
    structurally distinct, so an export lane's home-market PRODUCER role can never collapse
    into an import lane's home-market BUYER role by accident.

This module carries NO business facts. Every market_id, tier, lane, and role-keyword lexicon
used by tests is a placeholder the caller supplies -- it does not know about any specific
project, country, or company, and ships with no real-world lexicon of its own.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from deep_search_fabric import ProviderPerformanceTracker, allocate_budget  # noqa: E402

ENTITY_ROLES = frozenset({
    "BUYER", "END_USER", "PRODUCER", "SUPPLIER", "DISTRIBUTOR", "TRADER", "IMPORTER", "EXPORTER",
    "LOGISTICS_INTERMEDIARY", "AGENT_INTERMEDIARY", "GOVERNMENT_TENDERING_BODY",
    "MARKET_PRICE_SOURCE", "UNKNOWN",
})

# Roles that must never be silently treated as a buyer/customer opportunity, no matter how
# many supporting records exist -- mirrors discovery_pipeline.py's is_buyer_opportunity
# discipline, extended to this fuller taxonomy. A government tendering body issues demand
# signals but is not itself the buyer; a market-price row is evidence, not a counterparty.
_BUYER_LIKE_ROLES = frozenset({"BUYER", "END_USER", "DISTRIBUTOR", "TRADER", "IMPORTER"})

LANE_DIRECTIONS = frozenset({"EXPORT", "IMPORT"})


def is_buyer_role(role: str) -> bool:
    if role not in ENTITY_ROLES:
        raise ValueError("invalid_entity_role")
    return role in _BUYER_LIKE_ROLES


# ---------------------------------------------------------------------------
# Deterministic, ordered, keyword-based role classification (language-agnostic)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RoleKeywordRule:
    role: str
    keywords: tuple[str, ...]

    def validate(self) -> None:
        if self.role not in ENTITY_ROLES:
            raise ValueError("invalid_entity_role")
        if not self.keywords:
            raise ValueError("role_rule_requires_keywords")
        if any(not isinstance(k, str) or not k.strip() for k in self.keywords):
            raise ValueError("invalid_role_rule_keyword")


def classify_entity_role(text: str, rules: Sequence[RoleKeywordRule]) -> tuple[str, str]:
    """Deterministic, ordered, keyword-based classification -- never influenced by how many
    records support a candidate, only by the text itself, and never English-only: callers
    supply whatever keywords (Persian, transliterated, or Latin) their own lexicon defines.
    Rule order is the caller's priority order (e.g. logistics keywords checked before buyer
    keywords) -- this function does not reorder or score rules itself.
    Returns (role, matched_keyword); ("UNKNOWN", "") when nothing matches.
    """
    lowered = text.lower()
    for rule in rules:
        rule.validate()
        for keyword in rule.keywords:
            if keyword.lower() in lowered:
                return rule.role, keyword
    return "UNKNOWN", ""


# ---------------------------------------------------------------------------
# Evidence-adaptive geography/market-tier reranking
# ---------------------------------------------------------------------------

def _unit_rate(value, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
        raise ValueError(f"invalid_{field}")


@dataclass(frozen=True)
class MarketTier:
    market_id: str
    tier: int
    rationale: str

    def validate(self) -> None:
        if not self.market_id.strip():
            raise ValueError("invalid_market_id")
        if isinstance(self.tier, bool) or not isinstance(self.tier, int) or self.tier < 0:
            raise ValueError("invalid_tier")


@dataclass(frozen=True)
class MarketEvidence:
    """Every field is a measured [0,1] signal the caller supplies -- this dataclass computes
    a composite score from them, it does not itself measure anything or know any market."""

    market_id: str
    demand_signal: float = 0.0
    procurement_signal: float = 0.0
    trade_flow_signal: float = 0.0
    logistics_feasibility: float = 0.5
    compliance_feasibility: float = 0.5
    accessibility: float = 0.5
    source_coverage: float = 0.5
    freshness: float = 0.5
    contactability: float = 0.5
    expected_value: float = 0.5

    _WEIGHTS = {
        "demand_signal": 0.2, "procurement_signal": 0.15, "trade_flow_signal": 0.15,
        "logistics_feasibility": 0.1, "compliance_feasibility": 0.1, "accessibility": 0.1,
        "source_coverage": 0.05, "freshness": 0.05, "contactability": 0.05, "expected_value": 0.05,
    }

    def validate(self) -> None:
        if not self.market_id.strip():
            raise ValueError("invalid_market_id")
        for field_name in self._WEIGHTS:
            _unit_rate(getattr(self, field_name), field_name)

    @property
    def composite_score(self) -> float:
        self.validate()
        return sum(weight * getattr(self, field_name) for field_name, weight in self._WEIGHTS.items())


@dataclass(frozen=True)
class MarketPriorityPlan:
    tiers: tuple[MarketTier, ...]

    def validate(self) -> None:
        ids = [t.market_id for t in self.tiers]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate_market_id")
        for t in self.tiers:
            t.validate()

    def ranked_market_ids(self) -> tuple[str, ...]:
        self.validate()
        return tuple(t.market_id for t in sorted(self.tiers, key=lambda t: (t.tier, t.market_id)))


def rerank_markets_by_evidence(plan: MarketPriorityPlan, evidence: Mapping[str, MarketEvidence],
                              *, evidence_weight: float = 0.5) -> tuple[str, ...]:
    """Blends the prior tier ranking with measured evidence. Initial tiers are priors, not
    permanent decisions -- a market can be promoted or demoted as evidence changes. A market
    with no evidence yet keeps a neutral 0.5 evidence contribution (never 0.0), so absence of
    data never looks like proven low priority.
    """
    plan.validate()
    _unit_rate(evidence_weight, "evidence_weight")
    tiers = plan.tiers
    max_tier = max((t.tier for t in tiers), default=0) or 1
    scored = []
    for t in tiers:
        prior_score = 1 - (t.tier / max(max_tier, 1))
        market_evidence = evidence.get(t.market_id)
        evidence_score = market_evidence.composite_score if market_evidence is not None else 0.5
        blended = (1 - evidence_weight) * prior_score + evidence_weight * evidence_score
        scored.append((blended, t.market_id))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return tuple(market_id for _, market_id in scored)


# ---------------------------------------------------------------------------
# Market-aware search-budget allocation (reuses deep_search_fabric's mechanism)
# ---------------------------------------------------------------------------

def allocate_market_budget(tracker: ProviderPerformanceTracker, plan: MarketPriorityPlan,
                          evidence: Mapping[str, MarketEvidence], total_budget: int,
                          *, min_floor: int = 1, evidence_weight: float = 0.5) -> dict[str, int]:
    """Once any market has measured yield in ``tracker``, this delegates entirely to
    deep_search_fabric.allocate_budget() (same sum<=budget guarantee, same deterministic
    tie-break) using the evidence-reranked market order as its id list. Before any real yield
    exists, it seeds a deterministic rank-weighted allocation from the tier+evidence prior
    instead of an uninformative even split, so a Tier 0 market starts with more exploration
    budget than a Tier 4 one -- without ever exceeding total_budget.
    """
    ranked = rerank_markets_by_evidence(plan, evidence, evidence_weight=evidence_weight)
    if any(tracker.marginal_yield(m) > 0 for m in ranked):
        return allocate_budget(tracker, ranked, total_budget, min_floor=min_floor)

    n = len(ranked)
    if n == 0 or total_budget <= 0:
        return {m: 0 for m in ranked}
    if total_budget < n * min_floor:
        return allocate_budget(tracker, ranked, total_budget, min_floor=min_floor)

    weights = [n - i for i in range(n)]
    total_weight = sum(weights)
    allocation = {m: min_floor for m in ranked}
    remaining = total_budget - n * min_floor
    if remaining > 0:
        shares = [remaining * (w / total_weight) for w in weights]
        base = [int(s) for s in shares]
        leftover = remaining - sum(base)
        for i in range(leftover):
            base[i % n] += 1
        for market_id, extra in zip(ranked, base):
            allocation[market_id] += extra
    return allocation


# ---------------------------------------------------------------------------
# Lane-direction role binding -- keeps home/foreign roles structurally distinct
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LaneDiscoveryBinding:
    """Encodes "for an export lane, the home market is the producer/supply layer and foreign
    markets are the buyer-discovery layer; for an import lane, it's reversed" as a structural
    invariant rather than a convention someone has to remember. Never confuses the two: raising
    if home_market_role == foreign_market_role catches exactly that class of mistake.
    """

    lane_id: str
    direction: str
    home_market_id: str
    home_market_role: str
    foreign_market_role: str

    def validate(self) -> None:
        if not self.lane_id.strip():
            raise ValueError("invalid_lane_id")
        if self.direction not in LANE_DIRECTIONS:
            raise ValueError("invalid_lane_direction")
        if not self.home_market_id.strip():
            raise ValueError("invalid_home_market_id")
        if self.home_market_role not in ENTITY_ROLES or self.foreign_market_role not in ENTITY_ROLES:
            raise ValueError("invalid_lane_role")
        if self.home_market_role == self.foreign_market_role:
            raise ValueError("home_and_foreign_roles_must_differ")
