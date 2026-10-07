"""Shared-buyer graph semantics: overlap is discovery evidence, never relationship transitivity."""
from collections import defaultdict

def shared_buyers(edges):
 # edges: iterable of (producer,buyer,evidence_ref)
 by=defaultdict(dict)
 for producer,buyer,ref in edges:
  if not all(str(x).strip() for x in (producer,buyer,ref)): raise ValueError("edge_fields_required")
  by[buyer].setdefault(producer,set()).add(ref)
 out=[]
 for buyer,producers in by.items():
  if len(producers)<2: continue
  out.append({"buyer":buyer,"producers":tuple(sorted(producers)),
   "evidence_refs":tuple(sorted({r for rs in producers.values() for r in rs})),
   "state":"SHARED_BUYER_DISCOVERY_SIGNAL"})
 return tuple(sorted(out,key=lambda x:x["buyer"]))

def opportunity_from_overlap(*args,**kwargs):
 return False
