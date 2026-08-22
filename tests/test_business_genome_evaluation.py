from nexus_verticals.business_genome import Decision
from nexus_verticals.business_genome_evaluation import (
    PromotionEvidencePolicy,
    ShadowDecisionObservation,
    evaluate_shadow,
    promotion_evidence_gaps,
)


def obs(
    oid: str,
    case: str,
    recommendation: Decision,
    human: Decision | None = None,
    outcome: bool | None = None,
    stage: str | None = None,
    safety: bool = False,
):
    return ShadowDecisionObservation(
        observation_id=oid,
        project_id=f"project:{case}",
        case_type=case,
        recommendation=recommendation,
        human_decision=human,
        outcome_success=outcome,
        outcome_stage=stage,
        safety_violation=safety,
        source_ref=f"source:{oid}",
    )


def test_metrics_stay_undefined_without_labels():
    report = evaluate_shadow([obs("1", "hydrotester", Decision.RESEARCH)])
    assert report.recommendation_human_agreement is None
    assert report.pursue_outcome_precision is None
    assert report.human_labeled == 0
    assert report.outcome_labeled == 0
    assert report.final_outcome_labeled == 0


def test_stage_success_does_not_masquerade_as_order_precision():
    rows = [
        obs("1", "kcl", Decision.PURSUE, Decision.PURSUE, True, "reply"),
        obs("2", "kcl", Decision.PURSUE, Decision.PURSUE),
    ]
    report = evaluate_shadow(rows)
    assert report.stage_successes == 1
    assert report.final_outcome_labeled == 0
    assert report.pursue_outcome_precision is None


def test_report_uses_only_final_outcomes_for_pursue_precision():
    rows = [
        obs("1", "hydrotester", Decision.RESEARCH, Decision.RESEARCH),
        obs("2", "can-forming", Decision.PURSUE, Decision.PURSUE, True, "order"),
        obs("3", "can-forming", Decision.PURSUE, Decision.RESEARCH, False, "contract"),
    ]
    report = evaluate_shadow(rows)
    assert report.recommendation_human_agreement == 2 / 3
    assert report.pursue_outcome_precision == 1 / 2
    assert report.pursue_false_positives == 1
    assert report.distinct_case_types == 2


def test_invalid_observation_is_excluded_fail_closed():
    bad = ShadowDecisionObservation(
        observation_id="",
        project_id="p",
        case_type="hydrotester",
        recommendation=Decision.RESEARCH,
        source_ref="source:bad",
    )
    report = evaluate_shadow([bad])
    assert report.total_observations == 0


def test_outcome_requires_stage():
    bad = obs("bad", "kcl", Decision.PURSUE, Decision.PURSUE, True)
    report = evaluate_shadow([bad])
    assert report.total_observations == 0


def test_promotion_policy_requires_final_business_outcomes():
    report = evaluate_shadow([
        obs("1", "hydrotester", Decision.RESEARCH, Decision.RESEARCH),
        obs("2", "can-forming", Decision.RESEARCH, Decision.RESEARCH),
        obs("3", "kcl", Decision.PURSUE, Decision.PURSUE, True, "reply"),
        obs("4", "supplier", Decision.RESEARCH, Decision.RESEARCH),
        obs("5", "kcl", Decision.PURSUE, Decision.PURSUE),
    ])
    gaps = promotion_evidence_gaps(report)
    assert "insufficient_observations" not in gaps
    assert "insufficient_human_decisions" not in gaps
    assert "insufficient_final_business_outcomes" in gaps


def test_safety_violation_is_always_a_promotion_gap():
    rows = [
        obs("1", "hydrotester", Decision.RESEARCH, Decision.RESEARCH, True, "order"),
        obs("2", "can-forming", Decision.PURSUE, Decision.PURSUE, True, "order"),
        obs("3", "hydrotester", Decision.RESEARCH, Decision.RESEARCH, False, "contract"),
        obs("4", "can-forming", Decision.PURSUE, Decision.PURSUE, True, "order"),
        obs("5", "hydrotester", Decision.RESEARCH, Decision.RESEARCH, False, "contract", safety=True),
    ]
    report = evaluate_shadow(rows)
    gaps = promotion_evidence_gaps(
        report,
        PromotionEvidencePolicy(
            min_observations=5,
            min_case_types=2,
            min_human_labeled=3,
            min_final_outcome_labeled=3,
        ),
    )
    assert "safety_violation_present" in gaps
