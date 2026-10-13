"""Adapter from evidence-backed Deal Rooms/Genomes to commercial outcome measurement."""
from commercial_outcome_measurement import Funnel
from deal_room import validate_deal_room
from commercial_genome import validate_genome
from cost_to_outcome import OutcomeCosts,metrics

STAGE_ORDER=("PROSPECT","QUALIFIED","CONTACTED","RFQ","QUOTED","NEGOTIATION","ORDER","WON")
def build_funnel(deals,genomes=(),*,commercial_value=0.0,total_cost_usd=0.0):
 ds=tuple(deals); gs=tuple(genomes)
 if any(validate_deal_room(d) for d in ds):raise ValueError("invalid_deal_room")
 if any(validate_genome(g) for g in gs):raise ValueError("invalid_genome")
 outcome_refs=tuple(sorted({r for d in ds for r in d.evidence_refs} | {r for g in gs for r in g.outcome_evidence_refs}))
 def reached(stage):
  idx=STAGE_ORDER.index(stage)
  return sum(1 for d in ds if d.stage!="LOST" and d.stage in STAGE_ORDER and STAGE_ORDER.index(d.stage)>=idx)
 f=Funnel(discovered=len(ds),qualified=reached("QUALIFIED"),contacted=reached("CONTACTED"),
          rfqs=reached("RFQ"),quotes=reached("QUOTED"),negotiations=reached("NEGOTIATION"),
          orders=reached("ORDER"),commercial_value=commercial_value,outcome_evidence_refs=outcome_refs)
 c=OutcomeCosts(total_cost_usd,qualified_leads=f.qualified,rfqs=f.rfqs,accepted_opportunities=f.qualified,orders=f.orders)
 return {"funnel":f,"cost_metrics":metrics(c),"outcome_evidence_refs":outcome_refs}
