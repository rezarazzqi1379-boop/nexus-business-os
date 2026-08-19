from nexus_core.science_network import (
    ExperimentResult,
    ExperimentSpec,
    ExperimentStatus,
    can_start_experiment,
    validate_experiment,
    validate_result,
)


def _spec() -> ExperimentSpec:
    return ExperimentSpec(
        experiment_id="exp-1",
        hypothesis="Qualified project signals improve reply-to-quote progression",
        mechanism="Prioritize counterparties with verified project evidence",
        evidence_refs=("signal:1",),
        project_refs=("hydrotester",),
        smallest_reversible_test="Run a small research-only comparison cohort",
        success_metric="higher qualified-reply rate",
        failure_metric="no improvement or more false positives",
    )


def test_valid_experiment_can_start():
    assert can_start_experiment(_spec())


def test_missing_project_linkage_blocks_experiment():
    spec = ExperimentSpec(
        experiment_id="exp-2",
        hypothesis="h",
        mechanism="m",
        evidence_refs=("e",),
        project_refs=(),
        smallest_reversible_test="test",
        success_metric="success",
        failure_metric="failure",
    )
    assert "invalid_project_refs" in validate_experiment(spec)


def test_terminal_result_requires_observation_and_learning():
    spec = _spec()
    result = ExperimentResult(
        experiment_id="exp-1",
        status=ExperimentStatus.KEEP,
        observation_refs=(),
        measured_outcome="",
        learning="",
    )
    errors = validate_result(spec, result)
    assert "invalid_observation_refs" in errors
    assert "missing_measured_outcome" in errors
    assert "missing_learning" in errors


def test_running_status_is_not_accepted_as_final_result():
    spec = _spec()
    result = ExperimentResult(
        experiment_id="exp-1",
        status=ExperimentStatus.RUNNING,
        observation_refs=("obs:1",),
        measured_outcome="partial",
        learning="pending",
    )
    assert "non_terminal_result_status" in validate_result(spec, result)
