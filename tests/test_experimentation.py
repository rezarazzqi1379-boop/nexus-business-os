import pytest
from hypothesis import given, strategies as st

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


def test_non_string_or_duplicate_refs_fail_closed():
    assert "evidence_refs requires unique non-empty string references" in validate_experiment(spec(evidence_refs=(123,)))
    assert "evidence_refs requires unique non-empty string references" in validate_experiment(spec(evidence_refs=("ref:1", "ref:1")))


_malformed_scalar = st.one_of(
    st.none(),
    st.integers(),
    st.floats(allow_nan=True, allow_infinity=True),
    st.lists(st.integers(), max_size=3),
    st.dictionaries(st.text(max_size=4), st.integers(), max_size=3),
)


@given(value=_malformed_scalar)
def test_validator_never_raises_for_malformed_evidence_class(value):
    errors = validate_experiment(spec(evidence_class=value))
    assert isinstance(errors, list)
    assert "evidence_class must be supported" in errors


@given(value=_malformed_scalar)
def test_validator_never_raises_for_malformed_status(value):
    errors = validate_experiment(spec(status=value))
    assert isinstance(errors, list)
    assert "status must be supported" in errors


@given(value=_malformed_scalar)
def test_validator_never_raises_for_malformed_reversibility(value):
    errors = validate_experiment(spec(reversibility=value))
    assert isinstance(errors, list)
    assert "reversibility must be boolean" in errors


@given(
    refs=st.one_of(
        st.none(),
        st.integers(),
        st.lists(st.one_of(st.text(max_size=8), st.integers()), max_size=5),
        st.tuples(st.one_of(st.none(), st.integers(), st.just(""))),
    )
)
def test_validator_never_raises_for_malformed_reference_collections(refs):
    errors = validate_experiment(spec(evidence_refs=refs))
    assert isinstance(errors, list)
    assert "evidence_refs requires unique non-empty string references" in errors


@given(value=_malformed_scalar)
def test_record_result_rejects_non_boolean_passed(value):
    with pytest.raises(ValueError, match="passed must be boolean"):
        record_result(spec(), passed=value, observed_signal="measured", evidence_refs=("ci:run:1",))
