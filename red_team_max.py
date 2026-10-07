"""Cross-module adversarial invariants for NEXUS Red Team MAX v3."""
from dataclasses import dataclass
from opportunity_graph import GraphEdge,can_promote_verified
from sales_readiness import overall_readiness

@dataclass(frozen=True)
class RedTeamFinding:
 finding_id:str; severity:str; module:str; failure_mode:str; safe_fix:str

def opportunity_requires_compliance(readiness:dict[str,str])->bool:
 return overall_readiness(readiness)=="READY"

def historical_edge_may_be_current(*,historical:bool,current_evidence_refs:tuple[str,...])->bool:
 return (not historical) or bool(current_evidence_refs)

def contact_is_authority(*,role_evidence:tuple[str,...],authority_evidence:tuple[str,...])->bool:
 return bool(role_evidence) and bool(authority_evidence)

def recurring_grade(*,same_grade_events:int,category_events:int)->bool:
 # Category recurrence is deliberately irrelevant to grade-specific recurrence.
 return same_grade_events>=2
