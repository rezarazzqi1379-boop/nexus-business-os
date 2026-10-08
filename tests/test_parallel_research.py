from parallel_research import *

def w(**kw):
 d=dict(workstream_id="W1",project_id="P1",question="find procurement plan",signal_type="PROCUREMENT_PLAN",preferred_adapter="official_api",fallback_adapter="search"); d.update(kw); return Workstream(**d)
def r(**kw):
 d=dict(workstream_id="W1",project_id="P1",adapter="search",claim_key="buyer:A needs steel",source_locator="u1",evidence_fingerprint="fp1",source_origin="origin1",latency_ms=10,cost_units=1); d.update(kw); return ResearchResult(**d)

def test_routes_preferred_then_fallback():
 assert route(w(),("official_api","search"))==(RouteState.READY,"official_api")
 assert route(w(),("search",))==(RouteState.FALLBACK,"search")
def test_protected_workstream_never_runs_by_router(): assert route(w(protected=True),("official_api",))==(RouteState.HOLD,"")
def test_same_underlying_source_via_two_searchers_is_not_independent():
 raw=(r(adapter="exa"),r(adapter="web",source_locator="mirror"))
 clean=dedupe_results(raw,"P1"); assert len(clean)==1 and independent_source_count(clean)==1
def test_same_claim_from_two_origins_is_independent():
 raw=(r(evidence_fingerprint="a",source_origin="company"),r(adapter="official",source_locator="u2",evidence_fingerprint="b",source_origin="government"))
 clean=dedupe_results(raw,"P1"); assert len(clean)==2 and independent_source_count(clean)==2
def test_cross_project_result_is_dropped(): assert dedupe_results((r(project_id="OTHER"),),"P1")==()
def test_failed_adapter_result_is_not_evidence(): assert dedupe_results((r(success=False),),"P1")==()
def test_parallel_wall_clock_uses_slowest_worker_not_sum():
 raw=(r(latency_ms=10,evidence_fingerprint="a"),r(latency_ms=30,evidence_fingerprint="b",source_origin="origin2"))
 m=research_metrics(raw,dedupe_results(raw,"P1")); assert m["serial_latency_ms"]==40 and m["parallel_wall_clock_ms"]==30
def test_metrics_penalize_duplicate_work():
 raw=(r(adapter="a"),r(adapter="b",source_locator="mirror")); m=research_metrics(raw,dedupe_results(raw,"P1"))
 assert m["unique_evidence"]==1 and m["duplicate_ratio"]==0.5
def test_zero_cost_does_not_divide_by_zero():
 raw=(r(cost_units=0),); assert research_metrics(raw,dedupe_results(raw,"P1"))["evidence_per_cost"]==0
