from nexus_activation_status import status_report
from nexus_windows_lab_readiness import WindowsLabReadiness

def test_unverified_machine_is_blocked():
    result = status_report()
    assert result["readiness"] == "BLOCKED"
    assert len(result["blockers"]) == 10
    assert not result["installed"]
    assert not result["production_enabled"]

def test_ready_for_review_is_not_installation():
    result = status_report(WindowsLabReadiness(*([True] * 10)))
    assert result["readiness"] == "READY_FOR_REVIEW"
    assert result["blockers"] == []
    assert not result["installed"]
    assert not result["service_running"]
    assert not result["crm_live_connected"]
