"""Persist only gated distilled knowledge into append-only ProjectMemory."""
from experience_distillation import DistilledKnowledge,memory_eligible
def persist_distilled(store,item:DistilledKnowledge,*,project_id="STEEL_SALES",decided_by="NEXUS_DISTILLATION"):
 ok,blockers=memory_eligible(item)
 if not ok:raise ValueError("memory_ineligible:"+",".join(blockers))
 ns="hypothesis" if item.kind=="HYPOTHESIS" else "lesson"
 statement=f"{item.kind}: {item.statement} [cases={item.case_count}]"
 return store.record(ns,statement,decided_by=decided_by,project_id=project_id,lane="experience_distillation",evidence_refs=item.evidence_refs)
