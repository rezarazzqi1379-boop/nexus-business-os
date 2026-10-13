"""NEXUS v11 governance helpers integrated on the tested #103 substrate.

This module does not execute providers or protected actions. Capability admission is
an independent governance concern. Commercial maturity is a projection only: it
must not bypass the canonical #103 conversion/readiness/stock/contradiction gates.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

class Admission(str, Enum):
    KEEP="KEEP"; MERGE="MERGE"; SANDBOX="SANDBOX"; REJECT="REJECT"

@dataclass(frozen=True)
class CapabilityCandidate:
    capability_id:str
    functions:frozenset[str]
    evidence_refs:tuple[str,...]
    acceptance_tests:tuple[str,...]
    sandboxed:bool=False
    requires_secrets:bool=False
    external_write:bool=False
    def validate(self)->None:
        if not self.capability_id.strip() or not self.functions: raise ValueError("capability_identity_and_functions_required")
        if not self.evidence_refs: raise ValueError("capability_evidence_required")
        if not self.acceptance_tests: raise ValueError("capability_acceptance_tests_required")

@dataclass(frozen=True)
class AdmissionDecision:
    action:Admission
    reason:str
    overlap_ratio:float
    requires_exact_approval:bool

def evaluate_capability_admission(candidate:CapabilityCandidate, incumbents:Iterable[CapabilityCandidate], *, max_overlap:float=.70)->AdmissionDecision:
    candidate.validate()
    if not 0<=max_overlap<=1: raise ValueError("invalid_overlap_threshold")
    items=tuple(incumbents)
    for item in items: item.validate()
    best=0.0
    for item in items:
        union=candidate.functions|item.functions
        best=max(best,len(candidate.functions&item.functions)/len(union))
    if best>=max_overlap: return AdmissionDecision(Admission.MERGE,"material_overlap_with_existing_capability",best,False)
    if candidate.external_write or candidate.requires_secrets: return AdmissionDecision(Admission.SANDBOX,"consequential_or_secret_bearing_capability",best,True)
    if not candidate.sandboxed: return AdmissionDecision(Admission.SANDBOX,"new_capability_requires_sandbox_evaluation",best,False)
    return AdmissionDecision(Admission.KEEP,"bounded_tested_sandbox_candidate",best,False)

class ConversionStage(str, Enum):
    DISCOVERED="DISCOVERED"
    EVIDENCED="EVIDENCED"
    BUYER_VERIFIED="BUYER_VERIFIED"
    DECISION_MAKER_VERIFIED="DECISION_MAKER_VERIFIED"
    CONTACT_VERIFIED="CONTACT_VERIFIED"
    OUTREACH_READY="OUTREACH_READY"

@dataclass(frozen=True)
class ConversionProjection:
    company_identity:bool=False
    product_application:bool=False
    buyer_role:bool=False
    procurement_signal:bool=False
    decision_maker:bool=False
    verified_contact:bool=False
    independent_sources:int=0
    unresolved_contradiction:bool=False
    canonical_conversion_ready:bool=False
    canonical_sales_readiness:str="UNKNOWN"
    canonical_stock_ready:bool=False

def commercial_conversion_stage(e:ConversionProjection)->ConversionStage:
    """Project maturity without overriding canonical #103 gates."""
    if e.unresolved_contradiction or not e.company_identity:
        return ConversionStage.DISCOVERED
    if not (e.product_application and e.independent_sources>=2):
        return ConversionStage.EVIDENCED
    if not (e.buyer_role and e.procurement_signal):
        return ConversionStage.EVIDENCED
    if not e.canonical_conversion_ready:
        return ConversionStage.BUYER_VERIFIED
    if not e.decision_maker:
        return ConversionStage.BUYER_VERIFIED
    if not e.verified_contact:
        return ConversionStage.DECISION_MAKER_VERIFIED
    if e.canonical_sales_readiness!="READY" or not e.canonical_stock_ready:
        return ConversionStage.CONTACT_VERIFIED
    return ConversionStage.OUTREACH_READY
