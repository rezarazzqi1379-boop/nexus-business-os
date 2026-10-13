from dataclasses import replace
import pytest
from incremental_intelligence import Observation, ingest, candidate_edge, RetrievalBudget, model_route
from intelligence_graph import promotion_allowed


def obs(**kw):
    values = dict(project_id="SANDBOX", lane="proof", source_ref="fixture://rfq",
                  origin_id="fixture-origin", observed_at="2026-10-08T00:00:00Z",
                  payload=b"buyer requests chain", extractor_version="fixture-v1")
    return Observation(**(values | kw))


def test_vertical_change_cache_lineage_candidate():
    h, route = ingest((), obs())
    assert route == "EXTRACT_CHANGED"
    same, route = ingest(h, obs(observed_at="2026-10-08T01:00:00Z"))
    assert same == h and route == "CACHE_HIT_REVALIDATE_FRESHNESS"
    changed, _ = ingest(h, obs(payload=b"buyer cancels chain"))
    assert len(changed) == 2 and changed[1].previous_digest == h[0].digest
    edge = candidate_edge(h[0], "buyer", "chain", project_id="SANDBOX", lane="proof")
    assert h[0].digest in edge.source_id and not promotion_allowed(edge)


@pytest.mark.parametrize("field,value", [("project_id", "OTHER"), ("lane", "OTHER"), ("extractor_version", "v2"), ("origin_id", "new-origin")])
def test_cache_scope_and_extractor_invalidation(field, value):
    h, _ = ingest((), obs())
    new, route = ingest(h, obs(**{field: value}))
    assert len(new) == 2 and route == "EXTRACT_CHANGED"


@pytest.mark.parametrize("project,lane", [("OTHER", "proof"), ("SANDBOX", "other")])
def test_cross_scope_rejected(project, lane):
    h, _ = ingest((), obs())
    with pytest.raises(ValueError, match="cross_scope"):
        candidate_edge(h[0], "b", "i", project_id=project, lane=lane)


def test_tampered_lineage_rejected():
    h, _ = ingest((), obs())
    with pytest.raises(ValueError, match="digest"):
        candidate_edge(replace(h[0], digest="fake"), "b", "i", project_id="SANDBOX", lane="proof")


def test_budget_rejects_before_cost_and_low_yield_stops():
    b = RetrievalBudget(3, 100)
    assert b.reserve(101) == "STOP_BUDGET" and b.queries == 0
    assert b.reserve(40) == "RESERVED"
    b.observe_yield(0)
    assert b.reserve(40) == "RESERVED"
    b.observe_yield(0)
    assert b.reserve(1) == "STOP_LOW_YIELD" and b.queries == 2


def test_model_routing():
    assert model_route(changed=False, ambiguous=True) == "SKIP"
    assert model_route(changed=True, ambiguous=False) == "CHEAP_TRIAGE"
    assert model_route(changed=True, ambiguous=True) == "STRONG_REVIEW"
