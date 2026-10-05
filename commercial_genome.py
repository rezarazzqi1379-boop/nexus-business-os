"""Deterministic Commercial Genome baseline. Similarity is feature overlap, never LLM intuition."""
from dataclasses import dataclass
OUTCOMES={"UNKNOWN","RFQ","QUOTED","WON","LOST","NO_RESPONSE","DISQUALIFIED"}
DIMENSIONS=("buyer","need","product","application","market","trade","competitor","price","logistics","payment","compliance","relationship","timing")
@dataclass(frozen=True)
class CommercialGenome:
 opportunity_id:str
 features:dict[str,tuple[str,...]]
 outcome:str="UNKNOWN"
 evidence_refs:tuple[str,...]=()
def validate_genome(g:CommercialGenome)->tuple[str,...]:
 e=[]
 if not g.opportunity_id.strip():e.append("opportunity_id_required")
 if g.outcome not in OUTCOMES:e.append("invalid_outcome")
 unknown=set(g.features)-set(DIMENSIONS)
 if unknown:e.append("unknown_dimensions:"+",".join(sorted(unknown)))
 for k,v in g.features.items():
  if not isinstance(v,tuple):e.append("features_must_be_tuples:"+k)
 if g.outcome!="UNKNOWN" and not g.evidence_refs:e.append("outcome_requires_evidence")
 return tuple(e)
def similarity(a:CommercialGenome,b:CommercialGenome)->float:
 if validate_genome(a) or validate_genome(b):raise ValueError("invalid_genome")
 scores=[]
 for d in DIMENSIONS:
  x,y=set(a.features.get(d,())),set(b.features.get(d,()))
  if not x and not y:continue
  scores.append(len(x&y)/len(x|y) if x|y else 0)
 return round(sum(scores)/len(scores),4) if scores else 0.0
def comparable(target,history,minimum=.5):
 return tuple(sorted(((similarity(target,h),h) for h in history if similarity(target,h)>=minimum),key=lambda x:(-x[0],x[1].opportunity_id)))
