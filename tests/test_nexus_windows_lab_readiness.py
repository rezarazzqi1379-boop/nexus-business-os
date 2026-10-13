import pytest
from nexus_windows_lab_readiness import WindowsLabReadiness, readiness_errors

def test_default_is_not_ready():
    assert len(readiness_errors(WindowsLabReadiness())) == 10

def test_all_confirmed_has_no_errors():
    assert readiness_errors(WindowsLabReadiness(*([True] * 10))) == ()

@pytest.mark.parametrize("index",range(10))
def test_each_missing_requirement_blocks(index):
    values = [True] * 10
    values[index] = False
    assert len(readiness_errors(WindowsLabReadiness(*values))) == 1

def test_non_boolean_attestation_rejected():
    values = [True] * 10
    values[0] = "true"
    assert readiness_errors(WindowsLabReadiness(*values)) == ("invalid_readiness_evidence",)
