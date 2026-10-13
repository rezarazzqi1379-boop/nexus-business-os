"""Machine-readable Red Team Max v6 attack coverage."""
from dataclasses import dataclass

ATTACKS=("ROLE","PRODUCT","SOURCE","TIME","TRADE","PRICE","EQUIVALENCE","ENTITY","COVERAGE","CONTRADICTION","SCORING","EVIDENCE_BINDING","STATE_DRIFT","CONTRACT_CODE","BACKWARD_COMPATIBILITY","CHANGE_SET","COST","PROVIDER","COMPLIANCE","MEMORY","AUTOMATION","TEST_VALIDITY","ARCHITECTURE","COMMERCIAL_OUTCOME")
STATES={"PASS","FAIL","PARTIAL","NOT_RUN","BLOCKED"}

@dataclass(frozen=True)
class AttackResult:
 attack:str; state:str; evidence_refs:tuple[str,...]=(); finding:str=""
 def validate(self):
  if self.attack not in ATTACKS:raise ValueError("unknown_attack")
  if self.state not in STATES:raise ValueError("invalid_attack_state")
  if self.state in {"PASS","FAIL"} and not self.evidence_refs:raise ValueError("conclusive_attack_requires_evidence")

def audit(results):
 xs=tuple(results)
 for x in xs:x.validate()
 by={x.attack:x for x in xs}
 missing=tuple(a for a in ATTACKS if a not in by)
 failed=tuple(a for a,x in by.items() if x.state=="FAIL")
 unresolved=tuple(a for a in ATTACKS if a not in by or by[a].state in {"PARTIAL","NOT_RUN","BLOCKED"})
 return {"complete":not missing and not unresolved,"failed":failed,"unresolved":unresolved,"missing":missing}
