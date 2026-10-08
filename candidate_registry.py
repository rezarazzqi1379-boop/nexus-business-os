"""Governed lifecycle registry for externally discovered capability patterns."""
from dataclasses import dataclass
from enum import Enum

class CandidateState(str,Enum):
 DISCOVERED="DISCOVERED"; STUDIED="STUDIED"; SANDBOXED="SANDBOXED"; ABLATED="ABLATED"; ADMITTED="ADMITTED"; REJECTED="REJECTED"

@dataclass(frozen=True)
class CandidateRecord:
 candidate_id:str
 source_repo:str
 state:CandidateState
 evidence_refs:tuple[str,...]=()
 acceptance_tests:tuple[str,...]=()
 sandbox_passed:bool=False
 ablation_win:bool=False
 protected_runtime:bool=False

def next_candidate_state(c:CandidateRecord)->CandidateState:
 if not c.candidate_id or not c.source_repo:return CandidateState.REJECTED
 if c.state is CandidateState.DISCOVERED:
  return CandidateState.STUDIED if c.evidence_refs else CandidateState.DISCOVERED
 if c.state is CandidateState.STUDIED:
  return CandidateState.SANDBOXED if c.acceptance_tests else CandidateState.STUDIED
 if c.state is CandidateState.SANDBOXED:
  return CandidateState.ABLATED if c.sandbox_passed else CandidateState.REJECTED
 if c.state is CandidateState.ABLATED:
  if c.protected_runtime:return CandidateState.ABLATED
  return CandidateState.ADMITTED if c.ablation_win else CandidateState.REJECTED
 return c.state
