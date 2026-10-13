"""Offline CRM pilot: validate NEXUS schema probe without contacting any CRM."""
from nexus_crm_schema_probe import SyntheticCRMRecord, map_synthetic_record

def run_offline_crm_pilot() -> dict:
    fixture = SyntheticCRMRecord(
        project_id="SANDBOX", account_id="SANDBOX_STEEL_BUYER_A",
        contact_id="SANDBOX_CONTACT_A", opportunity_id="SANDBOX_OPP_A")
    outputs = {
        target: map_synthetic_record(fixture, target=target, expected_project_id="SANDBOX")
        for target in ("twenty", "espocrm")
    }
    if outputs["twenty"]["project_id"] != outputs["espocrm"]["project_id"]:
        raise AssertionError("project_mismatch")
    if any(output["live_write_authorized"] for output in outputs.values()):
        raise AssertionError("live_write_authorized")
    if any(output["opportunity"]["stage"] != "RESEARCH_ONLY" for output in outputs.values()):
        raise AssertionError("unsafe_stage")
    return {
        "status": "OFFLINE_SCHEMA_PROBE_ONLY",
        "targets": tuple(outputs),
        "synthetic_records": len(outputs),
        "external_api_calls": 0,
        "installation_verified": False,
        "api_compatibility_verified": False,
        "outputs": outputs,
    }
