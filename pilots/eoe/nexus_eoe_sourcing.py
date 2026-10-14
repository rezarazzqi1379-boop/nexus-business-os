"""Deterministic, side-effect-free EOE sourcing evidence gates (pilot)."""
from typing import Mapping

REQUIRED = ("project_id", "source_locator", "evidence_category", "listing_status", "quote_status", "capacity_basis")
CATEGORIES = {"FACT", "MEASUREMENT", "CLAIM", "ESTIMATE", "ASSUMPTION", "HYPOTHESIS", "UNKNOWN"}
LISTING = {"ACTIVE_VERIFIED", "ADVERTISED_UNVERIFIED", "SOLD", "UNKNOWN"}
QUOTE = {"FORMAL_QUOTE", "PUBLIC_ADVERTISED_PRICE", "NO_PRICE"}
CAPACITY = {"TOTAL", "PER_LANE", "UNKNOWN"}

def validate_supplier(record: Mapping) -> list[str]:
    errors = [f"missing:{k}" for k in REQUIRED if not record.get(k)]
    for field, allowed in (("evidence_category", CATEGORIES), ("listing_status", LISTING), ("quote_status", QUOTE), ("capacity_basis", CAPACITY)):
        if record.get(field) and record[field] not in allowed:
            errors.append(f"invalid:{field}")
    if record.get("project_id") != "PRJ-EOE-PILOT-01":
        errors.append("project_isolation")
    if record.get("listing_status") == "SOLD" and record.get("available") is True:
        errors.append("sold_not_available")
    if record.get("quote_status") == "PUBLIC_ADVERTISED_PRICE" and record.get("formal_quote") is True:
        errors.append("advertisement_not_formal_quote")
    if record.get("capacity_basis") == "UNKNOWN" and record.get("capacity_pass") is True:
        errors.append("capacity_unverified")
    return errors

def outreach_allowed(approval: Mapping) -> bool:
    required = ("recipient", "subject", "payload", "attachments", "persian_explanation", "latest_thread_checked", "duplicate_checked", "exact_approval")
    return all(k in approval and approval[k] is not None for k in required) and all(
        bool(approval[k]) for k in ("recipient", "subject", "payload", "persian_explanation", "latest_thread_checked", "duplicate_checked", "exact_approval")
    )
