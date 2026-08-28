from nexus_core.vertical_acceptance import (
    TraceEnvelope,
    VerticalAcceptancePolicy,
    VerticalRunObservation,
    assess_vertical_runs,
)


def _policy() -> VerticalAcceptancePolicy:
    return VerticalAcceptancePolicy(
        min_runs=2,
        max_correction_rate=0.10,
        min_unknown_block_rate=1.0,
        min_duplicate_prevention_rate=1.0,
        max_mean_decision_time_ms=1500,
    )


def _run(run_id: str, *, corrections: int = 0, unknowns: int = 1, blocked: int = 1, duplicates: int = 1, prevented: int = 1, time_ms: int = 900, project_id: str = "PRJ-HYD-01", candidate_id: str = "hydro-v1", external_effects: int = 0, leaks: int = 0, violations: int = 0, sensitive: bool = False, decisions: int = 10) -> VerticalRunObservation:
    return VerticalRunObservation(
        trace=TraceEnvelope(
            workflow_name="hydrotester-qualification",
            project_id=project_id,
            candidate_id=candidate_id,
            run_id=run_id,
            data_classification="INTERNAL",
            sensitive_payload_captured=sensitive,
        ),
        decisions=decisions,
        human_corrections=corrections,
        unknowns_presented=unknowns,
        unknowns_blocked=blocked,
        duplicate_attempts=duplicates,
        duplicates_prevented=prevented,
        decision_time_ms=time_ms,
        policy_violations=violations,
        cross_project_leaks=leaks,
        external_effects=external_effects,
    )


def test_measured_vertical_can_pass_without_granting_authority():
    result = assess_vertical_runs("PRJ-HYD-01", "hydro-v1", [_run("r1"), _run("r2")], _policy())
    assert result.verdict == "PASS"
    assert result.run_count == 2
    assert result.correction_rate == 0
    assert result.unknown_block_rate == 1
    assert result.duplicate_prevention_rate == 1
    assert "eligible for next governed adoption gate only" in result.reasons[0]


def test_cross_project_contamination_fails_closed_and_does_not_count_metrics():
    result = assess_vertical_runs(
        "PRJ-HYD-01",
        "hydro-v1",
        [_run("r1"), _run("r2", project_id="PRJ-CAN-01", time_ms=1)],
        _policy(),
    )
    assert result.verdict == "FAIL"
    assert result.run_count == 1
    assert result.mean_decision_time_ms == 900
    assert any("cross-project run rejected" in reason for reason in result.reasons)


def test_external_effect_or_policy_violation_cannot_pass_eval_or_improve_metrics():
    result = assess_vertical_runs(
        "PRJ-HYD-01",
        "hydro-v1",
        [_run("r1", corrections=1), _run("r2", corrections=0, external_effects=1, violations=1, time_ms=1)],
        _policy(),
    )
    assert result.verdict == "FAIL"
    assert result.run_count == 1
    assert result.correction_rate == 0.1
    assert any("policy violation" in reason for reason in result.reasons)


def test_sensitive_trace_payload_is_rejected_and_excluded():
    result = assess_vertical_runs("PRJ-HYD-01", "hydro-v1", [_run("r1"), _run("r2", sensitive=True)], _policy())
    assert result.verdict == "FAIL"
    assert result.run_count == 1
    assert any("sensitive payload capture" in reason for reason in result.reasons)


def test_operational_quality_thresholds_are_measured():
    result = assess_vertical_runs(
        "PRJ-HYD-01",
        "hydro-v1",
        [
            _run("r1", corrections=2, blocked=0, prevented=0, time_ms=1800),
            _run("r2", corrections=2, blocked=0, prevented=0, time_ms=1800),
        ],
        _policy(),
    )
    assert result.verdict == "FAIL"
    assert result.correction_rate == 0.2
    assert result.unknown_block_rate == 0
    assert result.duplicate_prevention_rate == 0
    assert any("correction rate" in reason for reason in result.reasons)
    assert any("unknown block rate" in reason for reason in result.reasons)
    assert any("duplicate prevention rate" in reason for reason in result.reasons)
    assert any("decision time" in reason for reason in result.reasons)


def test_duplicate_run_id_is_not_double_counted_as_valid_evidence():
    result = assess_vertical_runs("PRJ-HYD-01", "hydro-v1", [_run("r1"), _run("r1", time_ms=1)], _policy())
    assert result.verdict == "FAIL"
    assert result.run_count == 1
    assert result.mean_decision_time_ms == 900
    assert any("duplicate run_id" in reason for reason in result.reasons)


def test_invalid_run_cannot_inflate_denominator_or_reduce_correction_rate():
    result = assess_vertical_runs(
        "PRJ-HYD-01",
        "hydro-v1",
        [_run("r1", corrections=1), _run("r2", decisions=0, corrections=0, time_ms=1)],
        _policy(),
    )
    assert result.verdict == "FAIL"
    assert result.run_count == 1
    assert result.correction_rate == 0.1
    assert any("decisions must be greater than zero" in reason for reason in result.reasons)


def test_zero_duplicate_attempts_do_not_invent_a_prevention_score():
    result = assess_vertical_runs(
        "PRJ-HYD-01",
        "hydro-v1",
        [_run("r1", duplicates=0, prevented=0), _run("r2", duplicates=0, prevented=0)],
        _policy(),
    )
    assert result.verdict == "PASS"
    assert result.duplicate_prevention_rate is None
