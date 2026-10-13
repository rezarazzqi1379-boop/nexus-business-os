import pytest
from nexus_crm_schema_probe import SyntheticCRMRecord, map_synthetic_record

@pytest.mark.parametrize("field,value", [
    ("account_id", None), ("contact_id", 42), ("opportunity_id", ""),
    ("account_id", " A "), ("project_id", " SANDBOX "),
])
def test_invalid_identifier_fails_closed(field, value):
    data = dict(project_id="SANDBOX", account_id="A", contact_id="C", opportunity_id="O")
    data[field] = value
    with pytest.raises(ValueError):
        map_synthetic_record(SyntheticCRMRecord(**data), target="twenty", expected_project_id="SANDBOX")

@pytest.mark.parametrize("flag,value", [
    ("demand_verified", "false"), ("authority_verified", 0),
    ("demand_verified", None), ("authority_verified", 1),
])
def test_nonboolean_verification_flag_rejected(flag, value):
    data = dict(project_id="SANDBOX", account_id="A", contact_id="C", opportunity_id="O")
    data[flag] = value
    with pytest.raises(ValueError, match="invalid_verification_flag"):
        map_synthetic_record(SyntheticCRMRecord(**data), target="espocrm", expected_project_id="SANDBOX")

def test_invalid_expected_project_rejected():
    r = SyntheticCRMRecord(project_id="SANDBOX", account_id="A", contact_id="C", opportunity_id="O")
    with pytest.raises(ValueError, match="cross_project_record"):
        map_synthetic_record(r, target="twenty", expected_project_id=None)
