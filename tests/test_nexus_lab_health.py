import pytest
from nexus_lab_health import LabHealth, evaluate_lab_health, self_test

def test_synthetic_self_test_passes_without_claiming_install():
    report = self_test()
    assert report["ci_checks_passed"] is True
    assert report["local_install_verified"] is False
    assert report["persistent_service_verified"] is False
    assert report["production_ready"] is False

def test_missing_synthetic_evidence_blocks_ci_health():
    assert evaluate_lab_health(LabHealth(False, True))["ci_checks_passed"] is False

def test_missing_readiness_evidence_blocks_ci_health():
    assert evaluate_lab_health(LabHealth(True, False))["ci_checks_passed"] is False

@pytest.mark.parametrize("value",["true", 1, None])
def test_invalid_attestation_rejected(value):
    with pytest.raises(ValueError, match="invalid_health_evidence"):
        evaluate_lab_health(LabHealth(value, True))

def test_even_positive_local_attestation_never_claims_production():
    assert evaluate_lab_health(LabHealth(True, True, True, True))["production_ready"] is False
