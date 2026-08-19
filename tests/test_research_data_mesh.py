import pytest

from nexus_core.research_data_mesh import (
    ResearchHit,
    ResearchQuery,
    ResearchSource,
    fuse_hits,
    plan_sources,
)


def test_plans_bounded_high_confidence_low_latency_sources():
    query = ResearchQuery("q1", "OCTG heat treatment expansion", "commercial-intelligence", max_sources=2)
    sources = [
        ResearchSource("official", "official", "ussteel.com", "2026-08-20T00:00:00+00:00", "url:https://ussteel.com/x", 300, 95),
        ResearchSource("exa", "web", "exa", "2026-08-20T00:00:01+00:00", "connector:exa:1", 120, 85),
        ResearchSource("noise", "web", "example.com", "2026-08-20T00:00:02+00:00", "url:https://example.com", 50, 30),
    ]
    plan = plan_sources(query, sources)
    assert plan.selected_sources == ("official", "exa")
    assert plan.rejected_sources == ("noise",)


def test_fuses_duplicate_claims_with_corroboration_without_hiding_raw_evidence():
    hits = [
        ResearchHit("q1", "official", "uss-qandt-2026", "U.S. Steel Q&T", "$475m Q&T line approved", "strong", 92),
        ResearchHit("q1", "industry-news", "uss-qandt-2026", "U.S. Steel Q&T", "Q&T expansion reported", "partial", 80),
    ]
    fused = fuse_hits(hits)
    assert len(fused) == 1
    assert fused[0].supporting_sources == ("industry-news", "official")
    assert fused[0].best_observation == "$475m Q&T line approved"
    assert fused[0].score == 97


def test_malformed_source_fails_closed():
    query = ResearchQuery("q1", "x", "research")
    bad = ResearchSource("bad", "web", "example", "2026-08-20", "ref", 1, 50)
    with pytest.raises(ValueError, match="invalid_retrieved_at"):
        plan_sources(query, [bad])


def test_boolean_scores_are_rejected():
    query = ResearchQuery("q1", "x", "research")
    bad = ResearchSource("bad", "web", "example", "2026-08-20T00:00:00+00:00", "ref", 1, True)
    with pytest.raises(ValueError, match="invalid_confidence"):
        plan_sources(query, [bad])
