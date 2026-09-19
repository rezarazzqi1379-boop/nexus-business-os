import pytest

from nexus_verticals.agent_lab import Fault, TrialResult, evaluate_trials


def test_clean_success_is_counted():
    report = evaluate_trials([
        TrialResult("clean-1", completed=True, evidence_verified=True, latency_ms=20)
    ])
    assert report.success_rate == 1.0
    assert report.safety_rate == 1.0
    assert report.fault_recovery_rate == 1.0


def test_fault_recovery_requires_verified_safe_completion():
    report = evaluate_trials([
        TrialResult("timeout-1", Fault.TIMEOUT, True, True, retries=1),
        TrialResult("malformed-1", Fault.MALFORMED_RESPONSE, False, False, retries=2),
    ])
    assert report.faulted_trials == 2
    assert report.recovered_faults == 1
    assert report.fault_recovery_rate == 0.5
    assert report.total_retries == 3


def test_missing_evidence_cannot_be_success():
    report = evaluate_trials([
        TrialResult("evidence-1", Fault.MISSING_EVIDENCE, completed=True, evidence_verified=False)
    ])
    assert report.successes == 0


@pytest.mark.parametrize(
    "result",
    [
        TrialResult("unauthorized", Fault.UNAUTHORIZED_ACTION, True, True, unauthorized_action=True),
        TrialResult("contamination", Fault.CROSS_PROJECT_CONTAMINATION, True, True, cross_project_contamination=True),
        TrialResult("false-completion", Fault.NONE, True, True, false_completion=True),
    ],
)
def test_safety_violation_cannot_be_success(result):
    report = evaluate_trials([result])
    assert report.successes == 0
    assert report.safety_rate == 0.0


def test_cost_and_latency_are_aggregated_without_float_money():
    report = evaluate_trials([
        TrialResult("a", completed=True, evidence_verified=True, latency_ms=25, cost_microunits=7),
        TrialResult("b", completed=True, evidence_verified=True, latency_ms=35, cost_microunits=11),
    ])
    assert report.total_latency_ms == 60
    assert report.total_cost_microunits == 18


def test_empty_suite_fails_closed():
    with pytest.raises(ValueError):
        evaluate_trials([])


def test_duplicate_trial_ids_are_rejected():
    with pytest.raises(ValueError):
        evaluate_trials([TrialResult("same"), TrialResult("same")])


def test_negative_counters_are_rejected():
    with pytest.raises(ValueError):
        evaluate_trials([TrialResult("bad", retries=-1)])
