"""Gate distilled commercial lessons before ProjectMemory persistence."""
from dataclasses import dataclass
@dataclass(frozen=True)
class DistilledKnowledge:
 kind:str; statement:str; evidence_refs:tuple[str,...]; case_count:int
KINDS={"LESSON","FAILURE_PATTERN","WINNING_PATTERN","ANTI_PATTERN","PLAYBOOK","SKILL","DECISION_RULE","HYPOTHESIS"}
def memory_eligible(x:DistilledKnowledge)->tuple[bool,tuple[str,...]]:
 blockers=[]
 if x.kind not in KINDS:blockers.append("invalid_kind")
 if not x.statement.strip():blockers.append("statement_required")
 if not x.evidence_refs:blockers.append("evidence_required")
 if x.case_count<1:blockers.append("case_count_required")
 if x.kind!="HYPOTHESIS" and x.case_count<3:blockers.append("insufficient_cases_for_promoted_knowledge")
 return (not blockers,tuple(blockers))
