"""Immutable procurement event-chain schema inspired by OCDS lifecycle semantics."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class ProcurementStage(str,Enum):
 PLANNING="PLANNING"; PREQUALIFICATION="PREQUALIFICATION"; TENDER="TENDER"; AWARD="AWARD"; CONTRACT="CONTRACT"; IMPLEMENTATION="IMPLEMENTATION"; CANCELLATION="CANCELLATION"

@dataclass(frozen=True)
class ProcurementEvent:
 process_id:str; event_id:str; project_id:str; buyer_id:str; stage:ProcurementStage
 source_locator:str; observed_at:datetime; event_at:datetime
 supplier_id:str=""; supersedes_event_id:str=""; current:bool=True

def valid_event(e:ProcurementEvent)->bool:
 return bool(e.process_id and e.event_id and e.project_id and e.buyer_id and e.source_locator)

def append_event(history:tuple[ProcurementEvent,...],event:ProcurementEvent)->tuple[ProcurementEvent,...]:
 if not valid_event(event): raise ValueError("invalid_procurement_event")
 if any(x.event_id==event.event_id for x in history): raise ValueError("immutable_event_id")
 if event.supersedes_event_id and not any(x.event_id==event.supersedes_event_id and x.process_id==event.process_id for x in history):
  raise ValueError("missing_superseded_event")
 if any(x.project_id!=event.project_id for x in history if x.process_id==event.process_id):
  raise ValueError("cross_project_process")
 return history+(event,)

def stage_progression(history:tuple[ProcurementEvent,...],process_id:str)->tuple[ProcurementStage,...]:
 return tuple(e.stage for e in sorted((x for x in history if x.process_id==process_id),key=lambda x:(x.event_at,x.observed_at)))

def supplier_change(history:tuple[ProcurementEvent,...],process_id:str)->bool:
 suppliers=[e.supplier_id for e in history if e.process_id==process_id and e.stage in {ProcurementStage.AWARD,ProcurementStage.CONTRACT} and e.supplier_id]
 return len(set(suppliers))>1
