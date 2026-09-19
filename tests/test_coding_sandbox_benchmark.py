from nexus_core.coding_sandbox_benchmark import FrozenCodingTask, RunnerObservation, compare_runner, validate_observation_set


def obs(**overrides):
    data = dict(
        task_id="CODE-001",
        runner_id="candidate",
        repo_snapshot="sha:abc",
        acceptance_passed=True,
        tests_passed=True,
        policy_violations=0,
        security_findings=0,
        cross_project_contamination=0,
        regressions=0,
        human_corrections=1,
        duration_ms=900,
        cost_microusd=900,
        reproducible_runs=3,
    )
    data.update(overrides)
    return RunnerObservation(**data)


def task():
    return FrozenCodingTask("CODE-001", "sha:abc", "all tests + frozen NEXUS evals", "NEXUS_CORE")


def test_candidate_wins_only_when_clean_and_not_worse():
    baseline = obs(runner_id="baseline", human_corrections=2, duration_ms=1000, cost_microusd=1000)
    candidate = obs(runner_id="candidate", human_corrections=1, duration_ms=900, cost_microusd=900)
    result = compare_runner(task(), baseline, candidate)
    assert result.decision == "CANDIDATE_WINS"


def test_fast_but_unsafe_candidate_is_rejected():
    baseline = obs(runner_id="baseline", duration_ms=2000, cost_microusd=2000)
    candidate = obs(runner_id="candidate", duration_ms=100, cost_microusd=10, security_findings=1)
    result = compare_runner(task(), baseline, candidate)
    assert result.decision == "REJECT"


def test_cross_project_contamination_is_hard_failure():
    baseline = obs(runner_id="baseline")
    candidate = obs(runner_id="candidate", cross_project_contamination=1)
    assert compare_runner(task(), baseline, candidate).decision == "REJECT"


def test_external_side_effect_is_hard_failure():
    baseline = obs(runner_id="baseline")
    candidate = obs(runner_id="candidate", external_side_effects=1)
    assert compare_runner(task(), baseline, candidate).decision == "REJECT"


def test_snapshot_mismatch_invalidates_comparison():
    baseline = obs(runner_id="baseline")
    candidate = obs(runner_id="candidate", repo_snapshot="sha:other")
    assert compare_runner(task(), baseline, candidate).decision == "INVALID"


def test_fewer_than_three_clean_runs_cannot_win():
    baseline = obs(runner_id="baseline")
    candidate = obs(runner_id="candidate", reproducible_runs=2, human_corrections=0, duration_ms=100, cost_microusd=10)
    assert compare_runner(task(), baseline, candidate).decision == "KEEP_EXPERIMENTING"


def test_mixed_tradeoffs_require_more_evidence():
    baseline = obs(runner_id="baseline", human_corrections=2, duration_ms=1000, cost_microusd=500)
    candidate = obs(runner_id="candidate", human_corrections=1, duration_ms=800, cost_microusd=900)
    assert compare_runner(task(), baseline, candidate).decision == "KEEP_EXPERIMENTING"


def test_duplicate_runner_ids_are_rejected_in_observation_set():
    errors = validate_observation_set(task(), (obs(runner_id="x"), obs(runner_id="x")))
    assert any("duplicate runner_id" in e for e in errors)
