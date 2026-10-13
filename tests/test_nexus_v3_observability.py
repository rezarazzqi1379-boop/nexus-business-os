from evidence_time import EvidenceTime,validate_evidence_time,storage_timestamp
from agent_health import AgentTrace,health_score
from experience_distillation import DistilledKnowledge,memory_eligible
def test_date_precision_is_preserved_while_storage_uses_retrieval_time():
 t=EvidenceTime("2026-10-05","DATE","2026-10-05T10:00:00+00:00")
 assert validate_evidence_time(t)==()
 assert t.observed_value=="2026-10-05"
 assert storage_timestamp(t).startswith("2026-10-05T10:00:00")
def test_retrieval_timestamp_must_be_timezone_aware():
 assert "retrieved_at_requires_timezone" in validate_evidence_time(EvidenceTime("2026-10-05","DATE","2026-10-05T10:00:00"))
def test_agent_health_penalizes_silent_failure_and_rewards_evidence():
 good=AgentTrace("a",True,("e:1",),100,0)
 bad=AgentTrace("a",False,(),100,0,silent_failure=True)
 assert health_score([good])>health_score([bad])
def test_single_case_cannot_be_promoted_to_lesson_memory():
 ok,blockers=memory_eligible(DistilledKnowledge("LESSON","price loss",("e:1",),1))
 assert not ok and "insufficient_cases_for_promoted_knowledge" in blockers
 assert memory_eligible(DistilledKnowledge("HYPOTHESIS","price may matter",("e:1",),1))[0]
