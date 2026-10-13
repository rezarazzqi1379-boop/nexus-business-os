"""Adapters connecting v8 commercial-chain edges to existing NEXUS evidence/opportunity controls."""
from __future__ import annotations
from commercial_chain_graph import ChainEdge
from evidence_triangulation import EvidenceRef,triangulate
from opportunity_graph import GraphEdge,can_promote_verified
from chain_evidence_binding import BoundEdgeEvidence,can_verify_bound_edge

def edge_key(edge:ChainEdge)->str:
 return f"{edge.source_id}|{edge.relation}|{edge.target_id}"

def bind_and_promote(edge:ChainEdge,evidence:tuple[EvidenceRef,...],*,bindings:tuple[BoundEdgeEvidence,...]=(),today=None)->ChainEdge:
 """Promote only when evidence is both strong and explicitly bound to this relationship."""
 if edge.state not in {"CANDIDATE","HYPOTHESIS"}: return edge
 refs=tuple(x.ref for x in evidence)
 if set(edge.evidence_refs)-set(refs): return edge
 key=edge_key(edge)
 effective=bindings or tuple(BoundEdgeEvidence(key,x) for x in evidence if x.ref in edge.evidence_refs)
 if not can_verify_bound_edge(edge_key=key,bindings=effective):return edge
 og=GraphEdge(edge.source_id,edge.relation,edge.target_id,"HYPOTHESIS",edge.evidence_refs,edge.observed_at or "")
 if not can_promote_verified(og,evidence,today=today): return edge
 t=triangulate(evidence)
 return ChainEdge(edge.source_id,edge.relation,edge.target_id,"VERIFIED",edge.evidence_refs,edge.observed_at,tuple(sorted({x.source_family for x in evidence if x.current and not x.contradicts})),edge.contradiction_refs) if t["verified"] and not edge.contradiction_refs else edge
