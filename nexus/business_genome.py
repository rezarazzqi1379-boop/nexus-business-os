"""NEXUS Business Genome & Opportunity Engine v0.1.

Pure-domain kernel: no network calls, no external writes. It turns observed
business evidence into explicit needs, failures, capabilities and ranked
opportunity candidates while preserving epistemic status.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Sequence


class Epistemic(str, Enum):
    FACT = "fact"
    CLAIM = "claim"
    ESTIMATE = "estimate"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"
    ASSUMPTION = "assumption"
    UNKNOWN = "unknown"


class Decision(str, Enum):
    PURSUE = "pursue"
    RESEARCH = "research"
    WATCH = "watch"
    REJECT = "reject"


@dataclass(frozen=True)
class EvidenceRef:
    source_ref: str
    observed_at: str
    epistemic: Epistemic
    summary: str
    authority: int = 1  # ordinal only; not a probability


@dataclass(frozen=True)
class BusinessGenomeRecord:
    company_id: str
    process: str
    friction: str
    need: str
    existing_solution: str | None = None
    failure: str | None = None
    reusable_capability: str | None = None
    evidence: tuple[EvidenceRef, ...] = ()
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProblemRecord:
    problem_id: str
    description: str
    affected_entities: tuple[str, ...]
    frequency: int  # 0..5 ordinal
    pain: int  # 0..5 ordinal
    ability_to_pay: int  # 0..5 ordinal
    urgency: int  # 0..5 ordinal
    evidence: tuple[EvidenceRef, ...] = ()


@dataclass(frozen=True)
class OpportunityCandidate:
    opportunity_id: str
    problem_id: str
    market: int
    access: int
    strategic_fit: int
    differentiation: int
    evidence_strength: int
    capital: int
    complexity: int
    competition: int
    time_to_revenue: int
    risk: int
    evidence: tuple[EvidenceRef, ...] = ()

    def score(self, problem: ProblemRecord) -> int:
        positive = (
            problem.pain * 3
            + problem.frequency * 2
            + problem.ability_to_pay * 3
            + problem.urgency * 2
            + self.market * 2
            + self.access * 2
            + self.strategic_fit * 3
            + self.differentiation * 2
            + self.evidence_strength * 3
        )
        penalty = (
            self.capital * 2
            + self.complexity * 2
            + self.competition
            + self.time_to_revenue * 2
            + self.risk * 3
        )
        return positive - penalty

    def decide(self, problem: ProblemRecord) -> Decision:
        if not self.evidence or self.evidence_strength <= 1:
            return Decision.RESEARCH
        score = self.score(problem)
        if self.risk >= 5 and self.evidence_strength < 4:
            return Decision.RESEARCH
        if score >= 65:
            return Decision.PURSUE
        if score >= 40:
            return Decision.RESEARCH
        if score >= 20:
            return Decision.WATCH
        return Decision.REJECT


@dataclass
class NegativeKnowledge:
    rejected_suppliers: set[str] = field(default_factory=set)
    failed_strategies: set[str] = field(default_factory=set)
    invalid_hypotheses: set[str] = field(default_factory=set)
    duplicate_actions: set[str] = field(default_factory=set)
    unreliable_sources: set[str] = field(default_factory=set)
    deprecated_requirements: set[str] = field(default_factory=set)


def dedupe_genomes(records: Iterable[BusinessGenomeRecord]) -> list[BusinessGenomeRecord]:
    """Deterministically deduplicate the same company/process/need tuple."""
    chosen: dict[tuple[str, str, str], BusinessGenomeRecord] = {}
    for record in records:
        key = (record.company_id.strip().lower(), record.process.strip().lower(), record.need.strip().lower())
        previous = chosen.get(key)
        if previous is None or len(record.evidence) > len(previous.evidence):
            chosen[key] = record
    return list(chosen.values())


def rank_opportunities(
    problems: Sequence[ProblemRecord], candidates: Sequence[OpportunityCandidate]
) -> list[tuple[OpportunityCandidate, Decision, int]]:
    by_problem = {p.problem_id: p for p in problems}
    ranked: list[tuple[OpportunityCandidate, Decision, int]] = []
    for candidate in candidates:
        problem = by_problem.get(candidate.problem_id)
        if problem is None:
            continue
        ranked.append((candidate, candidate.decide(problem), candidate.score(problem)))
    return sorted(ranked, key=lambda row: row[2], reverse=True)
