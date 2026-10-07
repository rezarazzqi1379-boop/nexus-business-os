"""Evidence-native intelligence graph. Links never erase provenance or turn hypotheses into facts."""
from dataclasses import dataclass
from typing import FrozenSet
@dataclass(frozen=True)
class Node:
 id:str; kind:str; project_id:str; observed_at:str; source_id:str; evidence_class:str
@dataclass(frozen=True)
class Edge:
 src:str; dst:str; relation:str; source_id:str; state:str
ALLOWED_CLASSES=frozenset({"FACT","MEASUREMENT","CLAIM","ESTIMATE","ASSUMPTION","HYPOTHESIS","UNKNOWN"})
def valid_node(n:Node)->bool:
 return bool(n.id and n.kind and n.project_id and n.source_id) and n.evidence_class in ALLOWED_CLASSES
def link(a:Node,b:Node,relation:str,source_id:str,verified:bool=False)->Edge:
 if not valid_node(a) or not valid_node(b): raise ValueError("invalid node")
 if a.project_id!=b.project_id: raise ValueError("cross_project_link_blocked")
 return Edge(a.id,b.id,relation,source_id,"VERIFIED" if verified else "HYPOTHESIS")
def promotion_allowed(edge:Edge)->bool:
 return edge.state=="VERIFIED" and bool(edge.source_id)
