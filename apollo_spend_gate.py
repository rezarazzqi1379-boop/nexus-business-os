"""Separate Apollo paid-enrichment spend confidence from buyer fit."""
from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class SpendDecision:
    confidence:int; eligible:bool; blockers:tuple[str,...]
def assess_spend(*,buyer_fit:int,evidence_current:bool,dedup_clear:bool,free_resolution_attempted:bool,
                 existing_contact:bool,expected_value:bool,paid_credit_required:bool=True)->SpendDecision:
    blockers=[]
    if buyer_fit<70:blockers.append("buyer_fit_below_threshold")
    if not evidence_current:blockers.append("current_evidence_required")
    if not dedup_clear:blockers.append("dedup_not_clear")
    if not free_resolution_attempted:blockers.append("free_resolution_required_first")
    if existing_contact:blockers.append("existing_contact_use_first")
    if not expected_value:blockers.append("commercial_value_not_established")
    score=max(0,min(100,buyer_fit+(10 if evidence_current else 0)+(5 if dedup_clear else 0)+(5 if expected_value else 0)))
    eligible=paid_credit_required and not blockers
    return SpendDecision(score,eligible,tuple(blockers))
