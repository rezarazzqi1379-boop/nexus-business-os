"""Minimal immutable evidence lineage for NEXUS commercial intelligence."""
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class LineageRecord:
 lineage_id:str; project_id:str; source_origin:str; source_locator:str
 adapter:str; run_id:str; observed_at:datetime; output_type:str; output_id:str
 transformation:str="RAW"; parent_lineage_ids:tuple[str,...]=()

def valid_record(r:LineageRecord)->bool:
 return all((r.lineage_id,r.project_id,r.source_origin,r.source_locator,r.adapter,r.run_id,r.output_type,r.output_id))

def append_lineage(ledger:tuple[LineageRecord,...],r:LineageRecord)->tuple[LineageRecord,...]:
 if not valid_record(r): raise ValueError("invalid_lineage")
 if any(x.lineage_id==r.lineage_id for x in ledger): raise ValueError("immutable_lineage_id")
 known={x.lineage_id:x for x in ledger}
 for p in r.parent_lineage_ids:
  if p not in known: raise ValueError("missing_parent_lineage")
  if known[p].project_id!=r.project_id: raise ValueError("cross_project_lineage")
 return ledger+(r,)

def trace_to_sources(ledger:tuple[LineageRecord,...],lineage_id:str)->tuple[str,...]:
 by_id={x.lineage_id:x for x in ledger}
 if lineage_id not in by_id: return ()
 seen=set(); sources=set()
 def walk(i:str):
  if i in seen:return
  seen.add(i); x=by_id[i]
  if not x.parent_lineage_ids: sources.add(x.source_origin)
  for p in x.parent_lineage_ids: walk(p)
 walk(lineage_id)
 return tuple(sorted(sources))

def independent_origins(ledger:tuple[LineageRecord,...],lineage_id:str)->int:
 return len(trace_to_sources(ledger,lineage_id))
