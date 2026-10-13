"""Read-only, deterministic health checks for the NEXUS synthetic lab.

No network calls, credentials, filesystem writes or live CRM operations.
"""
from dataclasses import dataclass
from nexus_windows_lab_readiness import WindowsLabReadiness, readiness_errors

@dataclass(frozen=True)
class LabHealth:
    synthetic_mapping_passed: bool
    fail_closed_readiness_passed: bool
    local_install_verified: bool = False
    persistent_service_verified: bool = False

def evaluate_lab_health(state: LabHealth) -> dict:
    values = (state.synthetic_mapping_passed, state.fail_closed_readiness_passed,
              state.local_install_verified, state.persistent_service_verified)
    if any(type(v) is not bool for v in values):
        raise ValueError("invalid_health_evidence")
    return {
        "ci_checks_passed": state.synthetic_mapping_passed and state.fail_closed_readiness_passed,
        "local_install_verified": state.local_install_verified,
        "persistent_service_verified": state.persistent_service_verified,
        "production_ready": False,
    }

def self_test() -> dict:
    from nexus_crm_schema_probe import SyntheticCRMRecord, map_synthetic_record
    record = SyntheticCRMRecord(project_id="SANDBOX", account_id="A", contact_id="C", opportunity_id="O")
    payload = map_synthetic_record(record, target="twenty", expected_project_id="SANDBOX")
    synthetic_ok = payload["live_write_authorized"] is False and payload["project_id"] == "SANDBOX"
    blocked = len(readiness_errors(WindowsLabReadiness())) == 10
    return evaluate_lab_health(LabHealth(synthetic_ok, blocked))
