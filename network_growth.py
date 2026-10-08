"""Evidence-bound commercial network expansion without graph hallucination."""
from dataclasses import dataclass
from enum import Enum
class NodeState(str,Enum): VERIFIED="VERIFIED"; CLUE="CLUE"; HYPOTHESIS="HYPOTHESIS"
@dataclass(frozen=True)
class NetworkNode:
 project_id:str; node_id:str; node_type:str; label:str; state:NodeState; evidence_refs:tuple[str,...]=()
@dataclass(frozen=True)
class NetworkEdge:
 project_id:str; left:str; relation:str; right:str; evidence_ref:str; observed_at:str
def admissible_node(n:NetworkNode)->bool:
 return bool(n.project_id and n.node_id and n.node_type and n.label) and (n.state!=NodeState.VERIFIED or bool(n.evidence_refs))
def admissible_edge(e:NetworkEdge)->bool:
 return bool(e.project_id and e.left and e.relation and e.right and e.evidence_ref and e.observed_at)
def expand_frontier(nodes:tuple[NetworkNode,...],edges:tuple[NetworkEdge,...],project_id:str,seeds:tuple[str,...])->tuple[str,...]:
 known={n.node_id for n in nodes if n.project_id==project_id and admissible_node(n)}
 frontier=set()
 for e in edges:
  if e.project_id!=project_id or not admissible_edge(e): continue
  if e.left in seeds and e.right in known: frontier.add(e.right)
  if e.right in seeds and e.left in known: frontier.add(e.left)
 return tuple(sorted(frontier))
def relationship_strength(edges:tuple[NetworkEdge,...],project_id:str,a:str,b:str)->int:
 refs={e.evidence_ref for e in edges if e.project_id==project_id and {e.left,e.right}=={a,b}}
 return len(refs)
