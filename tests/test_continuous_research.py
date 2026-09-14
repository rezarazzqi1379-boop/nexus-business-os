import pytest

from continuous_research import ResearchHit, ResearchTopic, compile_queries, run_research_cycle


def topic():
    return ResearchTopic("t1", "P1", "Agent research", ("security", "evaluation"), 24, 2, 2)


def hit(query, **changes):
    values = dict(provider_id="exa", query=query, url="https://official.example/a", title="A",
                  snippet="Evidence", retrieved_at="2026-09-12T00:00:00+00:00", source_tier="official")
    values.update(changes)
    return ResearchHit(**values)


def test_cycle_deduplicates_and_only_proposes_on_independent_convergence():
    queries = compile_queries(topic())
    hits = (hit(queries[0]), hit(queries[1], url="https://research.example/b", source_tier="primary"))
    cycle = run_research_cycle(topic(), {"exa": hits}, run_id="run-1", candidate_findings=("Use commit gates",))
    assert len(cycle.unique_hits) == 2
    assert len(cycle.proposals) == 1
    assert cycle.proposals[0].auto_apply is False
    assert cycle.proposals[0].status == "EXPERIMENT_ONLY"


def test_one_domain_cannot_trigger_improvement_proposal():
    query = compile_queries(topic())[0]
    cycle = run_research_cycle(topic(), {"exa": (hit(query),)}, run_id="run-1",
                               candidate_findings=("Uncorroborated",))
    assert cycle.proposals == ()


def test_provider_cannot_exceed_budget_or_spoof_attribution():
    query = compile_queries(topic())[0]
    with pytest.raises(ValueError, match="attribution"):
        run_research_cycle(topic(), {"other": (hit(query),)}, run_id="run")
    too_many = tuple(hit(query, url=f"https://x{i}.example/a") for i in range(5))
    with pytest.raises(ValueError, match="budget"):
        run_research_cycle(topic(), {"exa": too_many}, run_id="run")


def test_unplanned_query_is_rejected():
    with pytest.raises(ValueError, match="outside_plan"):
        run_research_cycle(topic(), {"exa": (hit("surprise"),)}, run_id="run")

