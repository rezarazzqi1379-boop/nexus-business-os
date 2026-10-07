"""Evidence binding rules for consequential commercial-chain relations."""
from dataclasses import dataclass
from evidence_triangulation import EvidenceRef,triangulate

@dataclass(frozen=True)
class BoundEdgeEvidence:
 edge_key:str
 evidence:EvidenceRef

def can_verify_bound_edge(*,edge_key:str,bindings:tuple[BoundEdgeEvidence,...])->bool:
 xs=tuple(x.evidence for x in bindings if x.edge_key==edge_key)
 if len(xs)<2:return False
 return bool(triangulate(xs)["verified"])
