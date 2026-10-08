"""Native steel/trade relationship graph distilled from public graph-analysis patterns."""
from dataclasses import dataclass
from collections import defaultdict, deque

@dataclass(frozen=True)
class Edge:
 project_id:str; source_id:str; source_type:str; target_id:str; target_type:str
 relation:str; evidence_ref:str; observed_at:str; weight:float=1.0

def build_adjacency(edges:tuple[Edge,...],project_id:str):
 g=defaultdict(list)
 for e in edges:
  if e.project_id!=project_id: continue
  if not e.evidence_ref or not e.observed_at: raise ValueError("unbound_trade_edge")
  g[e.source_id].append(e); g[e.target_id].append(e)
 return g

def relationship_paths(edges:tuple[Edge,...],project_id:str,start:str,target:str,max_hops:int=3):
 g=build_adjacency(edges,project_id); q=deque([(start,(start,))]); out=[]
 while q:
  node,path=q.popleft()
  if len(path)-1>=max_hops: continue
  for e in g.get(node,[]):
   nxt=e.target_id if e.source_id==node else e.source_id
   if nxt in path: continue
   np=path+(nxt,)
   if nxt==target: out.append(np)
   else:q.append((nxt,np))
 return tuple(out)

def independent_origins(edges:tuple[Edge,...],project_id:str,relation:str)->int:
 return len({e.evidence_ref for e in edges if e.project_id==project_id and e.relation==relation})
