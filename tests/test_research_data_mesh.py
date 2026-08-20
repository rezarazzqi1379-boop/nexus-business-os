import pytest

from nexus_core.research_data_mesh import (
    ResearchHit,
    ResearchQuery,
    ResearchSource,
    benchmark_retrieval,
    fuse_hits,
    plan_sources,
)


def test_plans_bounded_diverse_high_confidence_sources():
    query = ResearchQuery("q1", "OCTG heat treatment expansion", "commercial-intelligence", max_sources=2)
    sources = [
        ResearchSource("official-a", "official", "ussteel.com", "2026-08-20T00:00:00+00:00", "url:https://ussteel.com/x", 300, 95),
        ResearchSource("official-b", "official", "tenaris.com", "2026-08-20T00:00:01+00:00", "url:https://tenaris.com/x", 100, 94),
        ResearchSource("academic", "academic", "scispace", "2026-08-20T00:00:02+00:00", "connector:scispace:1", 180, 86),
    ]
    plan = plan_sources(query, sources)
    assert plan.selected_sources == ("official-a", "academic")
    assert plan.rejected_sources == ("official-b",)


def test_fuses_duplicate_claims_with_corroboration_without_hiding_raw_evidence():
    hits = [
        ResearchHit("q1", "official", "uss-qandt-2026", "U.S. Steel Q&T", "$475m Q&T line approved", "strong", 92),
        ResearchHit("q1", "industry-news", "uss-qandt-2026", "U.S. Steel Q&T", "Q&T expansion reported", "partial", 80),
    ]
    fused = fuse_hits(hits)
    assert len(fused) == 1
    assert fused[0].supporting_sources == ("industry-news", "official")
    assert fused[0].refuting_sources == ()
    assert fused[0].best_observation == "$475m Q&T line approved"
    assert fused[0].score == 97
    assert fused[0].contradiction is False


def test_contradiction_is_preserved_and_penalized_not_silently_merged():
    hits = [
        ResearchHit("q1", "official", "claim", "Capacity", "capacity approved", "strong", 90, "support"),
        ResearchHit("q1", "regulator", "claim", "Capacity", "permit not granted", "strong", 88, "refute"),
    ]
    fused = fuse_hits(hits)[0]
    assert fused.contradiction is True
    assert fused.supporting_sources == ("official",)
    assert fused.refuting_sources == ("regulator",)
    assert fused.score == 75


def test_benchmark_does_not_call_contradiction_an_improvement():
    hits = [
        ResearchHit("q1", "a", "claim", "Claim", "yes", "strong", 90, "support"),
        ResearchHit("q1", "b", "claim", "Claim", "no", "strong", 88, "refute"),
    ]
    result = benchmark_retrieval(hits)
    assert result.single_source_score == 90
    assert result.multi_source_score == 75
    assert result.contradiction_detected is True
    assert result.improved is False


def test_benchmark_can_show_corroboration_gain_without_claiming_llm_quality():
    hits = [
        ResearchHit("q1", "a", "claim", "Claim", "confirmed", "strong", 90, "support"),
        ResearchHit("q1", "b", "claim", "Claim", "also confirmed", "partial", 80, "support"),
    ]
    result = benchmark_retrieval(hits)
    assert result.multi_source_score == 95
    assert result.improved is True


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


def test_invalid_stance_fails_closed():
    bad = ResearchHit("q1", "a", "claim", "Claim", "x", "strong", 90, "maybe")
    with pytest.raises(ValueError, match="invalid_stance"):
        fuse_hits([bad])
