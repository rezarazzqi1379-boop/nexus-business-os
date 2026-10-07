"""Conservative HS candidate reasoning for alloy-steel bars/forgings.

This module never returns a final customs classification. It narrows candidate
families and records the missing manufacturing facts that a broker/authority
must resolve.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class HSAssessment:
    candidate_heading:str
    confidence:str
    rationale:str
    blockers:tuple[str,...]

def assess_alloy_bar_hs(*, alloy_steel:bool, bar_or_rod:bool, condition:str|None,
                        further_worked:bool|None)->HSAssessment:
    if not alloy_steel or not bar_or_rod:
        return HSAssessment("UNKNOWN","LOW","7228 bar/rod premise not established",("product_form_or_material_unverified",))
    if further_worked is None:
        return HSAssessment("7228","LOW","Other alloy-steel bar/rod family only; finishing state unknown",("further_working_state_required",))
    if further_worked:
        return HSAssessment("7228","LOW","Further-worked goods need a more specific customs review",("final_subheading_requires_customs_review",))
    norm=(condition or "").strip().casefold()
    if norm in {"forged","not further worked than forged"}:
        return HSAssessment("722840","MEDIUM","Candidate: bars/rods not further worked than forged",("jurisdictional_subheading_and_product_evidence_required",))
    if norm in {"hot-rolled","hot drawn","hot-drawn","extruded"}:
        return HSAssessment("722830","MEDIUM","Candidate: other bars/rods not further worked than hot-rolled/hot-drawn/extruded",("jurisdictional_subheading_and_product_evidence_required",))
    return HSAssessment("7228","LOW","Manufacturing condition is not normalized to a supported candidate",("manufacturing_condition_required",))
