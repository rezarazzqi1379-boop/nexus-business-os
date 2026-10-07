"""Governed parallel research routing and evidence accounting."""
from dataclasses import dataclass
from enum import Enum

class RouteState(str,Enum):
 READY="READY"; HOLD="HOLD"; FALLBACK="FALLBACK"; REJECT="REJECT"

@dataclass(frozen=True)
class Workstream:
 workstream_id:str; project_id:str; question:str; signal_type:str; preferred_adapter:str
 fallback_adapter:str=""; protected:bool=False

@dataclass(frozen=True)
class ResearchResult:
 workstream_id:str; project_id:str; adapter:str; claim_key:str; source_locator:str; evidence_fingerprint:str
 source_origin:str=""
 latency_ms:int=0; cost_units:float=0.0; success:bool=True

def route(w:Workstream, available:tuple[str,...])->tuple[RouteState,str]:
 if not w.workstream_id or not w.project_id or not w.question or not w.signal_type: return (RouteState.REJECT,"")
 if w.protected: return (RouteState.HOLD,"")
 if w.preferred_adapter in available: return (RouteState.READY,w.preferred_adapter)
 if w.fallback_adapter and w.fallback_adapter in available: return (RouteState.FALLBACK,w.fallback_adapter)
 return (RouteState.HOLD,"")

def dedupe_results(results:tuple[ResearchResult,...],project_id:str)->tuple[ResearchResult,...]:
 seen=set(); out=[]
 for r in results:
  if not r.success or r.project_id!=project_id or not r.source_locator or not r.evidence_fingerprint: continue
  # Search engines are transport. Independence comes from underlying source origin.
  origin=r.source_origin or r.evidence_fingerprint
  key=(r.claim_key,origin,r.evidence_fingerprint)
  if key in seen: continue
  seen.add(key); out.append(r)
 return tuple(out)

def independent_source_count(results:tuple[ResearchResult,...])->int:
 return len({r.source_origin for r in results if r.success and r.source_origin})

def research_metrics(raw:tuple[ResearchResult,...],clean:tuple[ResearchResult,...])->dict[str,float]:
 successful=[r for r in raw if r.success]
 unique=len(clean); total=len(successful); cost=sum(r.cost_units for r in successful)
 return {
  "successful_results":float(total),
  "unique_evidence":float(unique),
  "independent_sources":float(independent_source_count(clean)),
  "duplicate_ratio":0.0 if not total else round(1-(unique/total),4),
  "serial_latency_ms":float(sum(r.latency_ms for r in successful)),
  "parallel_wall_clock_ms":float(max((r.latency_ms for r in successful),default=0)),
  "cost_units":float(cost),
  "evidence_per_cost":0.0 if not cost else round(unique/cost,4),
 }
