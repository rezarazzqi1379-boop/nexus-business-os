import pytest
from nexus_crm_schema_probe import SyntheticCRMRecord, map_synthetic_record

def record(**kw):
    d=dict(project_id="SANDBOX",account_id="A",contact_id="C",opportunity_id="O")
    d.update(kw)
    return SyntheticCRMRecord(**d)

@pytest.mark.parametrize("target",["twenty","espocrm"])
def test_synthetic_mapping_is_research_only(target):
    x=map_synthetic_record(record(),target=target,expected_project_id="SANDBOX")
    assert x["target"]==target and x["opportunity"]["stage"]=="RESEARCH_ONLY"
    assert x["live_write_authorized"] is False

def test_cross_project_is_rejected():
    with pytest.raises(ValueError,match="cross_project_record"):
        map_synthetic_record(record(project_id="OTHER"),target="twenty",expected_project_id="SANDBOX")

def test_unknown_target_is_rejected():
    with pytest.raises(ValueError,match="unsupported_crm"):
        map_synthetic_record(record(),target="unknown",expected_project_id="SANDBOX")

def test_missing_entity_is_rejected():
    with pytest.raises(ValueError,match="missing_entity"):
        map_synthetic_record(record(contact_id=" "),target="espocrm",expected_project_id="SANDBOX")

def test_synthetic_record_cannot_claim_verified_demand():
    with pytest.raises(ValueError,match="synthetic_verification_not_allowed"):
        map_synthetic_record(record(demand_verified=True),target="twenty",expected_project_id="SANDBOX")

def test_synthetic_record_cannot_claim_verified_authority():
    with pytest.raises(ValueError,match="synthetic_verification_not_allowed"):
        map_synthetic_record(record(authority_verified=True),target="espocrm",expected_project_id="SANDBOX")
