from datetime import datetime,timezone
import pytest
from evidence_lineage import *
T=datetime(2026,10,7,tzinfo=timezone.utc)
def r(**kw):
 d=dict(lineage_id="L1",project_id="NEXUS-BUSINESS-OS",source_origin="official:kz",source_locator="u",adapter="official_api",run_id="R1",observed_at=T,output_type="PROCUREMENT_EVENT",output_id="E1"); d.update(kw); return LineageRecord(**d)

def test_lineage_is_append_only(): 
 l=append_lineage((),r())
 with pytest.raises(ValueError): append_lineage(l,r())
def test_parent_must_exist():
 with pytest.raises(ValueError): append_lineage((),r(lineage_id="L2",parent_lineage_ids=("MISSING",)))
def test_cross_project_parent_rejected():
 l=append_lineage((),r())
 with pytest.raises(ValueError): append_lineage(l,r(lineage_id="L2",project_id="PRJ-HYD-01",parent_lineage_ids=("L1",)))
def test_trace_counts_underlying_sources_not_adapters():
 l=append_lineage((),r())
 l=append_lineage(l,r(lineage_id="L2",adapter="exa",run_id="R2",output_id="C2",source_locator="mirror"))
 l=append_lineage(l,r(lineage_id="L3",source_origin="company:qarmet",source_locator="company",adapter="web",run_id="R3",output_id="C3"))
 l=append_lineage(l,r(lineage_id="L4",source_origin="derived",source_locator="internal",adapter="nexus",run_id="R4",output_type="CLAIM",output_id="Q",parent_lineage_ids=("L1","L2","L3")))
 assert trace_to_sources(l,"L4")==("company:qarmet","official:kz")
 assert independent_origins(l,"L4")==2
