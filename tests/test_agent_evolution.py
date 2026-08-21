import math

import pytest

from nexus.agent_evolution import (
    EvaluationResult,
    FailureObservation,
    decide_evolution,
    deduplicate_observations,
    propose_from_failure,
)


def observation(**overrides):
    data = dict(
        observation_id="obs-1",
        component="research-search-tool",
        failure_mode="poor source selection",
        evidence_refs=("trace://run/1",),
        severity=3,
    )
    data.update(overrides)
    return FailureObservation(**data)


def proposal():
    return propose_from_failure(
        observation(),
        proposal_id="prop-1",
        hypothesis="source-quality rubric improves precision",
        change_summary="add source-quality prefilter",
        expected_metric="verified-answer precision",
    )


def test_observation_requires_evidence():
    with pytest.raises(ValueError):
        observation(evidence_refs=())


def test_observation_rejects_non_integer_severity():
    with pytest.raises(ValueError):
        observation(severity=2.5)


def test_proposal_is_traceable_to_failure():
    item = proposal()
    assert item.source_observations == ("obs-1",)


def test_proposal_rejects_nonfinite_regression_budget():
    with pytest.raises(ValueError):
        propose_from_failure(
            observation(),
            proposal_id="prop-1",
            hypothesis="test",
            change_summary="test",
            expected_metric="precision",
        ).__class__(
            proposal_id="prop-2",
            component="research-search-tool",
            hypothesis="test",
            change_summary="test",
            source_observations=("obs-1",),
            expected_metric="precision",
            max_regression=math.inf,
        )


def test_missing_eval_evidence_fails_closed():
    result = EvaluationResult("prop-1", 0.70, 0.90)
    decision = decide_evolution(proposal(), result)
    assert decision.decision == "reject"
    assert not decision.requires_human_approval


@pytest.mark.parametrize("bad_score", [math.nan, math.inf, -math.inf, "0.9", True])
def test_evaluation_rejects_malformed_or_nonfinite_scores(bad_score):
    with pytest.raises(ValueError):
        EvaluationResult("prop-1", 0.70, bad_score, evidence_refs=("eval://1",))


def test_evaluation_rejects_blank_evidence_ref():
    with pytest.raises(ValueError):
        EvaluationResult("prop-1", 0.70, 0.90, evidence_refs=(" ",))


def test_safety_regression_rejects_even_with_gain():
    result = EvaluationResult(
        "prop-1", 0.70, 0.95,
        safety_regressions=("external-send gate bypass",),
        evidence_refs=("eval://1",),
    )
    assert decide_evolution(proposal(), result).decision == "reject"


def test_weak_gain_stays_experimental():
    result = EvaluationResult("prop-1", 0.70, 0.705, evidence_refs=("eval://1",))
    assert decide_evolution(proposal(), result, minimum_gain=0.01).decision == "experiment"


def test_meaningful_gain_is_only_promotable_not_auto_promoted():
    result = EvaluationResult("prop-1", 0.70, 0.80, evidence_refs=("eval://1",))
    decision = decide_evolution(proposal(), result)
    assert decision.decision == "promotable"
    assert decision.requires_human_approval


@pytest.mark.parametrize("bad_gain", [-0.01, math.nan, math.inf, "0.01", True])
def test_minimum_gain_must_be_finite_non_negative(bad_gain):
    result = EvaluationResult("prop-1", 0.70, 0.80, evidence_refs=("eval://1",))
    with pytest.raises(ValueError):
        decide_evolution(proposal(), result, minimum_gain=bad_gain)


def test_mismatched_evaluation_rejected():
    result = EvaluationResult("other", 0.70, 0.90, evidence_refs=("eval://1",))
    assert decide_evolution(proposal(), result).decision == "reject"


def test_dedup_keeps_highest_severity():
    low = observation(observation_id="low", severity=1)
    high = observation(observation_id="high", severity=5)
    unique = deduplicate_observations([low, high])
    assert [item.observation_id for item in unique] == ["high"]


def test_dedup_rejects_wrong_runtime_type():
    with pytest.raises(ValueError):
        deduplicate_observations([observation(), "not-an-observation"])
