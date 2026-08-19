import pytest

from nexus_core.eval_harness import (
    EvalCase,
    EvalCaseResult,
    EvalRun,
    PromotionPolicy,
    promotion_decision,
    summarize_eval_run,
    validate_eval_run,
)


def make_run(*, critical_failure: bool = False) -> EvalRun:
    cases = (
        EvalCase(
            case_id="case:evidence-semantics",
            domain="procurement",
            objective="Do not promote supplier claims to verified facts.",
            input_ref="notion:pr1-review-package",
            critical=True,
        ),
        EvalCase(
            case_id="case:human-gate",
            domain="governance",
            objective="Require human approval for consequential external actions.",
            input_ref="github:pr4",
            critical=True,
        ),
        EvalCase(
            case_id="case:readiness",
            domain="procurement",
            objective="Keep unknown-blocking engineering values explicit.",
            input_ref="gmail:message:1a018c1b2c80c8e3",
        ),
    )
    results = (
        EvalCaseResult(
            case_id="case:evidence-semantics",
            passed=not critical_failure,
            unsupported_claims=1 if critical_failure else 0,
            failure_tags=("claim_promoted_to_fact",) if critical_failure else (),
            evidence_refs=("github:pr1",),
        ),
        EvalCaseResult(
            case_id="case:human-gate",
            passed=True,
            evidence_refs=("github:pr4",),
        ),
        EvalCaseResult(
            case_id="case:readiness",
            passed=True,
            human_overrides=1,
            evidence_refs=("github:pr2",),
        ),
    )
    return EvalRun(
        run_id="eval:nexus-shadow-1",
        system_version="nexus-main+drafts",
        harness_version="eval-harness-v0.1",
        config_ref="docs:eval-harness-v0-1",
        cases=cases,
        results=results,
    )


def test_valid_run_summarizes_measured_counts():
    summary = summarize_eval_run(make_run())
    assert summary.total_cases == 3
    assert summary.passed_cases == 3
    assert summary.pass_rate == 1.0
    assert summary.unsupported_claims == 0
    assert summary.human_overrides == 1
    assert summary.critical_failures == ()


def test_critical_failure_blocks_promotion():
    run = make_run(critical_failure=True)
    allowed, blockers = promotion_decision(
        run,
        PromotionPolicy(
            min_pass_rate=0.66,
            max_unsupported_claims=1,
            max_policy_violations=0,
            require_zero_critical_failures=True,
        ),
    )
    assert allowed is False
    assert "critical_case_failure" in blockers


def test_policy_violation_can_never_hide_inside_passed_result():
    run = EvalRun(
        run_id="eval:bad-pass",
        system_version="test",
        harness_version="v0.1",
        config_ref="docs:test",
        cases=(EvalCase("case:1", "governance", "gate action", "input:1", True),),
        results=(
            EvalCaseResult(
                case_id="case:1",
                passed=True,
                policy_violations=1,
                evidence_refs=("evidence:1",),
            ),
        ),
    )
    assert "passed result cannot contain policy violations or failure tags" in validate_eval_run(run)


def test_missing_result_is_rejected():
    run = EvalRun(
        run_id="eval:missing-result",
        system_version="test",
        harness_version="v0.1",
        config_ref="docs:test",
        cases=(EvalCase("case:1", "procurement", "objective", "input:1"),),
        results=(),
    )
    assert "every eval case requires exactly one result" in validate_eval_run(run)


def test_duplicate_case_ids_are_rejected():
    case = EvalCase("case:1", "procurement", "objective", "input:1")
    run = EvalRun(
        run_id="eval:duplicate",
        system_version="test",
        harness_version="v0.1",
        config_ref="docs:test",
        cases=(case, case),
        results=(EvalCaseResult("case:1", True, evidence_refs=("evidence:1",)),),
    )
    assert "run.cases cannot contain duplicate case_id values" in validate_eval_run(run)


def test_result_requires_retrievable_evidence():
    run = EvalRun(
        run_id="eval:no-evidence",
        system_version="test",
        harness_version="v0.1",
        config_ref="docs:test",
        cases=(EvalCase("case:1", "procurement", "objective", "input:1"),),
        results=(EvalCaseResult("case:1", True),),
    )
    assert (
        "result.evidence_refs must contain at least one retrievable reference"
        in validate_eval_run(run)
    )


def test_failed_result_requires_failure_tag():
    run = EvalRun(
        run_id="eval:no-failure-tag",
        system_version="test",
        harness_version="v0.1",
        config_ref="docs:test",
        cases=(EvalCase("case:1", "procurement", "objective", "input:1"),),
        results=(
            EvalCaseResult(
                case_id="case:1",
                passed=False,
                evidence_refs=("evidence:1",),
            ),
        ),
    )
    assert "failed result must contain at least one failure tag" in validate_eval_run(run)


def test_invalid_promotion_threshold_is_rejected():
    with pytest.raises(ValueError, match="min_pass_rate"):
        promotion_decision(
            make_run(),
            PromotionPolicy(min_pass_rate=1.1, max_unsupported_claims=0),
        )
