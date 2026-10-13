"""Governed registry for external agents/tools considered by NEXUS v8."""
from dataclasses import dataclass

LIFECYCLE=("DISCOVERED","LICENSE_CHECKED","SECURITY_REVIEWED","PRIVACY_TOS_REVIEWED","SANDBOXED","BENCHMARKED","EXPERIMENT_ONLY","APPROVED_ADAPTER","ACTIVE")
INTEGRATION_PREF=("ADAPTER","INTERFACE","PATTERN_ADAPTATION","FORK","COPY")

@dataclass(frozen=True)
class AgentCandidate:
 name:str; repository:str; capability:str; nexus_job:str
 state:str="DISCOVERED"; integration_method:str="ADAPTER"
 license:str="UNKNOWN"; maintenance:str="UNKNOWN"; security_notes:str=""; privacy_tos_notes:str=""
 network_credentials:str="UNKNOWN"; expected_gain:str=""; complexity_cost:str="UNKNOWN"; rollback:str=""; acceptance_test:str=""
 def validate(self)->tuple[str,...]:
  e=[]
  if not all(x.strip() for x in (self.name,self.repository,self.capability,self.nexus_job)):e.append("identity_required")
  if self.state not in LIFECYCLE:e.append("invalid_state")
  if self.integration_method not in INTEGRATION_PREF:e.append("invalid_integration_method")
  if LIFECYCLE.index(self.state)>=LIFECYCLE.index("LICENSE_CHECKED") and self.license=="UNKNOWN":e.append("license_required")
  if LIFECYCLE.index(self.state)>=LIFECYCLE.index("SANDBOXED") and (not self.rollback.strip() or not self.acceptance_test.strip()):e.append("sandbox_requires_rollback_and_acceptance_test")
  return tuple(e)

def can_activate(x:AgentCandidate)->bool:
 return not x.validate() and x.state=="ACTIVE" and all(v!="UNKNOWN" for v in (x.license,x.maintenance,x.network_credentials))
