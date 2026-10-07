"""Evidence-bound multi-hop commercial chain graph for NEXUS v8."""
from __future__ import annotations
from dataclasses import dataclass

EDGE_STATES={"HYPOTHESIS","CANDIDATE","VERIFIED","CONTRADICTED","STALE","SUPERSEDED"}
COMPANY_LEVEL_RELATIONS={"BOUGHT","SOLD","SUPPLIED_TO","BOUGHT_FROM","PROCESSED","IMPORTED","EXPORTED","STOCKED","USED"}

@dataclass(frozen=True)
class ChainEdge:
 source_id:str
 relation:str
 target_id:str
 state:str="HYPOTHESIS"
 evidence_refs:tuple[str,...]=()
 observed_at:str|None=None
 source_families:tuple[str,...]=()
 contradiction_refs:tuple[str,...]=()

 def validate(self)->tuple[str,...]:
  errors=[]
  if not self.source_id.strip() or not self.target_id.strip():errors.append("entity_required")
  if not self.relation.strip():errors.append("relation_required")
  if self.state not in EDGE_STATES:errors.append("invalid_state")
  if self.state=="VERIFIED":
   if not self.evidence_refs:errors.append("verified_requires_evidence")
   if len(set(self.source_families))<2:errors.append("verified_requires_independent_sources")
   if self.contradiction_refs:errors.append("verified_has_unresolved_contradiction")
  return tuple(errors)

def candidate_edge(*,source_id:str,relation:str,target_id:str,evidence_refs=(),source_families=(),observed_at=None)->ChainEdge:
 return ChainEdge(source_id,relation,target_id,"CANDIDATE",tuple(evidence_refs),observed_at,tuple(source_families))

def promote_verified(edge:ChainEdge)->ChainEdge:
 candidate=ChainEdge(edge.source_id,edge.relation,edge.target_id,"VERIFIED",edge.evidence_refs,edge.observed_at,edge.source_families,edge.contradiction_refs)
 if candidate.validate():return edge
 return candidate

def infer_company_edge_from_aggregate_trade(*,country:str,product:str)->ChainEdge:
 """Aggregate trade can create a search hypothesis, never a named-company fact."""
 return ChainEdge(country,"AGGREGATE_TRADE_SIGNAL",product,"HYPOTHESIS")

def expansion_questions(edge:ChainEdge)->tuple[str,...]:
 """Generate reversible adjacent discovery questions; these are not factual edges."""
 return (
  f"Who is immediately upstream of {edge.source_id} for {edge.relation}?",
  f"Who is immediately downstream of {edge.target_id}?",
  f"What entity should exist between {edge.source_id} and {edge.target_id} but is missing?",
  f"What evidence would falsify {edge.source_id} {edge.relation} {edge.target_id}?",
 )
