"""Persistent NEXUS continuous-cycle state machine. No protected action execution."""
from dataclasses import dataclass
from enum import Enum

class CycleState(str,Enum):
 RECOVER="RECOVER"; RESEARCH="RESEARCH"; RESOLVE="RESOLVE"; VERIFY="VERIFY"; BUILD="BUILD"; TEST="TEST"; RECORD="RECORD"; MEASURE="MEASURE"; LEARN="LEARN"; CHECKPOINT="CHECKPOINT"; GATED="GATED"; BLOCKED="BLOCKED"

@dataclass(frozen=True)
class CycleContext:
 project_id:str; repo_head:str; ci_head:str; ci_state:str
 checkpoint_fresh:bool; evidence_ready:bool=False; defect_found:bool=False
 protected_action:bool=False; blocker:bool=False

def next_cycle_state(c:CycleContext)->CycleState:
 if not c.project_id or not c.repo_head: return CycleState.RECOVER
 if c.blocker: return CycleState.BLOCKED
 if c.ci_state!="GREEN" or c.ci_head!=c.repo_head or not c.checkpoint_fresh: return CycleState.RECOVER
 if c.protected_action: return CycleState.GATED
 if not c.evidence_ready: return CycleState.RESEARCH
 if c.defect_found: return CycleState.BUILD
 return CycleState.MEASURE

SAFE_LOOP=(CycleState.RECOVER,CycleState.RESEARCH,CycleState.RESOLVE,CycleState.VERIFY,CycleState.BUILD,CycleState.TEST,CycleState.RECORD,CycleState.MEASURE,CycleState.LEARN,CycleState.CHECKPOINT)

def may_auto_continue(state:CycleState)->bool:
 return state in SAFE_LOOP and state not in {CycleState.GATED,CycleState.BLOCKED}
