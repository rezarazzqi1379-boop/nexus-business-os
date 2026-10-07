"""Cross-session NEXUS continuity contract."""
from dataclasses import dataclass
from enum import Enum

class ContinuityState(str,Enum):
 INVALID="INVALID"; RECOVERABLE="RECOVERABLE"; CONTINUABLE="CONTINUABLE"; GATED="GATED"

@dataclass(frozen=True)
class ProjectCheckpoint:
 project_id:str
 source_registry_ref:str
 master_ref:str
 repo_head:str
 ci_state:str
 stage:str
 maturity:str
 evidence_refs:tuple[str,...]
 blockers:tuple[str,...]
 next_safe_action:str
 protected_action:bool=False

def validate_checkpoint(c:ProjectCheckpoint)->ContinuityState:
 required=(c.project_id,c.source_registry_ref,c.master_ref,c.repo_head,c.ci_state,c.stage,c.maturity,c.next_safe_action)
 if not all(required) or not c.evidence_refs:
  return ContinuityState.INVALID
 if c.ci_state!="GREEN":
  return ContinuityState.RECOVERABLE
 if c.protected_action:
  return ContinuityState.GATED
 return ContinuityState.CONTINUABLE

def recovery_order()->tuple[str,...]:
 return ("SOURCE_REGISTRY","CANONICAL_MASTER","PROJECT_CHECKPOINT","REPO_HEAD","LIVE_CI","EVIDENCE_READBACK","BLOCKER","NEXT_SAFE_ACTION")

def may_continue_without_user_repetition(c:ProjectCheckpoint)->bool:
 return validate_checkpoint(c)==ContinuityState.CONTINUABLE
