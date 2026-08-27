from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

Maturity = Literal["RESEARCH", "SANDBOX", "PILOT", "ADOPTED"]
Decision = Literal["REJECT", "WATCH", "EXPERIMENT", "ADOPT_ADAPTER"]

_ALLOWED_MATURITY = {"RESEARCH", "SANDBOX", "PILOT", "ADOPTED"}
_ALLOWED_DECISIONS = {"REJECT", "WATCH", "EXPERIMENT", "ADOPT_ADAPTER"}


@dataclass(frozen=True)
class TechnologyCandidate:
    candidate_id: str
    name: str
    category: str
    source_url: str
    observed_at: str
    problem_fit: int
    implementation_cost: int
    overlap_risk: int
    lock_in_risk: int
    security_risk: int
    evidence_quality: int
    acceptance_test: str
    rollback: str
    maturity: Maturity = "RESEARCH"
    decision: Decision = "WATCH"
    notes: str = ""

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        for field_name in ("candidate_id", "name", "category", "source_url", "observed_at", "acceptance_test", "rollback"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{field_name} is required")
        for field_name in (
            "problem_fit",
            "implementation_cost",
            "overlap_risk",
            "lock_in_risk",
            "security_risk",
            "evidence_quality",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, int) or not 0 <= value <= 5:
                errors.append(f"{field_name} must be an integer 0..5")
        if self.maturity not in _ALLOWED_MATURITY:
            errors.append("unsupported maturity")
        if self.decision not in _ALLOWED_DECISIONS:
            errors.append("unsupported decision")
        if self.decision == "ADOPT_ADAPTER" and self.maturity == "RESEARCH":
            errors.append("research-only candidate cannot be adopted")
        return tuple(errors)


def value_score(candidate: TechnologyCandidate) -> int:
    """Deterministic portfolio score, not a probability.

    Rewards fit/evidence and penalizes cost, overlap, lock-in and security exposure.
    A high score is only a prioritization signal; it never authorizes installation,
    external connection, deployment or production use.
    """
    errors = candidate.validate()
    if errors:
        raise ValueError("invalid candidate: " + "; ".join(errors))
    return (
        3 * candidate.problem_fit
        + 2 * candidate.evidence_quality
        - candidate.implementation_cost
        - candidate.overlap_risk
        - candidate.lock_in_risk
        - 2 * candidate.security_risk
    )


def recommend(candidate: TechnologyCandidate) -> Decision:
    score = value_score(candidate)
    if candidate.security_risk >= 5 or candidate.evidence_quality <= 1:
        return "REJECT"
    if score >= 12 and candidate.overlap_risk <= 2:
        return "EXPERIMENT"
    if score >= 6:
        return "WATCH"
    return "REJECT"


def ranked_candidates(candidates: Sequence[TechnologyCandidate]) -> tuple[TechnologyCandidate, ...]:
    seen: set[str] = set()
    for candidate in candidates:
        if candidate.candidate_id in seen:
            raise ValueError(f"duplicate candidate_id: {candidate.candidate_id}")
        seen.add(candidate.candidate_id)
        errors = candidate.validate()
        if errors:
            raise ValueError(f"{candidate.candidate_id}: " + "; ".join(errors))
    return tuple(sorted(candidates, key=lambda item: (-value_score(item), item.candidate_id)))


def research_snapshot() -> tuple[TechnologyCandidate, ...]:
    """Fresh research candidates observed 2026-08-27 from primary documentation.

    These records are Tier-D research inputs. They are deliberately not authority and
    do not install dependencies. Each candidate must pass its acceptance test before
    any promotion beyond RESEARCH/SANDBOX.
    """
    return (
        TechnologyCandidate(
            candidate_id="TECH-OPENAI-AGENTS-SDK",
            name="OpenAI Agents SDK",
            category="agent-runtime",
            source_url="https://openai.github.io/openai-agents-python/",
            observed_at="2026-08-27",
            problem_fit=5,
            implementation_cost=2,
            overlap_risk=3,
            lock_in_risk=2,
            security_risk=2,
            evidence_quality=5,
            acceptance_test="Run one read-only NEXUS vertical with tools, guardrails, HITL and trace correlation; zero authority-policy regressions.",
            rollback="Remove adapter dependency and route execution back to the existing NEXUS runner/control plane.",
            maturity="SANDBOX",
            decision="EXPERIMENT",
            notes="Use as an execution adapter only; NEXUS authority, project isolation and approval policy remain canonical.",
        ),
        TechnologyCandidate(
            candidate_id="TECH-MCP-REGISTRY-BROKER",
            name="Official MCP Registry + NEXUS allowlist broker",
            category="tool-discovery",
            source_url="https://registry.modelcontextprotocol.io/docs",
            observed_at="2026-08-27",
            problem_fit=5,
            implementation_cost=2,
            overlap_risk=1,
            lock_in_risk=1,
            security_risk=3,
            evidence_quality=5,
            acceptance_test="Discover candidate MCP servers but expose none to execution until provenance, permissions, tool schema and trust policy pass deterministic checks.",
            rollback="Disable registry discovery and retain the static connector/tool registry.",
            maturity="SANDBOX",
            decision="EXPERIMENT",
            notes="High value because it turns ad-hoc tool hunting into governed discovery; never auto-connect third-party servers.",
        ),
        TechnologyCandidate(
            candidate_id="TECH-TEMPORAL",
            name="Temporal",
            category="durable-execution",
            source_url="https://docs.temporal.io/",
            observed_at="2026-08-27",
            problem_fit=4,
            implementation_cost=5,
            overlap_risk=2,
            lock_in_risk=2,
            security_risk=2,
            evidence_quality=5,
            acceptance_test="Demonstrate restart-safe resume of one multi-day waiting workflow with idempotent side-effect gates and no duplicated external action.",
            rollback="Keep current scheduler/task state and remove Temporal worker/service from the execution path.",
            maturity="RESEARCH",
            decision="WATCH",
            notes="Strong durability fit, but infrastructure cost is not justified until a real long-running vertical repeatedly loses state or needs crash-safe resume.",
        ),
        TechnologyCandidate(
            candidate_id="TECH-MS-AGENT-FRAMEWORK",
            name="Microsoft Agent Framework",
            category="agent-workflow-runtime",
            source_url="https://learn.microsoft.com/en-us/agent-framework/",
            observed_at="2026-08-27",
            problem_fit=4,
            implementation_cost=3,
            overlap_risk=4,
            lock_in_risk=2,
            security_risk=2,
            evidence_quality=5,
            acceptance_test="Benchmark the same NEXUS read-only vertical against the current runtime and Agents SDK on correctness, resumability, tool policy and implementation complexity.",
            rollback="Discard benchmark branch; no canonical state migration.",
            maturity="RESEARCH",
            decision="WATCH",
            notes="Interesting workflow/HITL/checkpoint feature set, but currently overlaps heavily with NEXUS and should not become a second orchestration core without measurable advantage.",
        ),
        TechnologyCandidate(
            candidate_id="TECH-N8N-ADAPTERS",
            name="n8n event/trigger adapters",
            category="automation-adapter",
            source_url="https://n8n.io/ai-agents/",
            observed_at="2026-08-27",
            problem_fit=4,
            implementation_cost=2,
            overlap_risk=2,
            lock_in_risk=2,
            security_risk=3,
            evidence_quality=4,
            acceptance_test="Trigger one read-only research/inbox workflow into NEXUS with stable IDs, dedupe, retries and an approval-blocked external-action path.",
            rollback="Disable webhook/schedule adapter; canonical state and logic remain in NEXUS.",
            maturity="RESEARCH",
            decision="EXPERIMENT",
            notes="Best used for triggers and plumbing, not as the business/engineering authority or decision layer.",
        ),
        TechnologyCandidate(
            candidate_id="TECH-LANGGRAPH",
            name="LangGraph",
            category="durable-agent-graph",
            source_url="https://docs.langchain.com/oss/python/langgraph/",
            observed_at="2026-08-27",
            problem_fit=3,
            implementation_cost=3,
            overlap_risk=5,
            lock_in_risk=2,
            security_risk=2,
            evidence_quality=4,
            acceptance_test="Only benchmark if a concrete workflow cannot be expressed cleanly by the existing NEXUS state machine; require lower defect rate or materially simpler recovery.",
            rollback="Discard benchmark; retain governed NEXUS graph and task state.",
            maturity="RESEARCH",
            decision="WATCH",
            notes="Potentially useful, but highest overlap with the graph/control-plane work already implemented.",
        ),
    )
