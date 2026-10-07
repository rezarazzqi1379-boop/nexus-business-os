from datetime import date
from unified_data_environment import UnifiedDataHub
from opportunity_graph import GraphEdge
from demand_signal import DemandSignal
from nexus_v3_evidence_adapter import ingest_edge,ingest_signal
def test_graph_and_signal_ingestion_are_idempotent(tmp_path):
 h=UnifiedDataHub(tmp_path/"h.sqlite",tmp_path)
 e=GraphEdge("GearCo","uses","20MnCr5","VERIFIED_EVIDENCE",("official:1",),"2026-10-05")
 assert ingest_edge(h,e,today=date(2026,10,5)) is True
 assert ingest_edge(h,e,today=date(2026,10,5)) is False
 s=DemandSignal("GearCo","Turkey","PLANT_EXPANSION","2026-10-05",("official:2",),"20MnCr5")
 assert ingest_signal(h,s) is True
 assert ingest_signal(h,s) is False
 assert len(h.project_view("STEEL_SALES"))==2
