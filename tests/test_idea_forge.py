from nexus_core.idea_forge import IdeaCandidate, decide_idea, rank_ideas


def idea(**overrides):
    data = dict(
        idea_id="IDEA-001",
        title="Synthetic reversible opportunity",
        domain="COMMERCIAL",
        problem="Repeated measurable problem",
        evidence_refs=("SRC-1",),
        project_refs=("NEXUS_CORE",),
        expected_value=4,
        strategic_fit=4,
        time_to_evidence=4,
        capital_intensity=1,
        execution_difficulty=2,
        risk=2,
        evidence_quality=4,
        reversibility=5,
        acceptance_test="Produce one measurable outcome without external action.",
        rollback="Discard experiment artifacts.",
        revisit_triggers=(),
    )
    data.update(overrides)
    return IdeaCandidate(**data)


def test_high_value_reversible_idea_can_enter_experiment_queue():
    result = decide_idea(idea())
    assert result.state == "EXPERIMENT"


def test_weak_evidence_never_promotes_to_experiment():
    result = decide_idea(idea(evidence_quality=1, expected_value=5, strategic_fit=5))
    assert result.state == "VALIDATE"


def test_high_risk_weak_evidence_rejects():
    result = decide_idea(idea(risk=5, evidence_quality=1))
    assert result.state == "REJECT"


def test_capital_heavy_slow_validation_is_watch_not_auto_build():
    result = decide_idea(idea(capital_intensity=5, time_to_evidence=1))
    assert result.state == "WATCH"


def test_duplicate_ids_fail_closed():
    try:
        rank_ideas((idea(), idea()))
        assert False, "expected duplicate failure"
    except ValueError as exc:
        assert "duplicate idea_id" in str(exc)


def test_no_evidence_is_invalid():
    result = decide_idea(idea(evidence_refs=()))
    assert result.state == "REJECT"
