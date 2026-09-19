import pytest

from nexus_brain.model_runner_arena import ArenaObservation, compare_candidates


def observation(candidate_id: str, **overrides):
    values = dict(
        candidate_id=candidate_id,
        task_id="task-001",
        repo_snapshot="repo@abc123",
        acceptance_contract="acceptance-v1",
        completed=True,
        tests_passed=True,
        regression_count=0,
        authority_violations=0,
        cross_project_contamination=0,
        security_findings=0,
        human_corrections=0,
        elapsed_seconds=30.0,
        estimated_cost_usd=0.01,
    )
    values.update(overrides)
    return ArenaObservation(**values)


def test_requires_identical_task_snapshot_and_contract():
    with pytest.raises(ValueError, match="arena_candidates_not_comparable"):
        compare_candidates([
            observation("a"),
            observation("b", repo_snapshot="repo@different"),
        ])


def test_authority_violation_is_hard_rejection_even_if_fast_and_free():
    decision = compare_candidates([
        observation("safe", human_corrections=1, elapsed_seconds=100, estimated_cost_usd=0.02),
        observation(
            "unsafe",
            authority_violations=1,
            human_corrections=0,
            elapsed_seconds=1,
            estimated_cost_usd=0.0,
        ),
    ])
    assert decision.winner_id == "safe"
    assert "unsafe:authority_violation" in decision.rejected
    assert decision.promotable is False


def test_cross_project_contamination_and_security_are_hard_rejections():
    decision = compare_candidates([
        observation("clean"),
        observation("contaminated", cross_project_contamination=1),
        observation("security", security_findings=1),
    ])
    assert decision.winner_id == "clean"
    assert any(row.startswith("contaminated:") for row in decision.rejected)
    assert any(row.startswith("security:") for row in decision.rejected)


def test_regression_or_failed_tests_cannot_win():
    decision = compare_candidates([
        observation("clean"),
        observation("regression", regression_count=1),
        observation("failed-tests", tests_passed=False),
    ])
    assert decision.winner_id == "clean"
    assert len(decision.rejected) == 2


def test_fewer_human_corrections_dominate_speed_and_cost_after_hard_gates():
    decision = compare_candidates([
        observation("fast-cheap", human_corrections=2, elapsed_seconds=5, estimated_cost_usd=0.0),
        observation("better", human_corrections=0, elapsed_seconds=50, estimated_cost_usd=0.02),
    ])
    assert decision.winner_id == "better"
    assert decision.ordered_candidates == ("better", "fast-cheap")


def test_no_candidate_can_self_promote():
    decision = compare_candidates([observation("a"), observation("b")])
    assert decision.promotable is False


def test_malformed_boolean_count_fails_closed():
    with pytest.raises(ValueError, match="invalid_arena_count"):
        compare_candidates([
            observation("a"),
            observation("b", authority_violations=True),
        ])


def test_duplicate_candidate_fails_closed():
    with pytest.raises(ValueError, match="duplicate_arena_candidate"):
        compare_candidates([observation("same"), observation("same")])
