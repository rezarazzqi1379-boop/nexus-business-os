"""Durable cross-chat intelligence state with project isolation, provenance and temporal validity."""
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlsplit

class RecordKind(str,Enum):
 ENTITY="ENTITY"; RELATION="RELATION"; EVENT="EVENT"; PERSON_ROLE="PERSON_ROLE"; SOURCE="SOURCE"; CHECKPOINT="CHECKPOINT"
class EvidenceState(str,Enum):
 VERIFIED="VERIFIED"; CLUE="CLUE"; HYPOTHESIS="HYPOTHESIS"; SUPERSEDED="SUPERSEDED"

@dataclass(frozen=True)
class DurableRecord:
 record_id:str; project_id:str; kind:RecordKind; subject_id:str; predicate:str; object_value:str
 evidence_state:EvidenceState; source_ref:str; observed_at:str
 valid_from:str=""; valid_to:str=""; supersedes:str=""; origin_id:str=""

@dataclass(frozen=True)
class CheckpointBinding:
 project_id:str; repo_head:str; ci_head:str; ci_run:str; ci_state:str; decision_version:str

def admissible(r:DurableRecord)->bool:
 if not all((r.record_id,r.project_id,r.subject_id,r.predicate,r.object_value,r.observed_at)): return False
 if r.evidence_state==EvidenceState.VERIFIED and not r.source_ref: return False
 if r.valid_from and r.valid_to and r.valid_from>r.valid_to: return False
 return True

def recover(records:tuple[DurableRecord,...],project_id:str)->tuple[DurableRecord,...]:
 return tuple(r for r in records if r.project_id==project_id and admissible(r))

def canonical_origin(r:DurableRecord)->str:
 if r.origin_id:return r.origin_id.strip().lower()
 s=r.source_ref.strip().lower()
 if "://" in s:
  host=urlsplit(s).hostname or s
  return host.removeprefix("www.")
 return s

def independent_origins(records:tuple[DurableRecord,...])->int:
 return len({canonical_origin(r) for r in records if admissible(r) and canonical_origin(r)})

def active_at(r:DurableRecord,as_of:str)->bool:
 if not admissible(r):return False
 if r.valid_from and as_of<r.valid_from:return False
 if r.valid_to and as_of>r.valid_to:return False
 return True

def current_verified(records:tuple[DurableRecord,...],project_id:str,subject_id:str,predicate:str,as_of:str)->tuple[DurableRecord,...]:
 superseded={r.supersedes for r in records if r.project_id==project_id and r.supersedes}
 return tuple(r for r in records if r.project_id==project_id and r.subject_id==subject_id and r.predicate==predicate and r.evidence_state==EvidenceState.VERIFIED and r.record_id not in superseded and active_at(r,as_of))

def checkpoint_valid(c:CheckpointBinding)->bool:
 return bool(c.project_id and c.repo_head and c.ci_head and c.ci_run and c.decision_version and c.ci_state=="SUCCESS" and c.repo_head==c.ci_head)

def cross_chat_capsule(records:tuple[DurableRecord,...],project_id:str,checkpoint:CheckpointBinding|None=None)->dict:
 scoped=recover(records,project_id)
 return {
  "project_id":project_id,
  "record_ids":tuple(r.record_id for r in scoped),
  "verified":sum(r.evidence_state==EvidenceState.VERIFIED for r in scoped),
  "clues":sum(r.evidence_state==EvidenceState.CLUE for r in scoped),
  "hypotheses":sum(r.evidence_state==EvidenceState.HYPOTHESIS for r in scoped),
  "independent_origins":independent_origins(scoped),
  "checkpoint_bound":bool(checkpoint and checkpoint.project_id==project_id and checkpoint_valid(checkpoint)),
 }
