"""Offline, synthetic-only CRM export schema comparison.

This module does not connect to Twenty, EspoCRM or any live CRM.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class SyntheticCRMRecord:
    project_id: str
    account_id: str
    contact_id: str
    opportunity_id: str
    demand_verified: bool = False
    authority_verified: bool = False

def map_synthetic_record(record: SyntheticCRMRecord, *, target: str,
                         expected_project_id: str) -> dict:
    if target not in {"twenty", "espocrm"}:
        raise ValueError("unsupported_crm")
    if not expected_project_id or record.project_id != expected_project_id:
        raise ValueError("cross_project_record")
    if not all((record.account_id.strip(), record.contact_id.strip(), record.opportunity_id.strip())):
        raise ValueError("missing_entity")
    if record.demand_verified or record.authority_verified:
        raise ValueError("synthetic_verification_not_allowed")
    return {"target": target, "project_id": record.project_id,
            "account": {"externalId": record.account_id},
            "contact": {"externalId": record.contact_id},
            "opportunity": {"externalId": record.opportunity_id, "stage": "RESEARCH_ONLY"},
            "live_write_authorized": False}
