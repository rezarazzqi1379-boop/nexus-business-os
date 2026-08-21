import pytest

from nexus_core.research_data_mesh import (
    ResearchHit,
    ResearchQuery,
    ResearchSource,
    ResearchOutcome,
    RetrievalAttempt,
    benchmark_retrieval,
    condition_sources_on_connector_health,
    fuse_hits,
    plan_sources,
    schedule_retrieval,
    summarize_source_outcomes,
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


def test_equal_confidence_prefers_fresher_evidence_before_latency():
    query = ResearchQuery("q1", "latest supplier state", "commercial-intelligence", max_sources=1)
    sources = [
        ResearchSource("stale-fast", "official", "old.example", "2026-08-19T00:00:00+00:00", "ref:old", 10, 90),
        ResearchSource("fresh-slow", "official", "new.example", "2026-08-21T00:00:00+00:00", "ref:new", 1000, 90),
    ]
    plan = plan_sources(query, sources)
    assert plan.selected_sources == ("fresh-slow",)
    assert plan.rejected_sources == ("stale-fast",)


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


def test_correlated_aliases_do_not_create_false_corroboration_bonus():
    hits = [
        ResearchHit("q1", "vendor-site", "claim", "Pressure", "120 MPa", "strong", 90, independence_key="vendor-a"),
        ResearchHit("q1", "vendor-marketplace", "claim", "Pressure", "120 MPa repost", "partial", 80, independence_key="vendor-a"),
    ]
    result = benchmark_retrieval(hits)
    assert result.source_count == 1
    assert result.single_source_score == 90
    assert result.multi_source_score == 90
    assert result.improved is False


def test_invalid_independence_key_fails_closed():
    bad = ResearchHit("q1", "a", "claim", "Claim", "x", "strong", 90, independence_key=" ")
    with pytest.raises(ValueError, match="invalid_independence_key"):
        fuse_hits([bad])


def test_connector_failures_are_excluded_and_degraded_results_are_capped():
    sources = [
        ResearchSource("ok", "official", "ok.example", "2026-08-21T00:00:00+00:00", "ref:ok", 10, 95),
        ResearchSource("partial", "web", "partial.example", "2026-08-21T00:00:00+00:00", "ref:partial", 10, 95),
        ResearchSource("stale", "crm", "stale.example", "2026-08-20T00:00:00+00:00", "ref:stale", 10, 95),
        ResearchSource("down", "email", "down.example", "2026-08-21T00:00:00+00:00", "ref:down", 10, 95),
    ]
    attempts = [
        RetrievalAttempt("ok", "success", 25, 3),
        RetrievalAttempt("partial", "partial", 400, 1),
        RetrievalAttempt("stale", "stale", 100, 2),
        RetrievalAttempt("down", "timeout", 2000, 0, "timeout"),
    ]
    conditioned = condition_sources_on_connector_health(sources, attempts)
    by_id = {source.source_id: source for source in conditioned.usable_sources}
    assert set(by_id) == {"ok", "partial", "stale"}
    assert by_id["ok"].confidence == 95
    assert by_id["partial"].confidence == 70
    assert by_id["stale"].confidence == 50
    assert conditioned.excluded_sources == ("down",)
    assert conditioned.degraded_sources == ("partial", "stale")


def test_connector_health_missing_attempt_fails_closed():
    source = ResearchSource("a", "official", "a.example", "2026-08-21T00:00:00+00:00", "ref:a", 10, 90)
    with pytest.raises(ValueError, match="missing_retrieval_attempt"):
        condition_sources_on_connector_health([source], [])


def test_failed_attempt_cannot_claim_evidence():
    source = ResearchSource("a", "official", "a.example", "2026-08-21T00:00:00+00:00", "ref:a", 10, 90)
    bad = RetrievalAttempt("a", "timeout", 1000, 1, "timeout")
    with pytest.raises(ValueError, match="failed_attempt_cannot_claim_evidence"):
        condition_sources_on_connector_health([source], [bad])


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


def test_fusion_rejects_hits_from_different_queries():
    hits = [
        ResearchHit("q1", "a", "same-key", "Claim", "first query", "strong", 90),
        ResearchHit("q2", "b", "same-key", "Claim", "second query", "strong", 90),
    ]
    with pytest.raises(ValueError, match="fuse_requires_one_query"):
        fuse_hits(hits)


def test_source_plan_prefers_distinct_publishers_before_correlated_fill():
    query = ResearchQuery("q1", "supplier evidence", "commercial-intelligence", max_sources=3)
    sources = [
        ResearchSource("a1", "official", "same.example", "2026-08-20T00:00:00+00:00", "ref:a1", 10, 99),
        ResearchSource("a2", "news", "same.example", "2026-08-20T00:00:00+00:00", "ref:a2", 10, 98),
        ResearchSource("b1", "official", "independent.example", "2026-08-20T00:00:00+00:00", "ref:b1", 10, 90),
    ]
    plan = plan_sources(query, sources)
    assert plan.selected_sources[:2] == ("a1", "b1")
    assert plan.selected_sources[2] == "a2"


def test_retrieval_schedule_enforces_bounded_parallel_waves():
    query = ResearchQuery("q1", "wide search", "research", max_sources=5)
    sources = [
        ResearchSource(
            f"s{i}",
            "web",
            f"d{i}.example",
            "2026-08-20T00:00:00+00:00",
            f"ref:{i}",
            i,
            90 - i,
        )
        for i in range(5)
    ]
    schedule = schedule_retrieval(plan_sources(query, sources), max_parallel=2)
    assert tuple(map(len, schedule.waves)) == (2, 2, 1)
    assert schedule.max_parallel == 2

    with pytest.raises(ValueError, match="invalid_max_parallel"):
        schedule_retrieval(plan_sources(query, sources), max_parallel=20)


def test_source_learning_requires_evidence_and_never_mutates_trust_automatically():
    learned = summarize_source_outcomes([
        ResearchOutcome("exa", True, 100),
        ResearchOutcome("exa", True, 120),
        ResearchOutcome("exa", True, 80),
        ResearchOutcome("slow", False, 900),
        ResearchOutcome("slow", True, 1100),
    ])
    assert learned[0].source_id == "exa"
    assert learned[0].recommendation == "prefer"
    assert learned[0].average_latency_ms == 100
    assert learned[1].recommendation == "insufficient_evidence"
