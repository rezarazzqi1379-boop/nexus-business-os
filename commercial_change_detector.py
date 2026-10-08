"""Detect commercially meaningful procurement changes; never grants action authority."""
from dataclasses import dataclass
from enum import Enum
from procurement_event_chain import ProcurementEvent,ProcurementStage,ChangeType as EventChangeType,AwardState

class ChangeType(str,Enum):
 NEW_PROCESS="NEW_PROCESS"; STAGE_ADVANCE="STAGE_ADVANCE"; STAGE_REGRESSION="STAGE_REGRESSION"
 SUPPLIER_CHANGE="SUPPLIER_CHANGE"; CANCELLATION="CANCELLATION"
 DEADLINE="DEADLINE"; DOCUMENT="DOCUMENT"; SPEC="SPEC"; QUANTITY="QUANTITY"; BIDDER="BIDDER"; AWARD="AWARD"; DELIVERY="DELIVERY"; REVISION="REVISION"

_STAGE_ORDER={ProcurementStage.PLANNING:0,ProcurementStage.PREQUALIFICATION:1,ProcurementStage.TENDER:2,ProcurementStage.AWARD:3,ProcurementStage.CONTRACT:4,ProcurementStage.IMPLEMENTATION:5}
_TYPED={
 EventChangeType.DEADLINE:ChangeType.DEADLINE,EventChangeType.DOCUMENT:ChangeType.DOCUMENT,
 EventChangeType.SPEC:ChangeType.SPEC,EventChangeType.QUANTITY:ChangeType.QUANTITY,
 EventChangeType.BIDDER:ChangeType.BIDDER,EventChangeType.AWARD:ChangeType.AWARD,
 EventChangeType.DELIVERY:ChangeType.DELIVERY,
}

@dataclass(frozen=True)
class CommercialChange:
 process_id:str; project_id:str; change_type:ChangeType; from_event_id:str; to_event_id:str; commercial_review_signal:bool
 @property
 def actionable(self)->bool:
  """Backward-compatible alias. This NEVER means permission to execute an external action."""
  return self.commercial_review_signal

def _verified_winner(e:ProcurementEvent)->str:
 return e.supplier_id if e.award_state==AwardState.WINNER_VERIFIED and e.supplier_id else ""

def detect_change(previous:ProcurementEvent|None,current:ProcurementEvent)->CommercialChange:
 if previous is None:
  return CommercialChange(current.process_id,current.project_id,ChangeType.NEW_PROCESS,"",current.event_id,False)
 if previous.process_id!=current.process_id or previous.project_id!=current.project_id:
  raise ValueError("change_scope_mismatch")
 if current.stage==ProcurementStage.CANCELLATION or current.change_type==EventChangeType.CANCELLATION:
  return CommercialChange(current.process_id,current.project_id,ChangeType.CANCELLATION,previous.event_id,current.event_id,False)
 old_winner,new_winner=_verified_winner(previous),_verified_winner(current)
 if old_winner and new_winner and old_winner!=new_winner:
  return CommercialChange(current.process_id,current.project_id,ChangeType.SUPPLIER_CHANGE,previous.event_id,current.event_id,True)
 if current.stage!=previous.stage:
  old=_STAGE_ORDER.get(previous.stage); new=_STAGE_ORDER.get(current.stage)
  if old is not None and new is not None and new<old:
   return CommercialChange(current.process_id,current.project_id,ChangeType.STAGE_REGRESSION,previous.event_id,current.event_id,False)
  return CommercialChange(current.process_id,current.project_id,ChangeType.STAGE_ADVANCE,previous.event_id,current.event_id,current.stage in {ProcurementStage.PREQUALIFICATION,ProcurementStage.TENDER})
 typed=_TYPED.get(current.change_type)
 if typed:
  # Spec/quantity/award changes deserve human commercial review; deadline/document/bidder/delivery are recorded but not promoted by themselves.
  signal=current.change_type in {EventChangeType.SPEC,EventChangeType.QUANTITY,EventChangeType.AWARD}
  return CommercialChange(current.process_id,current.project_id,typed,previous.event_id,current.event_id,signal)
 return CommercialChange(current.process_id,current.project_id,ChangeType.REVISION,previous.event_id,current.event_id,False)
