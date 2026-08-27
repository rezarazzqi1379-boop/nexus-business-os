from nexus_core.technology_radar import (
    TechnologyCandidate,
    ranked_candidates,
    recommend,
    research_snapshot,
    value_score,
)


def test_snapshot_is_valid_and_unique():
    items = research_snapshot()
    assert len(items) >= 6
    assert len({item.candidate_id for item in items}) == len(items)
    assert all(not item.validate() for item in items)


def test_research_radar_never_claims_adopted_production_state():
    assert all(item.maturity in {"RESEARCH", "SANDBOX"} for item in research_snapshot())
    assert all(item.decision != "ADOPT_ADAPTER" for item in research_snapshot())


def test_every_candidate_has_acceptance_and_rollback():
    for item in research_snapshot():
        assert item.acceptance_test.strip()
        assert item.rollback.strip()


def test_rank_is_deterministic():
    first = [item.candidate_id for item in ranked_candidates(research_snapshot())]
    second = [item.candidate_id for item in ranked_candidates(tuple(reversed(research_snapshot())))]
    assert first == second


def test_duplicate_candidate_fails_closed():
    item = research_snapshot()[0]
    try:
        ranked_candidates((item, item))
    except ValueError as exc:
        assert "duplicate candidate_id" in str(exc)
    else:
        raise AssertionError("duplicate technology candidate should fail")


def test_invalid_scores_fail_closed():
    item = TechnologyCandidate(
        candidate_id="BAD",
        name="Bad",
        category="test",
        source_url="https://example.invalid",
        observed_at="2026-08-27",
        problem_fit=9,
        implementation_cost=0,
        overlap_risk=0,
        lock_in_risk=0,
        security_risk=0,
        evidence_quality=5,
        acceptance_test="test",
        rollback="rollback",
    )
    try:
        value_score(item)
    except ValueError as exc:
        assert "problem_fit" in str(exc)
    else:
        raise AssertionError("invalid score should fail")


def test_security_ceiling_rejects_even_high_fit_candidate():
    item = TechnologyCandidate(
        candidate_id="RISKY",
        name="Risky",
        category="test",
        source_url="https://example.invalid",
        observed_at="2026-08-27",
        problem_fit=5,
        implementation_cost=0,
        overlap_risk=0,
        lock_in_risk=0,
        security_risk=5,
        evidence_quality=5,
        acceptance_test="test",
        rollback="rollback",
    )
    assert recommend(item) == "REJECT"


def test_score_is_prioritization_not_probability():
    scores = [value_score(item) for item in research_snapshot()]
    assert any(score > 0 for score in scores)
    assert not all(0 <= score <= 1 for score in scores)
