"""Evidence-aware buyer scoring for the NEXUS steel sales lane.

No network calls and no side effects. Scores are triage aids, never facts or
authorization to enrich, contact, quote, export or transact.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class BuyerEvidence:
    named_company: bool
    official_application_evidence: bool = False
    official_material_evidence: bool = False
    independent_trade_evidence: bool = False
    dimension_fit: bool = False
    end_user: bool = False
    decision_maker_found: bool = False
    logistics_feasible: bool = False
    payment_feasible: bool = False
    compliance_required: bool = False
    compliance_cleared: bool = False

@dataclass(frozen=True)
class BuyerScore:
    buyer_fit: int
    strategic_value: int
    enrichment_confidence: int
    classification: str
    blockers: tuple[str, ...]

def score_buyer(e: BuyerEvidence) -> BuyerScore:
    if not e.named_company:
        return BuyerScore(0,0,0,"REJECT",("named_company_required",))
    fit = (20 if e.official_application_evidence else 0) + (25 if e.official_material_evidence else 0)
    fit += (20 if e.independent_trade_evidence else 0) + (20 if e.dimension_fit else 0)
    fit += (15 if e.end_user else 5)
    strategic = min(100, fit + (10 if e.logistics_feasible else 0) + (10 if e.payment_feasible else 0))
    enrich = min(100, fit + (10 if e.decision_maker_found else 0))
    blockers=[]
    if not e.official_application_evidence: blockers.append("application_evidence_missing")
    if not e.official_material_evidence: blockers.append("material_evidence_missing")
    if not e.dimension_fit: blockers.append("dimension_fit_unverified")
    if e.compliance_required and not e.compliance_cleared: blockers.append("compliance_clearance_required")
    classification = "TIER_A" if fit >= 70 else "TIER_B" if fit >= 45 else "TIER_C"
    return BuyerScore(fit, strategic, enrich, classification, tuple(blockers))
