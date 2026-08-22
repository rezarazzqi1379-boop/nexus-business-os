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
    safety: bool = False,
):
    return ShadowDecisionObservation(
        observation_id=oid,
        project_id=f"project:{case}",
        case_type=case,
        recommendation=recommendation,
        human_decision=human,
        outcome_success=outcome,
        safety_violation=safety,
        source_ref=f"source:{oid}",
    )


def test_metrics_stay_undefined_without_labels():
    report = evaluate_shadow([obs("1", "hydrotester", Decision.RESEARCH)])
    assert report.recommendation_human_agreement is None
    assert report.pursue_outcome_precision is None
    assert report.human_labeled == 0
    assert report.outcome_labeled == 0


def test_report_uses_only_observed_denominators():
    rows = [
        obs("1", "hydrotester", Decision.RESEARCH, Decision.RESEARCH),
        obs("2", "can-forming", Decision.PURSUE, Decision.PURSUE, True),
        obs("3", "can-forming", Decision.PURSUE, Decision.RESEARCH, False),
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


def test_promotion_policy_reports_gaps_instead_of_auto_promoting():
    report = evaluate_shadow([
        obs("1", "hydrotester", Decision.RESEARCH, Decision.RESEARCH),
        obs("2", "can-forming", Decision.RESEARCH, Decision.RESEARCH),
    ])
    gaps = promotion_evidence_gaps(report)
    assert "insufficient_observations" in gaps
    assert "insufficient_human_decisions" in gaps
    assert "insufficient_real_outcomes" in gaps


def test_safety_violation_is_always_a_promotion_gap():
    rows = [
        obs("1", "hydrotester", Decision.RESEARCH, Decision.RESEARCH, True),
        obs("2", "can-forming", Decision.PURSUE, Decision.PURSUE, True),
        obs("3", "hydrotester", Decision.RESEARCH, Decision.RESEARCH, False),
        obs("4", "can-forming", Decision.PURSUE, Decision.PURSUE, True),
        obs("5", "hydrotester", Decision.RESEARCH, Decision.RESEARCH, False, safety=True),
    ]
    report = evaluate_shadow(rows)
    gaps = promotion_evidence_gaps(
        report,
        PromotionEvidencePolicy(
            min_observations=5,
            min_case_types=2,
            min_human_labeled=3,
            min_outcome_labeled=3,
        ),
    )
    assert "safety_violation_present" in gaps
