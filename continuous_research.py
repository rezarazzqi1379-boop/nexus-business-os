"""Governed continuous-research and non-parametric improvement loop for NEXUS."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Iterable, Literal, Mapping, Sequence
from urllib.parse import urlsplit, urlunsplit

ProposalKind = Literal["ADD_TEST", "UPDATE_SKILL", "UPDATE_POLICY", "RUN_EXPERIMENT", "WATCH"]


@dataclass(frozen=True)
class ResearchTopic:
    topic_id: str
    project_id: str
    objective: str
    search_angles: tuple[str, ...]
    interval_hours: int
    max_results_per_angle: int = 10
    minimum_independent_sources: int = 2

    def validate(self) -> None:
        if not all(x.strip() for x in (self.topic_id, self.project_id, self.objective)):
            raise ValueError("invalid_research_topic")
        if not 1 <= len(self.search_angles) <= 12 or any(not x.strip() for x in self.search_angles):
            raise ValueError("invalid_search_angles")
        if len(set(self.search_angles)) != len(self.search_angles):
            raise ValueError("duplicate_search_angles")
        if not 1 <= self.interval_hours <= 24 * 90:
            raise ValueError("invalid_research_interval")
        if not 1 <= self.max_results_per_angle <= 50:
            raise ValueError("invalid_research_result_limit")
        if not 2 <= self.minimum_independent_sources <= 10:
            raise ValueError("invalid_source_convergence_threshold")


@dataclass(frozen=True)
class ResearchHit:
    provider_id: str
    query: str
    url: str
    title: str
    snippet: str
    retrieved_at: str
    published_at: str | None = None
    source_tier: str = "secondary"

    def validate(self) -> None:
        if not all(x.strip() for x in (self.provider_id, self.query, self.url, self.title, self.snippet)):
            raise ValueError("invalid_research_hit")
        parsed = urlsplit(self.url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("unsafe_research_url")
        for value in (self.retrieved_at, self.published_at):
            if value is not None:
                parsed_time = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if parsed_time.tzinfo is None:
                    raise ValueError("research_time_requires_timezone")
        if self.source_tier not in {"primary", "official", "secondary", "unknown"}:
            raise ValueError("invalid_source_tier")

    @property
    def canonical_url(self) -> str:
        parsed = urlsplit(self.url)
        host = (parsed.hostname or "").casefold()
        port = f":{parsed.port}" if parsed.port and parsed.port != 443 else ""
        path = parsed.path.rstrip("/") or "/"
        return urlunsplit(("https", host + port, path, parsed.query, ""))

    @property
    def domain(self) -> str:
        return (urlsplit(self.url).hostname or "").casefold().removeprefix("www.")


@dataclass(frozen=True)
class ResearchFinding:
    finding_id: str
    statement: str
    supporting_urls: tuple[str, ...]
    independent_domains: tuple[str, ...]
    confidence: float
    verification_state: str = "unverified"


@dataclass(frozen=True)
class ImprovementProposal:
    proposal_id: str
    topic_id: str
    kind: ProposalKind
    rationale: str
    evidence_urls: tuple[str, ...]
    acceptance_test: str
    rollback: str
    status: str = "EXPERIMENT_ONLY"
    auto_apply: bool = False


@dataclass(frozen=True)
class ResearchCycle:
    run_id: str
    topic_id: str
    queries_executed: int
    hits_reviewed: int
    unique_hits: tuple[ResearchHit, ...]
    findings: tuple[ResearchFinding, ...]
    proposals: tuple[ImprovementProposal, ...]
    coverage_domains: tuple[str, ...]


def compile_queries(topic: ResearchTopic, *, since_date: str | None = None) -> tuple[str, ...]:
    topic.validate()
    suffix = f" published since {since_date}" if since_date else ""
    return tuple(f"{topic.objective}; {angle}; prefer primary or official technical sources{suffix}"
                 for angle in topic.search_angles)


def run_research_cycle(topic: ResearchTopic, provider_batches: Mapping[str, Sequence[ResearchHit]],
                       *, run_id: str, candidate_findings: Iterable[str] = ()) -> ResearchCycle:
    """Validate/deduplicate already retrieved provider results and gate learning proposals."""
    topic.validate()
    if not run_id.strip() or not provider_batches:
        raise ValueError("invalid_research_run")
    allowed_queries = set(compile_queries(topic))
    reviewed = 0
    unique: dict[str, ResearchHit] = {}
    for provider_id, hits in sorted(provider_batches.items()):
        if not provider_id.strip() or len(hits) > len(allowed_queries) * topic.max_results_per_angle:
            raise ValueError("provider_research_budget_exceeded")
        for hit in hits:
            hit.validate()
            if hit.provider_id != provider_id:
                raise ValueError("research_provider_attribution_mismatch")
            if hit.query not in allowed_queries:
                raise ValueError("research_query_outside_plan")
            reviewed += 1
            current = unique.get(hit.canonical_url)
            if current is None or _quality(hit) > _quality(current):
                unique[hit.canonical_url] = hit

    ordered_hits = tuple(sorted(unique.values(), key=lambda h: (-_quality(h), h.canonical_url)))
    findings = _build_findings(candidate_findings, ordered_hits)
    proposals = _propose(topic, findings)
    return ResearchCycle(run_id, topic.topic_id, len(allowed_queries), reviewed, ordered_hits, findings,
                         proposals, tuple(sorted({h.domain for h in ordered_hits})))


def _quality(hit: ResearchHit) -> int:
    return {"official": 4, "primary": 3, "secondary": 2, "unknown": 1}[hit.source_tier]


def _build_findings(statements: Iterable[str], hits: tuple[ResearchHit, ...]) -> tuple[ResearchFinding, ...]:
    urls = tuple(h.canonical_url for h in hits)
    domains = tuple(sorted({h.domain for h in hits}))
    results = []
    for statement in dict.fromkeys(s.strip() for s in statements if s.strip()):
        digest = hashlib.sha256(f"{statement}|{urls}".encode()).hexdigest()[:16]
        confidence = min(.95, .35 + .15 * len(domains))
        results.append(ResearchFinding(f"finding_{digest}", statement, urls, domains, confidence))
    return tuple(results)


def _propose(topic: ResearchTopic, findings: tuple[ResearchFinding, ...]) -> tuple[ImprovementProposal, ...]:
    proposals = []
    for finding in findings:
        if len(finding.independent_domains) < topic.minimum_independent_sources:
            continue
        proposal_id = "proposal_" + hashlib.sha256(f"{topic.topic_id}|{finding.finding_id}".encode()).hexdigest()[:16]
        proposals.append(ImprovementProposal(
            proposal_id, topic.topic_id, "RUN_EXPERIMENT",
            f"Evaluate corroborated finding: {finding.statement}", finding.supporting_urls,
            "Frozen baseline comparison passes with no policy, security, or project-isolation regression.",
            "Discard experiment artifacts and retain the current production behavior.",
        ))
    return tuple(proposals)


def cycle_as_json(cycle: ResearchCycle) -> str:
    return json.dumps(asdict(cycle), ensure_ascii=False, sort_keys=True, indent=2) + "\n"


DEFAULT_RESEARCH_TOPICS = (
    ResearchTopic("agent-runtime-radar", "NEXUS_CORE", "Advances in production agent runtimes and protocols",
                  ("security and deterministic tool governance", "durability and multi-agent coordination",
                   "evaluation and observability"), 24),
    ResearchTopic("research-quality-radar", "NEXUS_CORE", "Advances in deep research agents and evidence verification",
                  ("web search coverage and retrieval", "citation provenance and claim verification",
                   "deduplication and source independence"), 24),
    ResearchTopic("safe-self-improvement-radar", "NEXUS_CORE", "Safe continual improvement for tool-using agents",
                  ("experience and skill memory", "regression and commit gates", "failure attribution and transfer"), 24),
    ResearchTopic("account-governance-radar", "NEXUS_CORE", "Safe external account and connector onboarding",
                  ("official OAuth and account lifecycle guidance", "KYC MFA consent and human-presence boundaries",
                   "credential isolation revocation and audit"), 168),
    ResearchTopic("learning-media-radar", "NEXUS_CORE", "Evidence-grounded learning from educational media",
                  ("official caption and transcript APIs", "multilingual transcription evaluation and provenance",
                   "copyright privacy retention and prompt-injection isolation"), 168),
)
