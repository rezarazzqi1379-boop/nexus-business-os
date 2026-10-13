"""Unified evidence-bound graph for steel commercial intelligence."""
from dataclasses import dataclass
from enum import Enum
class EvidenceKind(str,Enum): OBSERVED="OBSERVED"; DERIVED="DERIVED"; HYPOTHESIS="HYPOTHESIS"
@dataclass(frozen=True)
class IntelEdge:
 project_id:str; left:str; relation:str; right:str; evidence_ref:str
 observed_at:str; kind:EvidenceKind; current:bool=False
def validate_edge(e:IntelEdge)->bool:
 if not all((e.project_id,e.left,e.relation,e.right,e.evidence_ref,e.observed_at)): return False
 if e.kind!=EvidenceKind.OBSERVED and e.current: return False
 return True
def current_demand_ready(edges:tuple[IntelEdge,...],project_id:str,buyer:str,product:str)->bool:
 relevant=[e for e in edges if e.project_id==project_id and e.kind==EvidenceKind.OBSERVED and e.current]
 has_buyer=any(e.left==buyer or e.right==buyer for e in relevant)
 has_product=any(e.left==product or e.right==product for e in relevant)
 has_trigger=any(e.relation in {"CURRENT_RFQ","CURRENT_TENDER","CURRENT_PROCUREMENT_NEED","CURRENT_STOCK_NEED"} for e in relevant)
 origins={e.evidence_ref for e in relevant}
 return has_buyer and has_product and has_trigger and len(origins)>=2
def failure_to_part_hypothesis(project_id,plant,equipment,component,part,ref,asof):
 return (
  IntelEdge(project_id,plant,"USES_EQUIPMENT",equipment,ref,asof,EvidenceKind.HYPOTHESIS),
  IntelEdge(project_id,equipment,"HAS_COMPONENT",component,ref,asof,EvidenceKind.HYPOTHESIS),
  IntelEdge(project_id,component,"MAY_REQUIRE_REPLACEMENT_PART",part,ref,asof,EvidenceKind.HYPOTHESIS),
 )
