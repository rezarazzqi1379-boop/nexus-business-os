"""Offline, synthetic-only CRM export schema comparison.

This is an internal normalized payload, not a vendor API schema.
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

def _identifier(value: str) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()

def map_synthetic_record(record: SyntheticCRMRecord, *, target: str,
                         expected_project_id: str) -> dict:
    if target not in {"twenty", "espocrm"}:
        raise ValueError("unsupported_crm")
    if not _identifier(expected_project_id) or not _identifier(record.project_id) or record.project_id != expected_project_id:
        raise ValueError("cross_project_record")
    if not all(_identifier(x) for x in (record.account_id, record.contact_id, record.opportunity_id)):
        raise ValueError("missing_entity")
    if type(record.demand_verified) is not bool or type(record.authority_verified) is not bool:
        raise ValueError("invalid_verification_flag")
    if record.demand_verified or record.authority_verified:
        raise ValueError("synthetic_verification_not_allowed")
    return {"target": target, "project_id": record.project_id,
            "account": {"externalId": record.account_id},
            "contact": {"externalId": record.contact_id},
            "opportunity": {"externalId": record.opportunity_id, "stage": "RESEARCH_ONLY"},
            "live_write_authorized": False}
