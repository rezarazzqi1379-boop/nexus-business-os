"""Durable cross-chat intelligence state with project isolation and provenance."""
from dataclasses import dataclass
from enum import Enum

class RecordKind(str,Enum):
 ENTITY="ENTITY"; RELATION="RELATION"; EVENT="EVENT"; PERSON_ROLE="PERSON_ROLE"; SOURCE="SOURCE"; CHECKPOINT="CHECKPOINT"

class EvidenceState(str,Enum):
 VERIFIED="VERIFIED"; CLUE="CLUE"; HYPOTHESIS="HYPOTHESIS"; SUPERSEDED="SUPERSEDED"

@dataclass(frozen=True)
class DurableRecord:
 record_id:str
 project_id:str
 kind:RecordKind
 subject_id:str
 predicate:str
 object_value:str
 evidence_state:EvidenceState
 source_ref:str
 observed_at:str
 valid_from:str=""
 valid_to:str=""
 supersedes:str=""
 origin_id:str=""

def admissible(r:DurableRecord)->bool:
 if not all((r.record_id,r.project_id,r.subject_id,r.predicate,r.object_value,r.observed_at)):
  return False
 if r.evidence_state==EvidenceState.VERIFIED and not r.source_ref:
  return False
 return True

def recover(records:tuple[DurableRecord,...],project_id:str)->tuple[DurableRecord,...]:
 return tuple(r for r in records if r.project_id==project_id and admissible(r))

def independent_origins(records:tuple[DurableRecord,...])->int:
 return len({r.origin_id or r.source_ref for r in records if admissible(r) and (r.origin_id or r.source_ref)})

def current_verified(records:tuple[DurableRecord,...],project_id:str,subject_id:str,predicate:str)->tuple[DurableRecord,...]:
 superseded={r.supersedes for r in records if r.project_id==project_id and r.supersedes}
 return tuple(r for r in records if r.project_id==project_id and r.subject_id==subject_id and r.predicate==predicate and r.evidence_state==EvidenceState.VERIFIED and r.record_id not in superseded and admissible(r))

def cross_chat_capsule(records:tuple[DurableRecord,...],project_id:str)->dict:
 scoped=recover(records,project_id)
 return {
  "project_id":project_id,
  "record_ids":tuple(r.record_id for r in scoped),
  "verified":sum(r.evidence_state==EvidenceState.VERIFIED for r in scoped),
  "clues":sum(r.evidence_state==EvidenceState.CLUE for r in scoped),
  "hypotheses":sum(r.evidence_state==EvidenceState.HYPOTHESIS for r in scoped),
  "independent_origins":independent_origins(scoped),
 }
