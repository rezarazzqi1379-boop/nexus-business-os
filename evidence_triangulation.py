"""Evidence authority, independence and triangulation for high-value claims."""
from dataclasses import dataclass
SOURCE_AUTHORITY={"OFFICIAL_CUSTOMS":5,"OFFICIAL_GOVERNMENT":5,"REGULATOR":5,"STANDARD":5,"OFFICIAL_COMPANY":4,"TRADE_DATASET":4,"INDEPENDENT_SOURCE":3,"COMMERCIAL_AGGREGATOR":2,"SOCIAL_COMPANY_CLAIM":2,"AI_INFERENCE":1}
@dataclass(frozen=True)
class EvidenceRef:
 ref:str; source_type:str; source_family:str; current:bool=True; contradicts:bool=False
def validate_ref(x):
 e=[]
 if not x.ref.strip():e.append("ref_required")
 if x.source_type not in SOURCE_AUTHORITY:e.append("invalid_source_type")
 if not x.source_family.strip():e.append("source_family_required")
 return tuple(e)
def triangulate(items):
 valid=[x for x in items if not validate_ref(x) and x.current]
 support=[x for x in valid if not x.contradicts]; contra=[x for x in valid if x.contradicts]
 families={x.source_family for x in support}
 authority=max((SOURCE_AUTHORITY[x.source_type] for x in support),default=0)
 # Copied/mirrored pages in one family count once. High-value verification needs 2 independent families and >=1 strong source.
 verified=len(families)>=2 and authority>=4 and not contra
 return {"support_count":len(support),"independent_sources":len(families),"max_authority":authority,"contradictions":len(contra),"verified":verified}
