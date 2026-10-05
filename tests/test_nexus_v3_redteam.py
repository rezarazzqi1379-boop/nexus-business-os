from commercial_genome import CommercialGenome,validate_genome
from nexus_scientist import Experiment,decision
from deal_room import DealRoom,validate_deal_room
from lost_deal_autopsy import LostDeal,validate_lost_deal,distill_failure_pattern,promote_pattern
def test_invalid_genome_outcome_rejected():
 assert "invalid_outcome" in validate_genome(CommercialGenome("O",{},"MAGIC",("e:1",)))
def test_scientist_rejects_invalid_metrics_and_cost():
 assert decision(Experiment("E","h",1.2,1.3,1,0,("e",),True))=="REJECT_INVALID_METRIC"
 assert decision(Experiment("E","h",.2,.3,-1,0,("e",),True))=="REJECT_INVALID_COST"
def test_lost_deal_requires_reason_and_evidence():
 assert "lost_deal_requires_reason" in validate_deal_room(DealRoom("O","LOST",("e",)))
 assert "specific_loss_reason_requires_evidence" in validate_lost_deal(LostDeal("O","PRICE",()))
def test_repeated_evidenced_failure_becomes_pattern_not_automatic_lesson():
 xs=[LostDeal(str(i),"PRICE",(f"e:{i}",),"Turkey","gear","20MnCr5") for i in range(3)]
 p=distill_failure_pattern(xs)[0]
 assert p["status"]=="FAILURE_PATTERN"
 assert distill_failure_pattern(xs[:1])[0]["status"]=="HYPOTHESIS"
 assert promote_pattern(p,eval_evidence_refs=(),replicated=True)=="FAILURE_PATTERN"
 assert promote_pattern(p,eval_evidence_refs=("eval:1",),replicated=True)=="LESSON"

def test_duplicate_opportunity_cannot_inflate_failure_pattern():
 xs=[LostDeal("same","PRICE",(f"e:{i}",),"Turkey","gear","20MnCr5") for i in range(4)]
 assert distill_failure_pattern(xs)[0]["cases"]==1
 assert distill_failure_pattern(xs)[0]["status"]=="HYPOTHESIS"

def test_contextless_repetition_is_not_generalized():
 xs=[LostDeal(str(i),"PRICE",(f"e:{i}",)) for i in range(3)]
 assert distill_failure_pattern(xs)[0]["status"]=="HYPOTHESIS"
