import pytest
from state_drift_audit import DecisionAutopsy,VOLATILE_FIELDS,audit_state,supersession_record

def test_state_drift_distinguishes_unknown_stale_and_change():
 assert audit_state(stored="A",observed=None,field="stock")=="UNKNOWN"
 assert audit_state(stored="A",observed="A",field="stock",stale=True)=="STALE"
 assert audit_state(stored="A",observed="B",field="stock")=="DRIFTED"

def test_contradiction_has_priority():
 assert audit_state(stored=True,observed=True,field="capability",stale=True,contradicted=True)=="CONTRADICTED"

def test_historical_decision_is_preserved_and_superseded():
 a=DecisionAutopsy("d1","Supplier has stock",("old:1",),"2026-01-01",("new:1",),contradicted=True)
 r=supersession_record(a,"Current stock is not verified")
 assert r["supersedes"]=="d1" and r["original_claim"]=="Supplier has stock"
 assert r["reason"]=="CONTRADICTED"

def test_no_silent_supersession_without_trigger():
 a=DecisionAutopsy("d1","claim",("e1",),"2026-01-01",("e2",))
 with pytest.raises(ValueError,match="supersession_not_required"):
  supersession_record(a,"replacement")

def test_failure_becomes_regression_candidate():
 a=DecisionAutopsy("d2","buyer","e1".split(),"2026-01-01",failure_mode="ROLE_MISCLASSIFICATION")
 assert a.regression_candidate


def test_commercial_relationship_fields_are_volatile():
 for field in ("procurement_status","award_winner","decision_authority","sales_readiness","relationship_state"):
  assert field in VOLATILE_FIELDS
