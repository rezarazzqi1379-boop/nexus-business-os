from nexus_core.project_memory import ProjectMemoryStore
from experience_distillation import DistilledKnowledge
from distilled_memory_adapter import persist_distilled
def test_hypothesis_and_lesson_remain_distinct(tmp_path):
 s=ProjectMemoryStore(tmp_path)
 h=persist_distilled(s,DistilledKnowledge("HYPOTHESIS","price may matter",("e:1",),1))
 l=persist_distilled(s,DistilledKnowledge("LESSON","price repeatedly lost deals",("e:1","e:2","e:3"),3))
 assert h.namespace=="hypothesis" and l.namespace=="lesson"
 assert len(s.query(namespace="hypothesis"))==1
def test_ineligible_lesson_never_reaches_memory(tmp_path):
 s=ProjectMemoryStore(tmp_path)
 try:persist_distilled(s,DistilledKnowledge("LESSON","one loss",("e:1",),1))
 except ValueError:pass
 else:assert False
 assert s.query()==()
