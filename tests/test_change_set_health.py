import pytest
from change_set_health import ChangeSet,assess

def test_large_pr_is_risk_signal_not_failure():
 r=assess(ChangeSet(commits=155,files_changed=85))
 assert r["risk"]=="HIGH"
 assert "very_large_commit_count" in r["reasons"]
 assert "very_large_file_surface" in r["reasons"]

def test_small_change_set_stays_low_risk():
 assert assess(ChangeSet(commits=3,files_changed=4))["risk"]=="LOW"

def test_schema_surface_increases_scrutiny_without_auto_failure():
 r=assess(ChangeSet(commits=20,files_changed=20,schemas_changed=1))
 assert r["risk"]=="LOW" and "schema_migration_surface" in r["reasons"]

def test_invalid_metrics_fail_closed():
 with pytest.raises(ValueError,match="invalid_change_set"):
  assess(ChangeSet(commits=-1,files_changed=2))
