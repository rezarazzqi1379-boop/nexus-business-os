"""Evidence-safe buyer-DNA matching for commercial discovery."""
from dataclasses import dataclass

@dataclass(frozen=True)
class BuyerDNA:
 entity:str
 roles:frozenset[str]
 products:frozenset[str]
 hs:frozenset[str]
 applications:frozenset[str]
 countries:frozenset[str]
 evidence_refs:tuple[str,...]

def similarity(a:BuyerDNA,b:BuyerDNA)->dict:
 dims=("roles","products","hs","applications","countries")
 scores={}
 for d in dims:
  x,y=getattr(a,d),getattr(b,d)
  scores[d]=0.0 if not x or not y else len(x&y)/len(x|y)
 used=[v for v in scores.values() if v>0]
 return {"score":round(sum(used)/len(used),4) if used else 0.0,"dimensions":scores,"state":"CANDIDATE_LOOKALIKE"}

def qualified_by_similarity(*args,**kwargs):
 # Similarity is a discovery signal and can never qualify a buyer.
 return False
