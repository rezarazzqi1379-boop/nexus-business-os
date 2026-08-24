from nexus_verticals.p0_measurement import P0MeasurementReport, ProjectMeasurement
from nexus_verticals.p0_promotion import evaluate_p0_promotion


def _measured(project_id, case_type):
    return ProjectMeasurement(
        project_id=project_id,
        case_type=case_type,
        maturity="operationally_measured",
        source_refs=(f"benchmark:{project_id}",),
        hazards_tested=3,
        hazards_detected=3,
        unsafe_equivalence_or_selection_blocked=2,
        unresolved_blockers=0,
        human_corrections=0,
        elapsed_minutes_to_decision=10,
    )


def _replay(project_id, case_type):
    return ProjectMeasurement(
        project_id=project_id,
        case_type=case_type,
        maturity="replay_tested",
        source_refs=(f"benchmark:{project_id}",),
        hazards_tested=3,
        hazards_detected=3,
        unsafe_equivalence_or_selection_blocked=2,
        unresolved_blockers=2,
    )


def test_green_ci_style_replay_is_not_enough_for_promotion():
    report = P0MeasurementReport(
        hydrotester=_replay("hydrotester", "hydrotester"),
        can_forming=_replay("can-forming", "can_forming"),
    )
    decision = evaluate_p0_promotion(
        report,
        authority_regressions=0,
        contamination_regressions=0,
        independent_review_complete=True,
    )
    assert decision.promotable is False
    assert "both benchmark cases require operational measurements" in decision.blockers


def test_independent_review_is_a_separate_gate():
    report = P0MeasurementReport(
        hydrotester=_measured("hydrotester", "hydrotester"),
        can_forming=_measured("can-forming", "can_forming"),
    )
    decision = evaluate_p0_promotion(
        report,
        authority_regressions=0,
        contamination_regressions=0,
        independent_review_complete=False,
    )
    assert decision.promotable is False
    assert "independent review is incomplete" in decision.blockers


def test_any_contamination_regression_blocks_promotion():
    report = P0MeasurementReport(
        hydrotester=_measured("hydrotester", "hydrotester"),
        can_forming=_measured("can-forming", "can_forming"),
    )
    decision = evaluate_p0_promotion(
        report,
        authority_regressions=0,
        contamination_regressions=1,
        independent_review_complete=True,
    )
    assert decision.promotable is False
    assert "cross-project contamination regression count must be zero" in decision.blockers


def test_promotion_possible_only_when_all_current_gates_are_satisfied():
    report = P0MeasurementReport(
        hydrotester=_measured("hydrotester", "hydrotester"),
        can_forming=_measured("can-forming", "can_forming"),
    )
    decision = evaluate_p0_promotion(
        report,
        authority_regressions=0,
        contamination_regressions=0,
        independent_review_complete=True,
    )
    assert decision.promotable is True
    assert decision.blockers == ()
