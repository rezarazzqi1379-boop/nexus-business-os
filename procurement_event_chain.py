"""Procurement event chain v2: immutable, dual-time, typed changes and award semantics."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class ProcurementStage(str,Enum):
 PLANNING="PLANNING"; PREQUALIFICATION="PREQUALIFICATION"; TENDER="TENDER"; AWARD="AWARD"; CONTRACT="CONTRACT"; IMPLEMENTATION="IMPLEMENTATION"; CANCELLATION="CANCELLATION"
class ChangeType(str,Enum):
 CREATED="CREATED"; DEADLINE="DEADLINE"; DOCUMENT="DOCUMENT"; SPEC="SPEC"; QUANTITY="QUANTITY"; BIDDER="BIDDER"; AWARD="AWARD"; DELIVERY="DELIVERY"; CANCELLATION="CANCELLATION"; OTHER="OTHER"
class AwardState(str,Enum):
 NONE="NONE"; BIDDER_ONLY="BIDDER_ONLY"; WINNER_VERIFIED="WINNER_VERIFIED"; WINNER_HIDDEN="WINNER_HIDDEN"; SUPERSEDED="SUPERSEDED"

@dataclass(frozen=True)
class ProcurementEvent:
 process_id:str; event_id:str; project_id:str; buyer_id:str; stage:ProcurementStage
 source_locator:str; observed_at:datetime; event_at:datetime
 supplier_id:str=""; supersedes_event_id:str=""; current:bool=True
 valid_from:datetime|None=None; valid_to:datetime|None=None
 change_type:ChangeType=ChangeType.CREATED
 authority:str="UNKNOWN"; origin_id:str=""
 award_state:AwardState=AwardState.NONE
 bidder_ids:tuple[str,...]=()

def valid_event(e:ProcurementEvent)->bool:
 if not all((e.process_id,e.event_id,e.project_id,e.buyer_id,e.source_locator)): return False
 if e.valid_from and e.valid_to and e.valid_from>e.valid_to:return False
 if e.award_state==AwardState.WINNER_VERIFIED and (e.stage not in {ProcurementStage.AWARD,ProcurementStage.CONTRACT} or not e.supplier_id):return False
 return True

def append_event(history:tuple[ProcurementEvent,...],event:ProcurementEvent)->tuple[ProcurementEvent,...]:
 if not valid_event(event): raise ValueError("invalid_procurement_event")
 if any(x.event_id==event.event_id for x in history): raise ValueError("immutable_event_id")
 if event.supersedes_event_id and not any(x.event_id==event.supersedes_event_id and x.process_id==event.process_id for x in history): raise ValueError("missing_superseded_event")
 if any(x.project_id!=event.project_id for x in history if x.process_id==event.process_id): raise ValueError("cross_project_process")
 return history+(event,)

def stage_progression(history:tuple[ProcurementEvent,...],process_id:str)->tuple[ProcurementStage,...]:
 return tuple(e.stage for e in sorted((x for x in history if x.process_id==process_id),key=lambda x:(x.event_at,x.observed_at)))

def active_at(e:ProcurementEvent,as_of:datetime)->bool:
 if not valid_event(e) or not e.current:return False
 if e.valid_from and as_of<e.valid_from:return False
 if e.valid_to and as_of>e.valid_to:return False
 return True

def current_events(history:tuple[ProcurementEvent,...],process_id:str,as_of:datetime)->tuple[ProcurementEvent,...]:
 superseded={x.supersedes_event_id for x in history if x.process_id==process_id and x.supersedes_event_id}
 return tuple(x for x in history if x.process_id==process_id and x.event_id not in superseded and active_at(x,as_of))

def supplier_change(history:tuple[ProcurementEvent,...],process_id:str)->bool:
 suppliers=[e.supplier_id for e in history if e.process_id==process_id and e.stage in {ProcurementStage.AWARD,ProcurementStage.CONTRACT} and e.supplier_id and e.award_state==AwardState.WINNER_VERIFIED]
 return len(set(suppliers))>1

def verified_winners(history:tuple[ProcurementEvent,...],process_id:str)->tuple[str,...]:
 return tuple(dict.fromkeys(e.supplier_id for e in sorted(history,key=lambda x:(x.event_at,x.observed_at)) if e.process_id==process_id and e.award_state==AwardState.WINNER_VERIFIED and e.supplier_id))

def incumbent_supplier(history:tuple[ProcurementEvent,...],process_id:str)->str:
 winners=[e for e in history if e.process_id==process_id and e.award_state==AwardState.WINNER_VERIFIED and e.supplier_id]
 if not winners:return ""
 return max(winners,key=lambda x:(x.event_at,x.observed_at)).supplier_id
