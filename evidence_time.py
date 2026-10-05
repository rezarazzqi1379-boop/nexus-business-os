"""Temporal evidence semantics without fabricated timestamp precision."""
from dataclasses import dataclass
from datetime import datetime
PRECISION={"DATE","DATETIME","PERIOD","UNKNOWN"}
@dataclass(frozen=True)
class EvidenceTime:
 observed_value:str; precision:str; retrieved_at:str
def validate_evidence_time(t):
 e=[]
 if t.precision not in PRECISION:e.append("invalid_temporal_precision")
 if not t.observed_value.strip() and t.precision!="UNKNOWN":e.append("observed_value_required")
 try:
  r=datetime.fromisoformat(t.retrieved_at.replace("Z","+00:00"))
  if r.tzinfo is None:e.append("retrieved_at_requires_timezone")
 except ValueError:e.append("invalid_retrieved_at")
 try:
  if t.precision=="DATE": datetime.strptime(t.observed_value,"%Y-%m-%d")
  elif t.precision=="DATETIME":
   o=datetime.fromisoformat(t.observed_value.replace("Z","+00:00"))
   if o.tzinfo is None:e.append("observed_datetime_requires_timezone")
 except ValueError:e.append("invalid_observed_value")
 return tuple(e)
def storage_timestamp(t):
 if validate_evidence_time(t):raise ValueError("invalid_evidence_time")
 return t.retrieved_at
