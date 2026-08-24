from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


EVIDENCE_CLASSES = frozenset({"FACT", "CLAIM", "ESTIMATE", "ASSUMPTION", "UNKNOWN"})
SIGNAL_TYPES = frozenset({
    "public_tender", "procurement_request", "expansion", "plant_change",
    "hiring", "regulatory_change", "email_reply", "customer_referral",
})
SOURCE_TYPES = frozenset({"official", "registry", "public_tender", "gmail", "notion", "customer_referral"})
FIT_LEVELS = ("none", "weak", "plausible", "strong")
TIMING_LEVELS = ("unknown", "later", "current", "urgent")
RELATIONSHIP_LEVELS = ("none", "cold", "direct", "warm_referral")
COMPANY_ROLES = ("buyer", "supplier", "integrator", "referrer", "unknown")


def _utc(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_observed_at") from exc
    if parsed.tzinfo is None:
        raise ValueError("observed_at_must_include_timezone")
    return parsed.astimezone(timezone.utc).isoformat()


@dataclass(frozen=True)
class NeedEvidence:
    evidence_id: str
    classification: str
    source_type: str
    source_ref: str
    observed_at: str
    statement: str

    def validate(self) -> None:
        if self.classification not in EVIDENCE_CLASSES:
            raise ValueError("invalid_evidence_class")
        if self.source_type not in SOURCE_TYPES:
            raise ValueError("invalid_source_type")
        if not all(isinstance(v, str) and v.strip() for v in (
            self.evidence_id, self.source_ref, self.statement
        )):
            raise ValueError("invalid_evidence")
        if len(self.statement) > 2_000:
            raise ValueError("evidence_statement_too_long")
        _utc(self.observed_at)
        if self.classification == "FACT" and self.source_type not in {
            "official", "registry", "public_tender", "gmail", "notion"
        }:
            raise ValueError("fact_requires_retrievable_primary_evidence")


@dataclass(frozen=True)
class NeedSignal:
    signal_id: str
    company_id: str
    company_name: str
    company_role: str
    project_id: str
    signal_type: str
    need_hypothesis: str
    fit: str
    timing: str
    relationship: str
    evidence: tuple[NeedEvidence, ...]
    contradictions: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()

    def validate(self) -> None:
        if not all(isinstance(v, str) and v.strip() for v in (
            self.signal_id, self.company_id, self.company_name,
            self.project_id, self.need_hypothesis,
        )):
            raise ValueError("missing_signal_identity")
        if self.signal_type not in SIGNAL_TYPES:
            raise ValueError("invalid_signal_type")
        if self.fit not in FIT_LEVELS or self.timing not in TIMING_LEVELS:
            raise ValueError("invalid_priority_level")
        if self.relationship not in RELATIONSHIP_LEVELS:
            raise ValueError("invalid_relationship_level")
        if self.company_role not in COMPANY_ROLES:
            raise ValueError("invalid_company_role")
        if not self.evidence:
            raise ValueError("evidence_required")
        ids: set[str] = set()
        for item in self.evidence:
            item.validate()
            if item.evidence_id in ids:
                raise ValueError("duplicate_evidence_id")
            ids.add(item.evidence_id)
        if len(self.need_hypothesis) > 2_000:
            raise ValueError("need_hypothesis_too_long")
        if any(not isinstance(v, str) or not v.strip() for v in self.contradictions + self.unknowns):
            raise ValueError("invalid_review_item")

    @property
    def digest(self) -> str:
        self.validate()
        payload = {
            "signal_id": self.signal_id, "company_id": self.company_id,
            "company_name": self.company_name, "company_role": self.company_role,
            "project_id": self.project_id,
            "signal_type": self.signal_type, "need_hypothesis": self.need_hypothesis,
            "fit": self.fit, "timing": self.timing, "relationship": self.relationship,
            "evidence": [item.__dict__ for item in self.evidence],
            "contradictions": self.contradictions, "unknowns": self.unknowns,
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode()).hexdigest()


@dataclass(frozen=True)
class NeedAssessment:
    signal: NeedSignal
    disposition: str
    reasons: tuple[str, ...]
    next_safe_action: str


def assess_need(signal: NeedSignal) -> NeedAssessment:
    signal.validate()
    independent_refs = {item.source_ref for item in signal.evidence}
    fact_refs = {item.source_ref for item in signal.evidence if item.classification == "FACT"}
    reasons = [f"{len(independent_refs)} evidence reference(s)", f"{len(fact_refs)} fact reference(s)"]

    if signal.contradictions:
        return NeedAssessment(signal, "manual_review", tuple(reasons + ["unresolved contradiction"]), "resolve_contradictions")
    if signal.company_role in {"supplier", "integrator"}:
        return NeedAssessment(signal, "supply_research", tuple(reasons + ["counterparty is not a buyer lead"]), "qualify_supply_or_solution")
    if signal.fit == "none":
        return NeedAssessment(signal, "hold", tuple(reasons + ["no demonstrated solution fit"]), "preserve_only")
    if not fact_refs:
        return NeedAssessment(signal, "verify", tuple(reasons + ["hypothesis lacks verified fact"]), "verify_primary_source")
    if signal.fit == "strong" and signal.timing in {"current", "urgent"} and len(independent_refs) >= 2:
        return NeedAssessment(signal, "priority_research", tuple(reasons + ["strong fit and current timing"]), "prepare_research_brief")
    return NeedAssessment(signal, "research", tuple(reasons + ["qualification incomplete"]), "fill_unknowns")


def build_research_queue(signals: Iterable[NeedSignal], *, limit: int = 100) -> tuple[NeedAssessment, ...]:
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 500:
        raise ValueError("invalid_signal_limit")
    unique: dict[str, NeedSignal] = {}
    company_projects: dict[tuple[str, str, str], str] = {}
    for signal in signals:
        signal.validate()
        previous = unique.get(signal.signal_id)
        if previous and previous.digest != signal.digest:
            raise ValueError("signal_id_collision")
        unique[signal.signal_id] = signal
        key = (signal.company_id, signal.project_id, signal.signal_type)
        prior_digest = company_projects.get(key)
        if prior_digest and prior_digest != signal.digest:
            raise ValueError("duplicate_company_need_requires_fusion")
        company_projects[key] = signal.digest
        if len(unique) > limit:
            raise ValueError("signal_limit_exceeded")
    order = {"priority_research": 0, "research": 1, "supply_research": 2, "verify": 3, "manual_review": 4, "hold": 5}
    assessed = [assess_need(item) for item in unique.values()]
    return tuple(sorted(assessed, key=lambda item: (order[item.disposition], item.signal.signal_id)))


def research_brief(assessment: NeedAssessment) -> dict[str, object]:
    if assessment.disposition not in {"priority_research", "research", "supply_research"}:
        raise ValueError("signal_not_ready_for_research_brief")
    signal = assessment.signal
    return {
        "schema_version": "nexus.need-brief.v1",
        "signal_id": signal.signal_id,
        "signal_digest": signal.digest,
        "company": {"id": signal.company_id, "name": signal.company_name, "role": signal.company_role},
        "project_id": signal.project_id,
        "need_hypothesis": signal.need_hypothesis,
        "evidence_refs": sorted({item.source_ref for item in signal.evidence}),
        "unknowns": list(signal.unknowns),
        "relationship_path": signal.relationship,
        "allowed_action": "research_only",
        "outreach_authorized": False,
    }
