from procurement_graph import *
from procurement_fit import *
from adaptive_discovery import *
from reverse_discovery_queue import DiscoveryTask

def test_tender_does_not_infer_award():
 p=ProcurementNode("zvezda-40hn2ma","PAO ZVEZDA","PAO ZVEZDA","40HN2MA rolled steel",grade="40HN2MA",quantity=5.04,quantity_unit="t",evidence_refs=("tender:z",),source_families=("tender",),observed_at="2026-08-31")
 assert published_demand_edge(p).relation=="PUBLISHED_DEMAND"
 assert award_edge(p) is None

def test_winner_requires_award_state():
 p=ProcurementNode("x","B","B","steel",winner_supplier="S",evidence_refs=("x",))
 assert "winner_without_award" in p.validate()

def test_unknown_dimension_blocks_exact_fit():
 checks={k:True for k in FIELDS};checks["dimensions"]=None
 assert assess_fit(checks,equivalence_supported=True)=="ENGINEERING_REVIEW"

def test_adaptive_pauses_low_information_path():
 b=DiscoveryTask("belarus","resolve importer","INTERMEDIATE",1,1,1,1,1,1)
 a=AdaptiveTask(b,1,1,1,queries=8,new_evidence=1)
 assert a.state()=="PAUSED_LOW_INFORMATION_GAIN"

def test_adaptive_prioritizes_resolution_recency_and_fit():
 b1=DiscoveryTask("opaque","q","p",1,1,1,1,1,1);b2=DiscoveryTask("demand","q","p",1,1,1,1,1,1)
 xs=prioritize_adaptive((AdaptiveTask(b1,.2,.5,.5),AdaptiveTask(b2,.9,1,1)))
 assert xs[0].base.task_id=="demand"
