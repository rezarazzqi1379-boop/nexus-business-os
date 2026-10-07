"""Evidence-safe two-hop commercial graph expansion."""
from dataclasses import dataclass

@dataclass(frozen=True)
class RelationshipEdge:
 subject:str; predicate:str; object:str; evidence_refs:tuple[str,...]; historical:bool=True

def expand_two_hop(first:tuple[RelationshipEdge,...],second:tuple[RelationshipEdge,...]):
 out=[]
 for a in first:
  for b in second:
   if a.object!=b.subject: continue
   # Never collapse A->B and B->C into a verified A->C commercial relationship.
   out.append({"origin":a.subject,"via":a.object,"target":b.object,
    "state":"CANDIDATE_TWO_HOP","evidence_refs":tuple(dict.fromkeys(a.evidence_refs+b.evidence_refs))})
 return tuple(out)

def can_promote_direct(edge:RelationshipEdge)->bool:
 return bool(edge.evidence_refs) and bool(edge.subject.strip()) and bool(edge.object.strip())
