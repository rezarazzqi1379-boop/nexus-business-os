"""Minimal governed MTC intake contract for steel procurement/QA."""
from dataclasses import dataclass

@dataclass(frozen=True)
class MTCRecord:
 project_id:str; certificate_number:str; issuing_date:str; standard:str
 heat_number:str; product_quality:str=""; product_size:str=""
 chemical_rows:int=0; mechanical_rows:int=0
 source_ref:str=""; extraction_method:str=""; extraction_confidence:float=0.0

def validate_mtc(r:MTCRecord)->tuple[bool,tuple[str,...]]:
 missing=[]
 for k in ("project_id","certificate_number","issuing_date","standard","heat_number","source_ref"):
  if not getattr(r,k): missing.append(k)
 if not 0<=r.extraction_confidence<=1: missing.append("invalid_confidence")
 return not missing,tuple(missing)

def review_route(r:MTCRecord)->str:
 ok,_=validate_mtc(r)
 if not ok:return "REJECT_INCOMPLETE"
 if r.extraction_confidence<0.60:return "MANUAL_OR_VISION_REVIEW"
 if r.chemical_rows==0 or r.mechanical_rows==0:return "COMPLETENESS_REVIEW"
 return "STRUCTURED_REVIEW_READY"

def may_claim_standard_compliance(r:MTCRecord)->bool:
 # Extraction is not engineering/standards verification.
 return False
