"""Temporal provenance without inventing source precision."""
from dataclasses import dataclass
from datetime import datetime,timezone
PRECISION={"DATE","DATETIME","PERIOD","UNKNOWN"}
@dataclass(frozen=True)
class EvidenceTime:
 observed_value:str; precision:str; retrieved_at:str
def validate_evidence_time(t:EvidenceTime)->tuple[str,...]:
 e=[]
 if t.precision not in PRECISION:e.append("invalid_temporal_precision")
 if not t.observed_value.strip() and t.precision!="UNKNOWN":e.append("observed_value_required")
 try:
  r=datetime.fromisoformat(t.retrieved_at.replace("Z","+00:00"))
  if r.tzinfo is None:e.append("retrieved_at_requires_timezone")
 except ValueError:e.append("invalid_retrieved_at")
 return tuple(e)
def storage_timestamp(t:EvidenceTime)->str:
 if validate_evidence_time(t):raise ValueError("invalid_evidence_time")
 r=datetime.fromisoformat(t.retrieved_at.replace("Z","+00:00")).astimezone(timezone.utc)
 return r.isoformat()
