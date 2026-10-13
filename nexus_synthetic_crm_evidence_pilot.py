"""Offline, dependency-free NEXUS CRM pilot with explicit project boundaries.

No live CRM, network calls, credentials or production mutations.
"""
from dataclasses import dataclass
from hashlib import sha256
import json


@dataclass(frozen=True)
class SyntheticOpportunity:
    project_id: str
    account_id: str
    contact_id: str
    opportunity_id: str


class ProjectBoundaryError(ValueError):
    pass


def synthetic_pilot(records, *, project_id: str) -> dict:
    if not isinstance(project_id, str) or not project_id.strip():
        raise ValueError("invalid_project_id")
    seen = set()
    output = []
    for record in records:
        if not isinstance(record, SyntheticOpportunity):
            raise ValueError("invalid_record")
        if any(not isinstance(value, str) or not value.strip() for value in (
            record.project_id, record.account_id, record.contact_id, record.opportunity_id
        )):
            raise ValueError("invalid_record_id")
        if record.project_id != project_id:
            raise ProjectBoundaryError("cross_project_record_blocked")
        key = (record.project_id, record.opportunity_id)
        if key in seen:
            raise ValueError("duplicate_opportunity_blocked")
        seen.add(key)
        output.append({
            "project_id": record.project_id,
            "account_id": record.account_id,
            "contact_id": record.contact_id,
            "opportunity_id": record.opportunity_id,
            "live_write_authorized": False,
        })
    serialized = json.dumps(output, sort_keys=True, separators=(",", ":"))
    return {
        "mode": "synthetic_offline_only",
        "project_id": project_id,
        "records": output,
        "record_count": len(output),
        "evidence_sha256": sha256(serialized.encode("utf-8")).hexdigest(),
        "external_crm_installed": False,
        "live_write_authorized": False,
    }
