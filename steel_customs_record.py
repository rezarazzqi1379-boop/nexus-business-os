"""Structured customs-classification evidence record.

A candidate HS code is not a final classification until product evidence,
jurisdiction and review authority are recorded.
"""
from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class CustomsRecord:
    jurisdiction:str
    candidate_hs:str
    product_form:str
    manufacturing_condition:str
    further_worked:bool|None
    evidence_refs:tuple[str,...]
    reviewed_by:str|None=None
    final:bool=False
def validate_customs_record(r:CustomsRecord)->tuple[str,...]:
    e=[]
    if not r.jurisdiction.strip():e.append("jurisdiction_required")
    if not r.product_form.strip():e.append("product_form_required")
    if not r.manufacturing_condition.strip():e.append("manufacturing_condition_required")
    if not r.evidence_refs:e.append("evidence_required")
    if r.final and not r.reviewed_by:e.append("final_requires_review_authority")
    if r.final and len(r.candidate_hs)<6:e.append("final_requires_subheading")
    return tuple(e)
