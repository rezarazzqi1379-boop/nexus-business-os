from nexus_evals import (
    Assertion,
    EvaluationCase,
    evaluate_case,
    evaluate_suite,
)


def make_case() -> EvaluationCase:
    return EvaluationCase(
        case_id="hydrotester-readiness-shadow",
        name="Hydrotester readiness preserves blocking unknowns",
        input_ref="gmail:message:1a018c1b2c80c8e3",
        observations={
            "decision": {
                "ready_for_discovery": True,
                "ready_for_final_quote": False,
            },
            "requirements": {
                "length_range": "unknown_blocking",
                "wall_thickness_or_id": "unknown_blocking",
                "max_pressure": "provisional",
            },
            "actions": ["request_engineering_inputs"],
        },
        assertions=(
            Assertion(
                assertion_id="discovery-open",
                path="decision.ready_for_discovery",
                operator="equals",
                expected=True,
            ),
            Assertion(
                assertion_id="final-quote-blocked",
                path="decision.ready_for_final_quote",
                operator="equals",
                expected=False,
            ),
            Assertion(
                assertion_id="length-stays-unknown",
                path="requirements.length_range",
                operator="equals",
                expected="unknown_blocking",
            ),
            Assertion(
                assertion_id="no-send-action",
                path="actions",
                operator="not_contains",
                expected="send_external_email",
            ),
        ),
        evidence_refs=("gmail:message:1a018c1b2c80c8e3",),
    )


def test_valid_case_passes():
    result = evaluate_case(make_case())
    assert result.passed is True
    assert result.failed_assertion_ids == ()


def test_failed_assertion_is_reported_without_throwing():
    case = make_case()
    broken = EvaluationCase(
        case_id=case.case_id,
        name=case.name,
        input_ref=case.input_ref,
        observations={
            **case.observations,
            "decision": {
                "ready_for_discovery": True,
                "ready_for_final_quote": True,
            },
        },
        assertions=case.assertions,
        evidence_refs=case.evidence_refs,
    )
    result = evaluate_case(broken)
    assert result.passed is False
    assert result.failed_assertion_ids == ("final-quote-blocked",)


def test_missing_evidence_fails_case_validation():
    case = make_case()
    invalid = EvaluationCase(
        case_id=case.case_id,
        name=case.name,
        input_ref=case.input_ref,
        observations=case.observations,
        assertions=case.assertions,
        evidence_refs=(),
    )
    result = evaluate_case(invalid)
    assert result.passed is False
    assert "at least one evidence_ref is required" in result.validation_errors
    assert result.assertion_results == ()


def test_duplicate_assertion_ids_are_rejected():
    case = make_case()
    duplicate = EvaluationCase(
        case_id=case.case_id,
        name=case.name,
        input_ref=case.input_ref,
        observations=case.observations,
        assertions=(case.assertions[0], case.assertions[0]),
        evidence_refs=case.evidence_refs,
    )
    result = evaluate_case(duplicate)
    assert result.passed is False
    assert "duplicate assertion_id: discovery-open" in result.validation_errors


def test_nested_missing_path_is_a_failed_assertion_not_exception():
    case = make_case()
    missing = EvaluationCase(
        case_id=case.case_id,
        name=case.name,
        input_ref=case.input_ref,
        observations={},
        assertions=(
            Assertion(
                assertion_id="missing-safe",
                path="decision.ready_for_final_quote",
                operator="equals",
                expected=False,
            ),
        ),
        evidence_refs=case.evidence_refs,
    )
    result = evaluate_case(missing)
    assert result.passed is False
    assert result.assertion_results[0].message == "path missing"


def test_present_and_absent_semantics():
    case = EvaluationCase(
        case_id="presence-check",
        name="Presence assertions",
        input_ref="notion:record:example",
        observations={"known": {"value": 1, "empty": None}},
        assertions=(
            Assertion("has-value", "known.value", "present"),
            Assertion("none-counts-absent", "known.empty", "absent"),
            Assertion("missing-counts-absent", "known.missing", "absent"),
        ),
        evidence_refs=("notion:record:example",),
    )
    assert evaluate_case(case).passed is True


def test_unsupported_membership_type_fails_closed():
    case = EvaluationCase(
        case_id="membership-type",
        name="Do not infer containment semantics for scalars",
        input_ref="evidence:membership",
        observations={"value": 42},
        assertions=(
            Assertion("scalar-not-contains", "value", "not_contains", "danger"),
        ),
        evidence_refs=("evidence:membership",),
    )
    result = evaluate_case(case)
    assert result.passed is False
    assert (
        result.assertion_results[0].message
        == "membership unsupported for observed value"
    )


def test_blank_dot_path_segment_is_rejected():
    case = EvaluationCase(
        case_id="bad-path",
        name="Malformed paths fail validation",
        input_ref="evidence:path",
        observations={"a": {"b": 1}},
        assertions=(Assertion("bad-path-assertion", "a..b", "equals", 1),),
        evidence_refs=("evidence:path",),
    )
    result = evaluate_case(case)
    assert result.passed is False
    assert any("path segments must be nonblank" in error for error in result.validation_errors)


def test_suite_summary_is_count_based_not_business_scoring():
    passing = make_case()
    failing = EvaluationCase(
        case_id="failing",
        name="Failing case",
        input_ref="evidence:failing",
        observations={"decision": {"allowed": True}},
        assertions=(
            Assertion("must-block", "decision.allowed", "equals", False),
        ),
        evidence_refs=("evidence:failing",),
    )
    suite = evaluate_suite((passing, failing))
    assert suite.total_cases == 2
    assert suite.passed_cases == 1
    assert suite.failed_cases == 1
    assert suite.passed is False


def test_duplicate_case_ids_fail_suite_even_when_cases_pass():
    case = make_case()
    suite = evaluate_suite((case, case))
    assert suite.passed_cases == 2
    assert suite.failed_cases == 0
    assert suite.passed is False
    assert suite.validation_errors == (
        "duplicate case_id: hydrotester-readiness-shadow",
    )


def test_empty_suite_does_not_pass():
    suite = evaluate_suite(())
    assert suite.total_cases == 0
    assert suite.passed is False
