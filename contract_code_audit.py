"""Audit NEXUS contract requirements against evidenced capability maturity."""
from __future__ import annotations
from dataclasses import dataclass

MATURITY=("IDEA","DESIGNED","IMPLEMENTED","TESTED","BENCHMARKED","INTEGRATED","ACTIVE","PRODUCTION","DEPRECATED","SUPERSEDED")
AUDIT_STATES={"DESIGNED_ONLY","IMPLEMENTED","TESTED","BENCHMARKED","INTEGRATED","ACTIVE","MISSING","PARTIAL","DRIFTED","SUPERSEDED"}

@dataclass(frozen=True)
class CapabilityEvidence:
    capability_id:str
    documented:bool=True
    implementation_refs:tuple[str,...]=()
    test_refs:tuple[str,...]=()
    benchmark_refs:tuple[str,...]=()
    integration_refs:tuple[str,...]=()
    active_refs:tuple[str,...]=()
    superseded_by:str|None=None

def classify(x:CapabilityEvidence)->str:
    if x.superseded_by:return "SUPERSEDED"
    if not x.documented and not any((x.implementation_refs,x.test_refs,x.benchmark_refs,x.integration_refs,x.active_refs)):return "MISSING"
    if x.active_refs and not x.integration_refs:return "DRIFTED"
    if x.integration_refs and not x.test_refs:return "DRIFTED"
    if x.benchmark_refs and not x.test_refs:return "DRIFTED"
    if x.test_refs and not x.implementation_refs:return "DRIFTED"
    if x.active_refs:return "ACTIVE"
    if x.integration_refs:return "INTEGRATED"
    if x.benchmark_refs:return "BENCHMARKED"
    if x.test_refs:return "TESTED"
    if x.implementation_refs:return "IMPLEMENTED"
    if x.documented:return "DESIGNED_ONLY"
    return "PARTIAL"

def audit(items):
    rows=tuple((x.capability_id,classify(x)) for x in items)
    return {"results":rows,"gaps":tuple(k for k,s in rows if s in {"DESIGNED_ONLY","MISSING","PARTIAL","DRIFTED"})}
