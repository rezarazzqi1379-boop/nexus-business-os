"""Quarantine gate for external agent/tool candidates."""
from dataclasses import dataclass
@dataclass(frozen=True)
class CandidateRisk:
 candidate_id:str; arbitrary_code:bool=False; host_write:bool=False; credential_access:bool=False
 unrestricted_network:bool=False; persistence:bool=False; browser_write:bool=False
 security_bypass:bool=False; access_control_bypass:bool=False; sanctions_evasion:bool=False
def disposition(r:CandidateRisk)->str:
 if r.security_bypass or r.access_control_bypass or r.sanctions_evasion:return "REJECT_UNSAFE_CAPABILITY"
 if any((r.arbitrary_code,r.host_write,r.credential_access,r.unrestricted_network,r.persistence,r.browser_write)):return "QUARANTINE_SANDBOX_ONLY"
 return "READ_ONLY_SANDBOX"
def may_run_on_host(r:CandidateRisk)->bool:return False
