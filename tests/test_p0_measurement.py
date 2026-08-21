from nexus_verticals.p0_measurement import P0MeasurementReport, ProjectMeasurement


def _hydro(**overrides):
    values = dict(
        project_id="hydrotester",
        case_type="hydrotester",
        maturity="replay_tested",
        source_refs=("data/procurement/hydrotester_qualification_matrix_v0_1.json",),
        hazards_tested=3,
        hazards_detected=3,
        unsafe_equivalence_or_selection_blocked=2,
        unresolved_blockers=4,
    )
    values.update(overrides)
    return ProjectMeasurement(**values)


def _can(**overrides):
    values = dict(
        project_id="can-forming",
        case_type="can_forming",
        maturity="replay_tested",
        source_refs=("data/procurement/can_forming_replay_v0_1.json",),
        hazards_tested=3,
        hazards_detected=3,
        unsafe_equivalence_or_selection_blocked=3,
        unresolved_blockers=3,
    )
    values.update(overrides)
    return ProjectMeasurement(**values)


def test_replay_pair_reports_control_detection_without_claiming_roi():
    report = P0MeasurementReport(hydrotester=_hydro(), can_forming=_can())
    assert report.validate() == []
    assert report.replay_detection_rate() == 1.0
    assert report.operational_metrics_available() is False
    assert report.commercial_roi_available() is False


def test_replay_record_cannot_smuggle_human_or_commercial_measurement():
    record = _can(human_corrections=0, commercial_value_usd=1000)
    errors = record.validate()
    assert "replay_tested records cannot claim human, timing, or commercial measurements" in errors


def test_human_reviewed_requires_actual_correction_count():
    record = _hydro(maturity="human_reviewed")
    assert "human_reviewed requires human_corrections" in record.validate()


def test_operational_measurement_requires_time_and_correction_count():
    record = _can(maturity="operationally_measured", human_corrections=1)
    assert "operationally_measured requires correction and elapsed-time measurements" in record.validate()


def test_operational_pair_still_does_not_claim_roi_without_commercial_value():
    report = P0MeasurementReport(
        hydrotester=_hydro(
            maturity="operationally_measured",
            human_corrections=0,
            elapsed_minutes_to_decision=12,
        ),
        can_forming=_can(
            maturity="operationally_measured",
            human_corrections=1,
            elapsed_minutes_to_decision=18,
        ),
    )
    assert report.validate() == []
    assert report.operational_metrics_available() is True
    assert report.commercial_roi_available() is False


def test_hazard_detection_cannot_exceed_tested_hazards():
    assert "hazards_detected cannot exceed hazards_tested" in _hydro(hazards_tested=1, hazards_detected=2).validate()
