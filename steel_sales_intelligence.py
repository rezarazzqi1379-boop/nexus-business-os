"""Governed registry and gates for NEXUS steel sales intelligence.

Pure/local by design: no network calls, no credentials and no external writes.
Live providers remain behind the existing NEXUS approval and connector control plane.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Literal

ProviderState = Literal["ACTIVE_CONNECTOR", "ACTIVE_LOCAL", "EXPERIMENT_ONLY", "BLOCKED"]

@dataclass(frozen=True)
class SalesProvider:
    provider_id: str
    capabilities: tuple[str, ...]
    state: ProviderState
    paid: bool = False
    external_write: bool = False
    note: str = ""

PROVIDERS = (
    SalesProvider("web-live", ("company_discovery","company_research","competitor_intelligence"), "ACTIVE_CONNECTOR"),
    SalesProvider("apollo-free-org", ("organization_resolution",), "ACTIVE_CONNECTOR"),
    SalesProvider("apollo-enrichment", ("organization_enrichment","contact_enrichment"), "ACTIVE_CONNECTOR", paid=True),
    SalesProvider("github-public", ("agent_discovery","implementation_research"), "ACTIVE_CONNECTOR"),
    SalesProvider("un-comtrade-adapter", ("trade_intelligence",), "EXPERIMENT_ONLY"),
    SalesProvider("external-sales-agent-repos", ("company_research","lead_scoring","outreach_patterns"), "EXPERIMENT_ONLY",
                  note="sandbox/review before adoption; never auto-install"),
)

@dataclass(frozen=True)
class LeadGate:
    discovery_allowed: bool
    paid_enrichment_allowed: bool
    outreach_allowed: bool
    blockers: tuple[str, ...]

def evaluate_lead(*, evidence_count: int, material_fit: bool, named_company: bool,
                  spend_approved: bool = False, outreach_approved: bool = False,
                  compliance_required: bool = False, compliance_cleared: bool = False) -> LeadGate:
    blockers: list[str] = []
    discovery = named_company and evidence_count > 0
    if not named_company:
        blockers.append("named_company_required")
    if evidence_count <= 0:
        blockers.append("evidence_required")
    if not material_fit:
        blockers.append("material_fit_unverified")
    paid = discovery and material_fit and spend_approved
    if discovery and material_fit and not spend_approved:
        blockers.append("paid_enrichment_requires_exact_scope_approval")
    compliance_ok = (not compliance_required) or compliance_cleared
    if compliance_required and not compliance_cleared:
        blockers.append("compliance_clearance_required")
    outreach = discovery and material_fit and compliance_ok and outreach_approved
    if discovery and material_fit and compliance_ok and not outreach_approved:
        blockers.append("outreach_requires_exact_scope_approval")
    return LeadGate(discovery, paid, outreach, tuple(dict.fromkeys(blockers)))

def provider_payload() -> dict:
    return {"schema_version":"nexus.steel-sales-providers.v1",
            "providers":[asdict(item) for item in PROVIDERS]}
