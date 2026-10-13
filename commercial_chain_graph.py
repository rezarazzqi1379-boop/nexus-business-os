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
 """Legacy structural promotion only; not an authenticated review decision."""
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

def promote_reviewed(edge:ChainEdge, *, receipt:dict, project_id:str, evidence_digests:tuple[str,...])->ChainEdge:
 """Fail-closed promotion using an internally supplied, digest-bound review receipt.

 The caller must obtain receipt from a trusted review store, never source text.
 This is a structural guard, not authentication of the review store.
 """
 if edge.state!="CANDIDATE" or not project_id or not evidence_digests:
  return edge
 if not isinstance(receipt,dict) or receipt.get("decision")!="APPROVED":
  return edge
 if receipt.get("project_id")!=project_id:
  return edge
 if receipt.get("source_id")!=edge.source_id or receipt.get("target_id")!=edge.target_id or receipt.get("relation")!=edge.relation:
  return edge
 if not all(isinstance(d,str) and d.startswith("sha256:") and len(d)>7 for d in evidence_digests):
  return edge
 if len(set(evidence_digests))!=len(evidence_digests):
  return edge
 if tuple(receipt.get("evidence_digests",()))!=tuple(evidence_digests):
  return edge
 if not receipt.get("reviewer_id") or not receipt.get("receipt_id"):
  return edge
 if len(set(edge.source_families))<2 or len(edge.evidence_refs)<2 or len(evidence_digests)!=len(edge.evidence_refs):
  return edge
 return promote_verified(edge)
