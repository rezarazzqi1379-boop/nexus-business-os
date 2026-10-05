from commercial_genome import CommercialGenome,validate_genome
from nexus_scientist import Experiment,decision
from deal_room import DealRoom,validate_deal_room
from lost_deal_autopsy import LostDeal,validate_lost_deal,distill_failure_pattern
def test_invalid_genome_outcome_rejected():
 assert "invalid_outcome" in validate_genome(CommercialGenome("O",{},"MAGIC",("e:1",)))
def test_scientist_rejects_invalid_metrics_and_cost():
 assert decision(Experiment("E","h",1.2,1.3,1,0,("e",),True))=="REJECT_INVALID_METRIC"
 assert decision(Experiment("E","h",.2,.3,-1,0,("e",),True))=="REJECT_INVALID_COST"
def test_lost_deal_requires_reason_and_evidence():
 assert "lost_deal_requires_reason" in validate_deal_room(DealRoom("O","LOST",("e",)))
 assert "specific_loss_reason_requires_evidence" in validate_lost_deal(LostDeal("O","PRICE",()))
def test_repeated_evidenced_failure_becomes_lesson_not_single_case():
 xs=[LostDeal(str(i),"PRICE",(f"e:{i}",),"Turkey","gear","20MnCr5") for i in range(3)]
 assert distill_failure_pattern(xs)[0]["status"]=="LESSON"
 assert distill_failure_pattern(xs[:1])[0]["status"]=="HYPOTHESIS"
