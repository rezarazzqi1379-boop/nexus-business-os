import pytest

from nexus_core.experimentation import ExperimentSpec, record_result, select_experiments, validate_experiment


def spec(**overrides):
    values = dict(
        experiment_id="exp:research-to-code:1",
        domain="coding_learning",
        hypothesis="A primary-source technique can improve an active NEXUS implementation.",
        mechanism="Translate one technique into a reversible regression-backed patch.",
        evidence_class="hypothesis",
        evidence_refs=("source:primary:1",),
        success_metric="A regression or implementation test passes and addresses a current requirement.",
        failure_metric="No measurable implementation benefit or only passive summary is produced.",
        reversibility=True,
    )
    values.update(overrides)
    return ExperimentSpec(**values)


def test_valid_experiment_is_accepted():
    assert validate_experiment(spec()) == []


def test_missing_metrics_fail_closed():
    errors = validate_experiment(spec(success_metric=""))
    assert "success_metric is required" in errors


def test_selector_prefers_reversible_and_better_evidence():
    items = (
        spec(experiment_id="exp:hypothesis", evidence_class="hypothesis", reversibility=True),
        spec(experiment_id="exp:fact", evidence_class="fact", reversibility=True),
        spec(experiment_id="exp:irreversible", evidence_class="fact", reversibility=False),
    )
    selected = select_experiments(items)
    assert [item.experiment_id for item in selected] == ["exp:fact", "exp:hypothesis", "exp:irreversible"]


def test_result_requires_observed_evidence():
    with pytest.raises(ValueError):
        record_result(spec(), passed=True, observed_signal="", evidence_refs=("test:1",))
    with pytest.raises(ValueError):
        record_result(spec(), passed=True, observed_signal="improved", evidence_refs=())


def test_failed_experiment_does_not_auto_kill_without_learning():
    result = record_result(spec(), passed=False, observed_signal="No measurable improvement.", evidence_refs=("ci:run:1",))
    assert result.status == "failed"
    assert result.recommendation == "modify"
