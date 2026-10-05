from deal_room import DealRoom,validate_deal_room
from nexus_scientist import Experiment,decision
def test_advanced_deal_stage_needs_evidence():
 d=DealRoom("O1","RFQ",(),next_action="review spec")
 assert "advanced_stage_requires_evidence" in validate_deal_room(d)
def test_scientist_cannot_promote_without_heldout_evidence():
 x=Experiment("E1","new scorer improves precision",.7,.8,1,0.8,("eval:1",),False)
 assert decision(x)=="HUMAN_REVIEW_NO_HELD_OUT"
def test_measured_heldout_improvement_can_be_promotion_candidate_not_deployment():
 x=Experiment("E2","new scorer improves precision",.7,.8,1,0.8,("eval:2",),True)
 assert decision(x)=="PROMOTE_CANDIDATE"
