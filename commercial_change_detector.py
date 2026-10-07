"""Detect commercially meaningful changes across immutable procurement events."""
from dataclasses import dataclass
from enum import Enum
from procurement_event_chain import ProcurementEvent,ProcurementStage

class ChangeType(str,Enum):
 NEW_PROCESS="NEW_PROCESS"; STAGE_ADVANCE="STAGE_ADVANCE"; SUPPLIER_CHANGE="SUPPLIER_CHANGE"; CANCELLATION="CANCELLATION"; REVISION="REVISION"

@dataclass(frozen=True)
class CommercialChange:
 process_id:str; project_id:str; change_type:ChangeType; from_event_id:str; to_event_id:str; actionable:bool

def detect_change(previous:ProcurementEvent|None,current:ProcurementEvent)->CommercialChange:
 if previous is None:
  return CommercialChange(current.process_id,current.project_id,ChangeType.NEW_PROCESS,"",current.event_id,False)
 if previous.process_id!=current.process_id or previous.project_id!=current.project_id:
  raise ValueError("change_scope_mismatch")
 if current.stage==ProcurementStage.CANCELLATION:
  return CommercialChange(current.process_id,current.project_id,ChangeType.CANCELLATION,previous.event_id,current.event_id,False)
 if previous.supplier_id and current.supplier_id and previous.supplier_id!=current.supplier_id:
  return CommercialChange(current.process_id,current.project_id,ChangeType.SUPPLIER_CHANGE,previous.event_id,current.event_id,True)
 if current.stage!=previous.stage:
  return CommercialChange(current.process_id,current.project_id,ChangeType.STAGE_ADVANCE,previous.event_id,current.event_id,current.stage in {ProcurementStage.PREQUALIFICATION,ProcurementStage.TENDER})
 return CommercialChange(current.process_id,current.project_id,ChangeType.REVISION,previous.event_id,current.event_id,False)
