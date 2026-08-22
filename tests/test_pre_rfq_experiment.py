from nexus_verticals.pre_rfq_experiment import (
    PreRfqExperimentObservation,
    experiment_promotion_gaps,
    summarize_pre_rfq_experiment,
)


def test_no_outcomes_produces_no_fake_rates():
    metrics = summarize_pre_rfq_experiment((
        PreRfqExperimentObservation(
            observation_id="o1",
            project_id="p1",
            baseline_would_send=True,
            candidate_would_send=False,
            actual_sent=True,
            clarification_rework_observed=None,
            source_ref="test:o1",
        ),
    ))
    assert metrics.observed_outcomes == 0
    assert metrics.baseline_rework_rate is None
    assert metrics.candidate_rework_rate is None
    assert "missing_comparable_rework_rates" in experiment_promotion_gaps(metrics)


def test_observed_rates_use_explicit_denominators():
    rows = (
        PreRfqExperimentObservation("o1", "p1", True, True, True, True, "e1"),
        PreRfqExperimentObservation("o2", "p2", True, True, True, False, "e2"),
        PreRfqExperimentObservation("o3", "p3", True, False, True, True, "e3"),
    )
    metrics = summarize_pre_rfq_experiment(rows)
    assert metrics.baseline_sent_observed == 3
    assert metrics.baseline_rework_observed == 2
    assert metrics.baseline_rework_rate == 2 / 3
    assert metrics.candidate_sent_observed == 2
    assert metrics.candidate_rework_observed == 1
    assert metrics.candidate_rework_rate == 1 / 2
    assert metrics.paired_rate_delta == (1 / 2) - (2 / 3)


def test_conflicting_duplicate_observation_fails_closed():
    a = PreRfqExperimentObservation("same", "p1", True, True, True, False, "e1")
    b = PreRfqExperimentObservation("same", "p1", True, False, True, False, "e1")
    try:
        summarize_pre_rfq_experiment((a, b))
    except ValueError as exc:
        assert "conflicting duplicate" in str(exc)
    else:
        raise AssertionError("expected conflicting duplicate to fail closed")
