from nexus_core.adoption_gate import ExperimentEvidence, evaluate_adoption
from nexus_core.technology_radar import TechnologyCandidate


def candidate() -> TechnologyCandidate:
    return TechnologyCandidate(
        candidate_id="TECH-X",
        name="Candidate X",
        category="adapter",
        source_url="https://example.invalid/docs",
        observed_at="2026-08-27",
        problem_fit=5,
        implementation_cost=2,
        overlap_risk=1,
        lock_in_risk=1,
        security_risk=2,
        evidence_quality=5,
        acceptance_test="one bounded vertical",
        rollback="remove adapter",
        maturity="SANDBOX",
        decision="EXPERIMENT",
    )


def evidence(**overrides) -> ExperimentEvidence:
    values = dict(
        candidate_id="TECH-X",
        acceptance_passed=True,
        policy_violations=0,
        security_findings=0,
        regressions=0,
        cross_project_contamination=0,
        human_corrections=1,
        baseline_human_corrections=3,
        duration_ms=900,
        baseline_duration_ms=1200,
        cost_microusd=100,
        baseline_cost_microusd=150,
        rollback_tested=True,
        reproducible_runs=3,
        authority_expansion_required=False,
        production_dependency_required=False,
    )
    values.update(overrides)
    return ExperimentEvidence(**values)


def test_clean_reproducible_measured_improvement_can_adopt_only_as_adapter():
    result = evaluate_adoption(candidate(), evidence())
    assert result.decision == "ADOPT_ADAPTER"
    assert any("adapter only" in reason for reason in result.reasons)


def test_one_policy_violation_hard_rejects_even_if_faster_and_cheaper():
    assert evaluate_adoption(candidate(), evidence(policy_violations=1)).decision == "REJECT"


def test_cross_project_contamination_hard_rejects():
    assert evaluate_adoption(candidate(), evidence(cross_project_contamination=1)).decision == "REJECT"


def test_authority_expansion_hard_rejects():
    assert evaluate_adoption(candidate(), evidence(authority_expansion_required=True)).decision == "REJECT"


def test_untested_rollback_hard_rejects():
    assert evaluate_adoption(candidate(), evidence(rollback_tested=False)).decision == "REJECT"


def test_less_than_three_clean_runs_keeps_experimenting():
    assert evaluate_adoption(candidate(), evidence(reproducible_runs=2)).decision == "KEEP_EXPERIMENTING"


def test_safe_but_no_better_candidate_is_watch_not_adopted():
    result = evaluate_adoption(
        candidate(),
        evidence(
            human_corrections=3,
            baseline_human_corrections=3,
            duration_ms=1200,
            baseline_duration_ms=1200,
            cost_microusd=150,
            baseline_cost_microusd=150,
        ),
    )
    assert result.decision == "WATCH"


def test_identity_mismatch_fails_closed():
    assert evaluate_adoption(candidate(), evidence(candidate_id="OTHER")).decision == "REJECT"
