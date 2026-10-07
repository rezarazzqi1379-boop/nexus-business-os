"""Deal Room contract for serious opportunities."""
from dataclasses import dataclass
STAGES={"PROSPECT","QUALIFIED","CONTACTED","RFQ","QUOTED","NEGOTIATION","ORDER","WON","LOST"}
@dataclass(frozen=True)
class DealRoom:
 opportunity_id:str; stage:str; evidence_refs:tuple[str,...]
 contacts:tuple[str,...]=(); specifications:tuple[str,...]=(); quotes:tuple[str,...]=()
 commitments:tuple[str,...]=(); loss_reason:str=""; risks:tuple[str,...]=(); open_questions:tuple[str,...]=(); next_action:str=""
def validate_deal_room(d:DealRoom)->tuple[str,...]:
 e=[]
 if not d.opportunity_id.strip():e.append("opportunity_id_required")
 if d.stage not in STAGES:e.append("invalid_stage")
 if d.stage in {"RFQ","QUOTED","NEGOTIATION","ORDER","WON","LOST"} and not d.evidence_refs:e.append("advanced_stage_requires_evidence")
 if d.stage=="LOST" and not d.loss_reason.strip():e.append("lost_deal_requires_reason")
 if d.stage not in {"WON","LOST"} and not d.next_action.strip():e.append("open_deal_requires_next_action")
 return tuple(e)
