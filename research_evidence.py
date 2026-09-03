"""Provider-neutral search/evidence architecture (Phase E/G scaffolding).

No search provider ships live in this module. Phase G requires a benchmark
before any provider is trusted, and none has been benchmarked yet, so the
only concrete implementation here is ``NullSearchProvider`` -- it always
returns zero results. Search-provider *selection* reuses the existing,
tested fail-closed ResourceRouter/ProviderRecord pattern
(src/nexus_brain/resource_router.py) with capability="search", rather than
building an eighth independent rank/reject implementation.

When no eligible provider is available -- which is the only path possible
today -- the engine degrades gracefully and returns zero claims. It never
fabricates a search result, and it never assigns EvidenceClass.FACT to a
claim derived from a raw search result: that promotion is a deliberate,
separate human/analyst action, never something this module does itself.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Protocol

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from nexus_brain.resource_router import ProviderRecord, ResourceRouter, RoutingRequest  # noqa: E402

from contracts import EvidenceClass, canonical_digest  # noqa: E402

SCHEMA_VERSION = "nexus.research-query.v1"
SEARCH_CAPABILITY = "search"
VERIFICATION_STATES = frozenset({"unverified", "reviewed", "verified"})
BENCHMARK_DECISIONS = frozenset({"KEEP", "CONNECT", "BUILD", "DEFER", "REJECT"})


def _utc(value: str, field: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid_{field}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field}_must_include_timezone")
    return parsed.astimezone(timezone.utc).isoformat()


@dataclass(frozen=True)
class SearchResult:
    """A raw, unverified hit from a search provider. Not evidence until wrapped."""

    title: str
    url: str
    snippet: str
    published_at: str | None = None


class SearchProvider(Protocol):
    provider_id: str

    def search(self, query: str, *, max_results: int) -> tuple[SearchResult, ...]: ...


class NullSearchProvider:
    """The only provider shipped in v0.1: graceful degradation, never fabrication."""

    provider_id = "null-search-provider"

    def search(self, query: str, *, max_results: int) -> tuple[SearchResult, ...]:
        return ()


_PROVIDER_IMPLEMENTATIONS: dict[str, SearchProvider] = {NullSearchProvider.provider_id: NullSearchProvider()}


@dataclass(frozen=True)
class EvidenceClaim:
    """One factual claim with full provenance. Confidence and classification are never
    upgraded by this module -- FACT requires a deliberate downstream review, not a search hit.
    """

    claim_id: str
    statement: str
    source_name: str
    url: str
    retrieved_at: str
    evidence_class: EvidenceClass
    confidence: float
    verification_state: str
    project_id: str | None = None
    lane_id: str | None = None
    published_at: str | None = None
    supersedes: str | None = None

    def validate(self) -> None:
        if not all(isinstance(v, str) and v.strip() for v in (
            self.claim_id, self.statement, self.source_name, self.url
        )):
            raise ValueError("invalid_evidence_claim_identity")
        if not self.url.lower().startswith(("https://", "http://")):
            raise ValueError("evidence_claim_requires_retrievable_url")
        EvidenceClass(self.evidence_class)
        _utc(self.retrieved_at, "retrieved_at")
        if self.published_at is not None:
            _utc(self.published_at, "published_at")
        if self.verification_state not in VERIFICATION_STATES:
            raise ValueError("invalid_verification_state")
        if isinstance(self.confidence, bool) or not 0 <= self.confidence <= 1:
            raise ValueError("invalid_confidence")


@dataclass(frozen=True)
class ResearchQueryResult:
    schema_version: str
    query: str
    project_id: str | None
    lane_id: str | None
    provider_id: str | None
    provider_available: bool
    claims: tuple[EvidenceClaim, ...]
    routing_reason: str

    @property
    def digest(self) -> str:
        body = dict(vars(self))
        body["claims"] = tuple(vars(c) for c in self.claims)
        return canonical_digest({k: (list(v) if isinstance(v, tuple) else v) for k, v in body.items()})


def _claim_from_search_result(result: SearchResult, *, query: str, retrieved_at: str,
                              project_id: str | None, lane_id: str | None) -> EvidenceClaim:
    claim_id = "claim_" + sha256(f"{query}:{result.url}:{retrieved_at}".encode()).hexdigest()[:20]
    claim = EvidenceClaim(
        claim_id=claim_id, statement=result.snippet, source_name=result.title, url=result.url,
        retrieved_at=retrieved_at, evidence_class=EvidenceClass.CLAIM, confidence=0.3,
        verification_state="unverified", project_id=project_id, lane_id=lane_id,
        published_at=result.published_at,
    )
    claim.validate()
    return claim


def run_research_query(
    router: ResourceRouter,
    query: str,
    *,
    project_id: str | None = None,
    lane_id: str | None = None,
    sensitivity: str = "public",
    max_results: int = 5,
) -> ResearchQueryResult:
    """Route to an eligible search provider and wrap its hits as unverified claims.

    Degrades to zero claims -- never an exception, never a fabricated result -- when no
    provider is eligible. ``router`` is the existing, tested ``ResourceRouter``; this
    function does not implement its own selection logic.
    """
    if not query.strip():
        raise ValueError("invalid_research_query")
    if max_results < 1:
        raise ValueError("invalid_max_results")

    decision = router.route(RoutingRequest(capability=SEARCH_CAPABILITY, sensitivity=sensitivity))
    if not decision.allowed or decision.provider_id not in _PROVIDER_IMPLEMENTATIONS:
        return ResearchQueryResult(SCHEMA_VERSION, query, project_id, lane_id, None, False, (), decision.reason)

    provider = _PROVIDER_IMPLEMENTATIONS[decision.provider_id]
    retrieved_at = datetime.now(timezone.utc).isoformat()
    claims = tuple(
        _claim_from_search_result(result, query=query, retrieved_at=retrieved_at,
                                  project_id=project_id, lane_id=lane_id)
        for result in provider.search(query, max_results=max_results)
    )
    return ResearchQueryResult(SCHEMA_VERSION, query, project_id, lane_id, provider.provider_id, True,
                               claims, decision.reason)


@dataclass(frozen=True)
class SearchProviderBenchmark:
    """Phase G/H acceptance record. A provider earns KEEP/CONNECT only by measured evidence,
    never by being merely available -- see ``validate``'s hallucination-rate guard below.
    """

    provider_id: str
    coverage: float
    freshness: float
    citation_accuracy: float
    source_quality: float
    latency_ms: float
    cost_usd_per_query: float
    duplicate_rate: float
    hallucination_rate: float
    decision: str
    evaluated_at: str
    sample_size: int
    notes: str = ""

    def validate(self) -> None:
        if not self.provider_id.strip():
            raise ValueError("invalid_provider_id")
        for value in (self.coverage, self.freshness, self.citation_accuracy, self.source_quality,
                     self.duplicate_rate, self.hallucination_rate):
            if isinstance(value, bool) or not 0 <= value <= 1:
                raise ValueError("invalid_benchmark_rate")
        if self.latency_ms < 0 or self.cost_usd_per_query < 0:
            raise ValueError("invalid_benchmark_cost_or_latency")
        if self.decision not in BENCHMARK_DECISIONS:
            raise ValueError("invalid_benchmark_decision")
        if isinstance(self.sample_size, bool) or not isinstance(self.sample_size, int) or self.sample_size < 1:
            raise ValueError("invalid_benchmark_sample_size")
        _utc(self.evaluated_at, "evaluated_at")
        if self.decision in {"KEEP", "CONNECT"} and self.hallucination_rate > 0.05:
            raise ValueError("decision_inconsistent_with_hallucination_rate")


def search_provider_record(provider_id: str, *, production_approved: bool = False,
                           policy_verified: bool = False, max_sensitivity: str = "public") -> ProviderRecord:
    """Build the ProviderRecord a benchmarked search provider needs to become eligible
    via the existing ResourceRouter -- no new registry format, reuses provider_registry.py's shape.
    """
    return ProviderRecord(
        id=provider_id, status="experimental", authority="OFFICIAL_DOCS_VERIFIED" if policy_verified else "DISCOVERY_ONLY",
        capabilities=(SEARCH_CAPABILITY,), openai_compatible=False, sensitive_data_allowed=False,
        production_role="search_provider", free_limit="unknown", data_training="unknown",
        max_sensitivity=max_sensitivity, production_approved=production_approved,
        policy_verified=policy_verified,
    )
