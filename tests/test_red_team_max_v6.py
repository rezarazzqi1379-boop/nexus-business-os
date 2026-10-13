import pytest
from red_team_max_v6 import ATTACKS,AttackResult,audit

def test_documentation_cannot_make_attack_pass_without_evidence():
 with pytest.raises(ValueError,match="conclusive_attack_requires_evidence"):
  AttackResult("CONTRACT_CODE","PASS").validate()

def test_not_run_is_explicitly_unresolved():
 r=audit((AttackResult("ROLE","NOT_RUN"),))
 assert "ROLE" in r["unresolved"] and not r["complete"]

def test_provider_failure_cannot_disappear_from_audit():
 xs=[AttackResult(a,"PASS",("ci:1",)) for a in ATTACKS]
 xs[ATTACKS.index("PROVIDER")]=AttackResult("PROVIDER","FAIL",("failure:provider",),"provider unavailable")
 r=audit(xs)
 assert r["failed"]==("PROVIDER",) and r["complete"]

def test_missing_attack_family_blocks_completion():
 xs=[AttackResult(a,"PASS",("ci:1",)) for a in ATTACKS if a!="COMMERCIAL_OUTCOME"]
 r=audit(xs)
 assert "COMMERCIAL_OUTCOME" in r["missing"] and not r["complete"]
