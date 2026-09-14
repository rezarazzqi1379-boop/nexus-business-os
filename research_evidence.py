"""Provider-neutral search/evidence architecture (Phase E/G scaffolding).

No search provider ships live in this module. Phase G requires a benchmark
before any provider is trusted, and none has been benchmarked yet, so the
only concrete implementation here is ``NullSearchProvider`` -- it always
returns zero results. Search-provider *selection* reuses the existing,
tested fail-closed ResourceRouter/ProviderRecord pattern
(src/nexus_brain/resource_router.py) with capability="search", rather than
building an eighth independent rank/reject implementation.

When no eligible provider is available -- the only path possible today
with the default registry -- the engine degrades gracefully and returns
zero claims. It never fabricates a search result, and it never assigns
EvidenceClass.FACT to a claim derived from a raw search result: that
promotion is a deliberate, separate human/analyst action, never something
this module does itself.

Lane-neutral evidence transport: this module carries ``project_id`` and
``lane_id`` on every claim/result exactly as given, and does not interpret,
normalize, or validate them. In particular it has no knowledge of PRJ-FAL-01
or its FAL-A/FAL-B lane-isolation rules -- that authority (which grades,
prices, counterparties, etc. may never cross which lane) belongs to a
separate project-binding policy layer that does not exist yet and must not
be invented here ahead of the real canonical authority sync.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Mapping, Protocol

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from nexus_brain.resource_router import ProviderRecord, ResourceRouter, RoutingRequest  # noqa: E402

from contracts import EvidenceClass, canonical_digest  # noqa: E402

SCHEMA_VERSION = "nexus.research-query.v1"
SEARCH_CAPABILITY = "search"
VERIFICATION_STATES = frozenset({"unverified", "reviewed", "verified"})
BENCHMARK_DECISIONS = frozenset({"KEEP", "CONNECT", "BUILD", "DEFER", "REJECT"})
_ACCEPTANCE_DECISIONS = frozenset({"KEEP", "CONNECT"})


def _utc(value: str, field: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid_{field}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field}_must_include_timezone")
    return parsed.astimezone(timezone.utc).isoformat()


def _unit_rate(value, field: str) -> None:
    """A 0..1 rate that fails with ValueError, never TypeError, on a non-numeric input."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
        raise ValueError(f"invalid_{field}")


@dataclass(frozen=True)
class SearchResult:
    """A raw, unverified hit from a search provider. Not evidence until wrapped and validated."""

    title: str
    url: str
    snippet: str
    published_at: str | None = None

    def validate(self) -> None:
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("invalid_search_result_title")
        if not isinstance(self.snippet, str) or not self.snippet.strip():
            raise ValueError("invalid_search_result_snippet")
        if not isinstance(self.url, str) or not self.url.lower().startswith(("https://", "http://")):
            raise ValueError("invalid_search_result_url")
        if self.published_at is not None:
            _utc(self.published_at, "search_result_published_at")


class SearchProvider(Protocol):
    provider_id: str

    def search(self, query: str, *, max_results: int) -> tuple[SearchResult, ...]: ...


class NullSearchProvider:
    """The only provider shipped in v0.1: graceful degradation, never fabrication."""

    provider_id = "null-search-provider"

    def search(self, query: str, *, max_results: int) -> tuple[SearchResult, ...]:
        return ()


def default_search_providers() -> dict[str, SearchProvider]:
    """A fresh registry containing only the graceful-degradation default.

    Returns a new dict on every call -- there is no shared module-level mutable
    registry to accidentally mutate. Callers that add a real provider pass their
    own registry to ``run_research_query`` via ``providers=`` instead of editing
    this module.
    """
    return {NullSearchProvider.provider_id: NullSearchProvider()}


