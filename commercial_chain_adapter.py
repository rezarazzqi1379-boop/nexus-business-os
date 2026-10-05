"""Adapters connecting v8 commercial-chain edges to existing NEXUS evidence/opportunity controls."""
from __future__ import annotations
from commercial_chain_graph import ChainEdge
from evidence_triangulation import EvidenceRef,triangulate
from opportunity_graph import GraphEdge,can_promote_verified

def bind_and_promote(edge:ChainEdge,evidence:tuple[EvidenceRef,...],*,today=None)->ChainEdge:
 """Promote only when existing Opportunity Graph + triangulation controls also permit it."""
 if edge.state not in {"CANDIDATE","HYPOTHESIS"}: return edge
 refs=tuple(x.ref for x in evidence)
 if set(edge.evidence_refs)-set(refs): return edge
 og=GraphEdge(edge.source_id,edge.relation,edge.target_id,"HYPOTHESIS",edge.evidence_refs,edge.observed_at or "")
 if not can_promote_verified(og,evidence,today=today): return edge
 t=triangulate(evidence)
 return ChainEdge(edge.source_id,edge.relation,edge.target_id,"VERIFIED",edge.evidence_refs,edge.observed_at,tuple(sorted({x.source_family for x in evidence if x.current and not x.contradicts})),edge.contradiction_refs) if t["verified"] and not edge.contradiction_refs else edge
