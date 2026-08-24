"""NEXUS Business Genome & Opportunity Engine v0.1.

Pure-domain shadow kernel. No network calls, no external writes, no autonomous
promotion. Scores are ordinal decision aids, never probabilities.
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


def _ordinal(name: str, value: int, low: int = 0, high: int = 5) -> list[str]:
    if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
        return [f"{name} must be integer {low}..{high}"]
    return []


def _required(name: str, value: str) -> list[str]:
    if not isinstance(value, str) or not value.strip():
        return [f"{name} is required"]
    return []


@dataclass(frozen=True)
class EvidenceRef:
    source_ref: str
    observed_at: str
    epistemic: Epistemic
    summary: str
    authority: int = 1

    def validate(self) -> list[str]:
        errors = _required("source_ref", self.source_ref)
        errors += _required("observed_at", self.observed_at)
        errors += _required("summary", self.summary)
        if not isinstance(self.epistemic, Epistemic):
            errors.append("epistemic must be Epistemic")
        errors += _ordinal("authority", self.authority)
        return errors


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

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name, value in (("company_id", self.company_id), ("process", self.process), ("friction", self.friction), ("need", self.need)):
            errors += _required(name, value)
        for item in self.evidence:
            errors += item.validate()
        return errors


@dataclass(frozen=True)
class ProblemRecord:
    problem_id: str
    description: str
    affected_entities: tuple[str, ...]
    frequency: int
    pain: int
    ability_to_pay: int
    urgency: int
    evidence: tuple[EvidenceRef, ...] = ()

    def validate(self) -> list[str]:
        errors = _required("problem_id", self.problem_id) + _required("description", self.description)
        if not self.affected_entities or any(not x.strip() for x in self.affected_entities):
            errors.append("affected_entities requires at least one non-empty entity")
        for name in ("frequency", "pain", "ability_to_pay", "urgency"):
            errors += _ordinal(name, getattr(self, name))
        for item in self.evidence:
            errors += item.validate()
        return errors


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
    blocking_unknowns: tuple[str, ...] = ()

    def validate(self) -> list[str]:
        errors = _required("opportunity_id", self.opportunity_id) + _required("problem_id", self.problem_id)
        for name in ("market", "access", "strategic_fit", "differentiation", "evidence_strength", "capital", "complexity", "competition", "time_to_revenue", "risk"):
            errors += _ordinal(name, getattr(self, name))
        for item in self.evidence:
            errors += item.validate()
        if any(not isinstance(item, str) or not item.strip() for item in self.blocking_unknowns):
            errors.append("blocking_unknowns must contain non-empty strings")
        return errors

    def score(self, problem: ProblemRecord) -> int:
        if self.validate() or problem.validate():
            raise ValueError("invalid opportunity/problem input")
        positive = (
            problem.pain * 3 + problem.frequency * 2 + problem.ability_to_pay * 3 + problem.urgency * 2
            + self.market * 2 + self.access * 2 + self.strategic_fit * 3 + self.differentiation * 2
            + self.evidence_strength * 3
        )
        penalty = self.capital * 2 + self.complexity * 2 + self.competition + self.time_to_revenue * 2 + self.risk * 3
        return positive - penalty

    def decide(self, problem: ProblemRecord) -> Decision:
        if self.validate() or problem.validate():
            return Decision.RESEARCH
        if self.blocking_unknowns:
            return Decision.RESEARCH
        if not self.evidence or self.evidence_strength <= 1:
            return Decision.RESEARCH
        supported_classes = {item.epistemic for item in self.evidence}
        if supported_classes <= {Epistemic.HYPOTHESIS, Epistemic.ASSUMPTION, Epistemic.UNKNOWN}:
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
    chosen: dict[tuple[str, str, str], BusinessGenomeRecord] = {}
    for record in records:
        if record.validate():
            continue
        key = (record.company_id.strip().lower(), record.process.strip().lower(), record.need.strip().lower())
        previous = chosen.get(key)
        if previous is None or len(record.evidence) > len(previous.evidence):
            chosen[key] = record
    return list(chosen.values())


def rank_opportunities(problems: Sequence[ProblemRecord], candidates: Sequence[OpportunityCandidate]) -> list[tuple[OpportunityCandidate, Decision, int]]:
    by_problem = {p.problem_id: p for p in problems if not p.validate()}
    ranked: list[tuple[OpportunityCandidate, Decision, int]] = []
    for candidate in candidates:
        problem = by_problem.get(candidate.problem_id)
        if problem is None or candidate.validate():
            continue
        ranked.append((candidate, candidate.decide(problem), candidate.score(problem)))
    return sorted(ranked, key=lambda row: row[2], reverse=True)
