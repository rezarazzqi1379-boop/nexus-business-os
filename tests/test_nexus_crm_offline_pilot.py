from nexus_crm_offline_pilot import run_offline_crm_pilot

def test_offline_pilot_is_synthetic_and_does_not_authorize_writes():
    result = run_offline_crm_pilot()
    assert result["status"] == "OFFLINE_SCHEMA_PROBE_ONLY"
    assert result["targets"] == ("twenty", "espocrm")
    assert result["synthetic_records"] == 2
    assert result["external_api_calls"] == 0
    assert result["installation_verified"] is False
    assert result["api_compatibility_verified"] is False
    assert all(not x["live_write_authorized"] for x in result["outputs"].values())
    assert all(x["opportunity"]["stage"] == "RESEARCH_ONLY" for x in result["outputs"].values())