@dataclass(frozen=True)
class EvidenceClaim:
    """One factual claim with full provenance. Confidence and classification are never
    upgraded by this module -- FACT requires a deliberate downstream review, not a search hit.

    ``project_id``/``lane_id`` are carried exactly as given and never interpreted here --
    see the module docstring's "lane-neutral evidence transport" note.
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
        _unit_rate(self.confidence, "confidence")


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
    result.validate()
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
    providers: Mapping[str, SearchProvider] | None = None,
    project_id: str | None = None,
    lane_id: str | None = None,
    sensitivity: str = "public",
    max_results: int = 5,
) -> ResearchQueryResult:
    """Route to an eligible search provider and wrap its hits as unverified claims.

    Degrades to zero claims -- never an exception, never a fabricated result -- when no
    provider is eligible or the routed provider isn't in ``providers``. ``router`` is the
    existing, tested ``ResourceRouter``; this function does not implement its own selection
    logic. ``providers`` defaults to ``default_search_providers()`` (Null only) when omitted --
    injecting a different registry (e.g. a test fake, or eventually a real adapter) never
    requires editing this module.

    ``project_id``/``lane_id`` are passed through to every produced claim unchanged --
    this function does not interpret or validate them (see module docstring).
    """
    if not query.strip():
        raise ValueError("invalid_research_query")
    if max_results < 1:
        raise ValueError("invalid_max_results")

    registry = providers if providers is not None else default_search_providers()
    decision = router.route(RoutingRequest(capability=SEARCH_CAPABILITY, sensitivity=sensitivity))
    if not decision.allowed or decision.provider_id not in registry:
        return ResearchQueryResult(SCHEMA_VERSION, query, project_id, lane_id, None, False, (), decision.reason)

    provider = registry[decision.provider_id]
    if provider.provider_id != decision.provider_id:
        raise ValueError("provider_registry_id_mismatch")

    retrieved_at = datetime.now(timezone.utc).isoformat()
    claims = tuple(
        _claim_from_search_result(result, query=query, retrieved_at=retrieved_at,
                                  project_id=project_id, lane_id=lane_id)
        for result in provider.search(query, max_results=max_results)
    )
    return ResearchQueryResult(SCHEMA_VERSION, query, project_id, lane_id, provider.provider_id, True,
                               claims, decision.reason)


@dataclass(frozen=True)
class SearchBenchmarkPolicy:
    """Versioned, explicit acceptance thresholds for Phase G/H provider benchmarks.

    These are NEXUS policy parameters, not measured truth -- they are meant to be
    revised (as a new ``policy_version``) as real provider data accumulates, not
    treated as fixed constants scattered through validation code.
    """

    policy_version: str
    min_coverage: float
    min_citation_accuracy: float
    min_source_quality: float
    max_hallucination_rate: float
    min_sample_size: int

    def validate(self) -> None:
        if not self.policy_version.strip():
            raise ValueError("invalid_policy_version")
        _unit_rate(self.min_coverage, "policy_min_coverage")
        _unit_rate(self.min_citation_accuracy, "policy_min_citation_accuracy")
        _unit_rate(self.min_source_quality, "policy_min_source_quality")
        _unit_rate(self.max_hallucination_rate, "policy_max_hallucination_rate")
        if isinstance(self.min_sample_size, bool) or not isinstance(self.min_sample_size, int) or self.min_sample_size < 1:
            raise ValueError("invalid_policy_min_sample_size")

    def failures(self, benchmark: "SearchProviderBenchmark") -> tuple[str, ...]:
        """Every mandatory threshold this benchmark fails to meet. Empty means it meets all of them."""
        failures = []
        if benchmark.coverage < self.min_coverage:
            failures.append(f"coverage_below_policy:{benchmark.coverage}<{self.min_coverage}")
        if benchmark.citation_accuracy < self.min_citation_accuracy:
            failures.append(f"citation_accuracy_below_policy:{benchmark.citation_accuracy}<{self.min_citation_accuracy}")
        if benchmark.source_quality < self.min_source_quality:
            failures.append(f"source_quality_below_policy:{benchmark.source_quality}<{self.min_source_quality}")
        if benchmark.hallucination_rate > self.max_hallucination_rate:
            failures.append(f"hallucination_rate_above_policy:{benchmark.hallucination_rate}>{self.max_hallucination_rate}")
        if benchmark.sample_size < self.min_sample_size:
            failures.append(f"sample_size_below_policy:{benchmark.sample_size}<{self.min_sample_size}")
        return tuple(failures)


DEFAULT_SEARCH_BENCHMARK_POLICY = SearchBenchmarkPolicy(
    policy_version="nexus.search-benchmark-policy.v1",
    min_coverage=0.6,
    min_citation_accuracy=0.8,
    min_source_quality=0.6,
    max_hallucination_rate=0.05,
    min_sample_size=20,
)


@dataclass(frozen=True)
class SearchProviderBenchmark:
    """Phase G/H measured acceptance record. A KEEP/CONNECT decision must satisfy every
    mandatory threshold in the governing ``SearchBenchmarkPolicy`` -- see ``validate``.
    BUILD/DEFER/REJECT may legitimately sit below threshold (that's the point of those
    decisions): only KEEP/CONNECT are gated.
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

    def validate(self, policy: SearchBenchmarkPolicy = DEFAULT_SEARCH_BENCHMARK_POLICY) -> None:
        if not self.provider_id.strip():
            raise ValueError("invalid_provider_id")
        for value, field in (
            (self.coverage, "coverage"), (self.freshness, "freshness"),
            (self.citation_accuracy, "citation_accuracy"), (self.source_quality, "source_quality"),
            (self.duplicate_rate, "duplicate_rate"), (self.hallucination_rate, "hallucination_rate"),
        ):
            _unit_rate(value, field)
        if (isinstance(self.latency_ms, bool) or not isinstance(self.latency_ms, (int, float)) or self.latency_ms < 0
                or isinstance(self.cost_usd_per_query, bool) or not isinstance(self.cost_usd_per_query, (int, float))
                or self.cost_usd_per_query < 0):
            raise ValueError("invalid_benchmark_cost_or_latency")
        if self.decision not in BENCHMARK_DECISIONS:
            raise ValueError("invalid_benchmark_decision")
        if isinstance(self.sample_size, bool) or not isinstance(self.sample_size, int) or self.sample_size < 1:
            raise ValueError("invalid_benchmark_sample_size")
        _utc(self.evaluated_at, "evaluated_at")

        policy.validate()
        if self.decision in _ACCEPTANCE_DECISIONS:
            failures = policy.failures(self)
            if failures:
                raise ValueError("decision_violates_benchmark_policy:" + ",".join(failures))


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
