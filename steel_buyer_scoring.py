"""Evidence-aware buyer scoring for the NEXUS steel sales lane.

Evidence provenance is mandatory for positive evidence. Scores are triage aids,
never authorization to enrich, contact, quote, export or transact.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class BuyerEvidence:
    named_company: bool
    official_application_evidence: bool=False
    official_material_evidence: bool=False
    independent_trade_evidence: bool=False
    dimension_fit: bool=False
    end_user: bool=False
    decision_maker_found: bool=False
    logistics_feasible: bool=False
    payment_feasible: bool=False
    compliance_required: bool=False
    compliance_cleared: bool=False
    application_refs:tuple[str,...]=()
    material_refs:tuple[str,...]=()
    trade_refs:tuple[str,...]=()
    dimension_refs:tuple[str,...]=()

@dataclass(frozen=True)
class BuyerScore:
    buyer_fit:int; strategic_value:int; enrichment_confidence:int
    classification:str; blockers:tuple[str,...]

def _grounded(flag:bool, refs:tuple[str,...])->bool:
    return flag and bool(refs) and all(isinstance(x,str) and x.strip() for x in refs)

def score_buyer(e:BuyerEvidence)->BuyerScore:
    if not e.named_company:return BuyerScore(0,0,0,"REJECT",("named_company_required",))
    app=_grounded(e.official_application_evidence,e.application_refs)
    mat=_grounded(e.official_material_evidence,e.material_refs)
    trade=_grounded(e.independent_trade_evidence,e.trade_refs)
    dim=_grounded(e.dimension_fit,e.dimension_refs)
    fit=(20 if app else 0)+(25 if mat else 0)+(20 if trade else 0)+(20 if dim else 0)+(15 if e.end_user else 5)
    strategic=min(100,fit+(10 if e.logistics_feasible else 0)+(10 if e.payment_feasible else 0))
    enrich=min(100,fit+(10 if e.decision_maker_found else 0))
    blockers=[]
    if e.official_application_evidence and not app:blockers.append("application_evidence_ref_required")
    elif not app:blockers.append("application_evidence_missing")
    if e.official_material_evidence and not mat:blockers.append("material_evidence_ref_required")
    elif not mat:blockers.append("material_evidence_missing")
    if e.independent_trade_evidence and not trade:blockers.append("trade_evidence_ref_required")
    if e.dimension_fit and not dim:blockers.append("dimension_evidence_ref_required")
    elif not dim:blockers.append("dimension_fit_unverified")
    if e.compliance_required and not e.compliance_cleared:blockers.append("compliance_clearance_required")
    cls="TIER_A" if fit>=70 else "TIER_B" if fit>=45 else "TIER_C"
    return BuyerScore(fit,strategic,enrich,cls,tuple(blockers))
