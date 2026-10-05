"""Evidence-bound Commercial Genome; similarity is deterministic feature overlap."""
from dataclasses import dataclass
OUTCOMES={"UNKNOWN","RFQ","QUOTED","WON","LOST","NO_RESPONSE","DISQUALIFIED"}
DIMENSIONS=("buyer","need","product","application","market","trade","competitor","price","logistics","payment","compliance","relationship","timing")
@dataclass(frozen=True)
class GenomeFeature:
 dimension:str; value:str; evidence_refs:tuple[str,...]; observed_at:str
def validate_feature(f):
 e=[]
 if f.dimension not in DIMENSIONS:e.append("invalid_dimension")
 if not f.value.strip():e.append("feature_value_required")
 if not f.evidence_refs:e.append("feature_evidence_required")
 if not f.observed_at.strip():e.append("feature_observed_at_required")
 return tuple(e)
@dataclass(frozen=True)
class CommercialGenome:
 opportunity_id:str; features:tuple[GenomeFeature,...]; outcome:str="UNKNOWN"; outcome_evidence_refs:tuple[str,...]=()
def validate_genome(g):
 e=[]
 if not g.opportunity_id.strip():e.append("opportunity_id_required")
 if g.outcome not in OUTCOMES:e.append("invalid_outcome")
 for f in g.features:e.extend(validate_feature(f))
 if g.outcome!="UNKNOWN" and not g.outcome_evidence_refs:e.append("outcome_requires_evidence")
 return tuple(e)
def _sets(g):
 out={}
 for f in g.features:out.setdefault(f.dimension,set()).add(f.value)
 return out
def similarity(a,b):
 if validate_genome(a) or validate_genome(b):raise ValueError("invalid_genome")
 aa,bb=_sets(a),_sets(b); scores=[]
 for d in DIMENSIONS:
  x,y=aa.get(d,set()),bb.get(d,set())
  if not x and not y:continue
  scores.append(len(x&y)/len(x|y))
 return round(sum(scores)/len(scores),4) if scores else 0.0
def comparable(target,history,minimum=.5,min_shared_dimensions=2):
 if validate_genome(target):raise ValueError("invalid_genome")
 out=[]
 td=set(_sets(target))
 for h in history:
  if validate_genome(h):continue
  shared=td & set(_sets(h))
  s=similarity(target,h)
  if len(shared)>=min_shared_dimensions and s>=minimum:out.append((s,h))
 return tuple(sorted(out,key=lambda x:(-x[0],x[1].opportunity_id)))
