"""Persist governed v3 graph edges and demand signals into UnifiedDataHub."""
import hashlib
from datetime import datetime,timezone
from unified_data_environment import EvidenceObservation,UnifiedDataHub
from opportunity_graph import GraphEdge,validate_edge
from demand_signal import DemandSignal,validate_signal
def _observed_at(value):
 parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
 if parsed.tzinfo is None: parsed=parsed.replace(tzinfo=timezone.utc)
 return parsed.isoformat()
def _id(prefix,*parts):
 return prefix+"-"+hashlib.sha256("|".join(parts).encode()).hexdigest()[:20]
def ingest_edge(hub:UnifiedDataHub,e:GraphEdge,project_id="STEEL_SALES",today=None):
 err=validate_edge(e,today=today)
 if err:raise ValueError("invalid_edge:"+",".join(err))
 oid=_id("edge",e.subject,e.predicate,e.object,e.state,*e.evidence_refs)
 o=EvidenceObservation(oid,project_id,"opportunity_edge",f"{e.subject} -> {e.predicate} -> {e.object} [{e.state}]",e.evidence_refs,_observed_at(e.observed_at),1.0 if e.state in {"FACT","VERIFIED_EVIDENCE"} else .5)
 return hub.record_observation(o)
def ingest_signal(hub:UnifiedDataHub,s:DemandSignal,project_id="STEEL_SALES"):
 err=validate_signal(s)
 if err:raise ValueError("invalid_signal:"+",".join(err))
 oid=_id("signal",s.company,s.country,s.signal_type,s.observed_at,*s.evidence_refs)
 statement=f"{s.company} {s.signal_type} country={s.country} plant={s.plant or 'UNKNOWN'} potential_need={s.potential_need or 'UNKNOWN'}"
 return hub.record_observation(EvidenceObservation(oid,project_id,"demand_signal",statement,s.evidence_refs,_observed_at(s.observed_at),.5))
