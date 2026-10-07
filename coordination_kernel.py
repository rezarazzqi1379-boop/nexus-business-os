"""NEXUS coordination kernel: authority-aware state across projects, sessions and agents."""
from dataclasses import dataclass
from enum import Enum

class StateScope(str,Enum):
 CANONICAL="CANONICAL"; SHARED="SHARED"; SESSION="SESSION"; EPHEMERAL="EPHEMERAL"

@dataclass(frozen=True)
class CoordinationState:
 project_id:str; source_registry_version:str; master_id:str; master_version:str
 repo_head:str; ci_head:str; ci_state:str; decision_version:str
 scope:StateScope=StateScope.SESSION; blocker:str=""

@dataclass(frozen=True)
class HandoffCapsule:
 project_id:str; objective:str; last_verified_head:str; ci_run:str
 evidence_refs:tuple[str,...]; decisions:tuple[str,...]; unknowns:tuple[str,...]
 next_safe_action:str; protected_action:bool=False

def recoverable(s:CoordinationState)->bool:
 return bool(s.project_id and s.source_registry_version and s.master_id and s.master_version and s.repo_head)

def direction_guard(s:CoordinationState,target_project_id:str,proposed_decision_version:str)->tuple[bool,str]:
 if not recoverable(s): return False,"RECOVER_AUTHORITY"
 if target_project_id!=s.project_id: return False,"PROJECT_ISOLATION"
 if s.ci_state!="GREEN" or s.ci_head!=s.repo_head: return False,"REFRESH_EXACT_HEAD_CI"
 if s.blocker: return False,"BLOCKED"
 if proposed_decision_version!=s.decision_version: return False,"PIVOT_RECONCILIATION_REQUIRED"
 return True,"ALIGNED"

def validate_handoff(c:HandoffCapsule,s:CoordinationState)->tuple[bool,str]:
 if c.project_id!=s.project_id: return False,"PROJECT_ISOLATION"
 if c.last_verified_head!=s.repo_head or s.ci_head!=s.repo_head or s.ci_state!="GREEN":
  return False,"STALE_HANDOFF"
 if not c.evidence_refs: return False,"MISSING_EVIDENCE"
 if c.protected_action: return False,"ACTION_GATE"
 return True,"RESUMABLE"

def memory_may_authorize(scope:StateScope)->bool:
 """Only canonical governed state can be authority; chat/session memory cannot."""
 return scope==StateScope.CANONICAL
