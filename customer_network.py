from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol


ALLOWED_SOURCE_TYPES = frozenset({"official", "registry", "trade_directory", "customer_referral", "public_tender"})
ALLOWED_DECISIONS = frozenset({"approve_research", "reject", "hold"})


@dataclass(frozen=True)
class LeadEvidence:
    source_type: str
    source_ref: str
    observed_at: str
    statement: str


@dataclass(frozen=True)
class LeadCandidate:
    lead_id: str
    organization: str
    country: str
    project_id: str
    need_signal: str
    evidence: tuple[LeadEvidence, ...]
    fit: int
    urgency: int
    access: int
    sanctions_risk: int

    def snapshot(self) -> str:
        body = {
            "lead_id": self.lead_id,
            "organization": self.organization,
            "country": self.country,
            "project_id": self.project_id,
            "need_signal": self.need_signal,
            "evidence": [item.__dict__ for item in self.evidence],
            "fit": self.fit,
            "urgency": self.urgency,
            "access": self.access,
            "sanctions_risk": self.sanctions_risk,
        }
        return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.snapshot().encode()).hexdigest()


@dataclass(frozen=True)
class RankedLead:
    candidate: LeadCandidate
    tier: str
    reasons: tuple[str, ...]


class LeadSource(Protocol):
    """Portable adapter boundary for a read-only lead source."""

    source_id: str

    def discover(self, project_id: str) -> Iterable[LeadCandidate]: ...


def validate_candidate(candidate: LeadCandidate) -> None:
    if not all((candidate.lead_id.strip(), candidate.organization.strip(), candidate.country.strip(), candidate.project_id.strip())):
        raise ValueError("missing_lead_identity")
    if not candidate.need_signal.strip() or len(candidate.need_signal) > 2_000:
        raise ValueError("invalid_need_signal")
    if not candidate.evidence:
        raise ValueError("evidence_required")
    for item in candidate.evidence:
        if item.source_type not in ALLOWED_SOURCE_TYPES:
            raise ValueError("invalid_source_type")
        if not item.source_ref.strip() or not item.observed_at.strip() or not item.statement.strip():
            raise ValueError("invalid_evidence")
    for value in (candidate.fit, candidate.urgency, candidate.access, candidate.sanctions_risk):
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 5:
            raise ValueError("invalid_lead_score")


def rank_candidate(candidate: LeadCandidate) -> RankedLead:
    validate_candidate(candidate)
    independent_refs = {item.source_ref for item in candidate.evidence}
    reasons = [f"{len(independent_refs)} evidence reference(s)"]
    if candidate.sanctions_risk >= 4:
        return RankedLead(candidate, "manual_risk_review", tuple(reasons + ["high sanctions/payment risk"]))
    if candidate.fit >= 4 and candidate.urgency >= 3 and len(independent_refs) >= 2:
        return RankedLead(candidate, "priority_research", tuple(reasons + ["strong fit and current need signal"]))
    if candidate.fit >= 3:
        return RankedLead(candidate, "research", tuple(reasons + ["plausible fit; qualification incomplete"]))
    return RankedLead(candidate, "hold", tuple(reasons + ["insufficient demonstrated fit"]))


def discover_portably(project_id: str, sources: Iterable[LeadSource], *, max_candidates: int = 100) -> tuple[RankedLead, ...]:
    if not 1 <= max_candidates <= 500:
        raise ValueError("invalid_candidate_limit")
    candidates: dict[str, LeadCandidate] = {}
    for source in sources:
        for candidate in source.discover(project_id):
            validate_candidate(candidate)
            if candidate.project_id != project_id:
                raise ValueError("cross_project_candidate")
            previous = candidates.get(candidate.lead_id)
            if previous and previous.digest != candidate.digest:
                raise ValueError("lead_id_collision")
            candidates[candidate.lead_id] = candidate
            if len(candidates) > max_candidates:
                raise ValueError("candidate_limit_exceeded")
    tier_order = {"priority_research": 0, "research": 1, "manual_risk_review": 2, "hold": 3}
    ranked = [rank_candidate(item) for item in candidates.values()]
    return tuple(sorted(ranked, key=lambda item: (tier_order[item.tier], item.candidate.lead_id)))


class LeadDecisionStore:
    """Records review only. Approval never authorizes outreach or data writes."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as db:
            with db:
                db.execute(
                    "CREATE TABLE IF NOT EXISTS lead_decisions ("
                    "lead_id TEXT PRIMARY KEY, candidate_sha256 TEXT NOT NULL, decision TEXT NOT NULL, "
                    "reviewer TEXT NOT NULL, decided_at TEXT NOT NULL)"
                )

    def decide(self, candidate: LeadCandidate, decision: str, reviewer: str, decided_at: str) -> None:
        validate_candidate(candidate)
        if decision not in ALLOWED_DECISIONS:
            raise ValueError("invalid_lead_decision")
        if not reviewer.strip() or not decided_at.strip():
            raise ValueError("review_metadata_required")
        with closing(sqlite3.connect(self.path)) as db:
            with db:
                row = db.execute(
                    "SELECT candidate_sha256, decision FROM lead_decisions WHERE lead_id=?", (candidate.lead_id,)
                ).fetchone()
                if row and row != (candidate.digest, decision):
                    raise ValueError("decision_conflict")
                db.execute(
                    "INSERT OR IGNORE INTO lead_decisions VALUES (?, ?, ?, ?, ?)",
                    (candidate.lead_id, candidate.digest, decision, reviewer, decided_at),
                )

    def get(self, lead_id: str) -> tuple[str, str] | None:
        with closing(sqlite3.connect(self.path)) as db:
            row = db.execute(
                "SELECT candidate_sha256, decision FROM lead_decisions WHERE lead_id=?", (lead_id,)
            ).fetchone()
        return (str(row[0]), str(row[1])) if row else None
