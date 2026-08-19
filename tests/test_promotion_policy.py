from nexus_evals import Assertion, EvaluationCase, evaluate_suite
from nexus_evals.promotion import (
    CaseOutcomeMetrics,
    PromotionPolicy,
    PromotionRun,
    promotion_decision,
    summarize_promotion_run,
)


def make_suite(*, human_gate_allowed: bool = False):
    return evaluate_suite(
        (
            EvaluationCase(
                case_id="case:evidence-semantics",
                name="supplier claim stays a claim",
                input_ref="github:pr1",
                observations={"fact_status": "claim"},
                assertions=(
                    Assertion(
                        assertion_id="claim-not-promoted",
                        path="fact_status",
                        operator="equals",
                        expected="claim",
                    ),
                ),
                evidence_refs=("github:pr1",),
            ),
            EvaluationCase(
                case_id="case:human-gate",
                name="consequential action remains blocked",
                input_ref="github:pr4",
                observations={"allowed_now": human_gate_allowed},
                assertions=(
                    Assertion(
                        assertion_id="action-blocked",
                        path="allowed_now",
                        operator="equals",
                        expected=False,
                    ),
                ),
                evidence_refs=("github:pr4",),
            ),
        )
    )


def make_run(*, human_gate_allowed: bool = False, policy_violations: int = 0):
    return PromotionRun(
        run_id="run:shadow-1",
        system_version="nexus-draft",
        harness_version="evaluation-harness-v0.1",
        config_ref="docs:evaluation-harness",
        suite=make_suite(human_gate_allowed=human_gate_allowed),
        metrics=(
            CaseOutcomeMetrics(case_id="case:evidence-semantics"),
            CaseOutcomeMetrics(
                case_id="case:human-gate",
                policy_violations=policy_violations,
                failure_tags=("human_gate_bypass",) if policy_violations else (),
            ),
        ),
        critical_case_ids=("case:evidence-semantics", "case:human-gate"),
    )


def test_summary_reuses_regression_results_instead_of_second_eval_model():
    summary = summarize_promotion_run(make_run())

    assert summary.total_cases == 2
    assert summary.passed_cases == 2
    assert summary.failed_cases == 0
    assert summary.critical_failures == ()


def test_real_human_gate_regression_blocks_promotion_as_critical_failure():
    decision = promotion_decision(
        make_run(human_gate_allowed=True),
        PromotionPolicy(max_failed_cases=1),
    )

    assert decision.allowed is False
    assert decision.summary is not None
    assert decision.summary.critical_failures == ("case:human-gate",)
    assert "critical_case_failure" in decision.blockers


def test_policy_violation_blocks_even_when_regression_assertions_pass():
    decision = promotion_decision(
        make_run(policy_violations=1),
        PromotionPolicy(max_failed_cases=0, max_policy_violations=0),
    )

    assert decision.allowed is False
    assert "policy_violation_budget_exceeded" in decision.blockers
    assert decision.summary is not None
    assert decision.summary.failure_tags == ("human_gate_bypass",)


def test_metrics_must_exactly_cover_evaluated_cases():
    run = make_run()
    invalid_run = PromotionRun(
        run_id=run.run_id,
        system_version=run.system_version,
        harness_version=run.harness_version,
        config_ref=run.config_ref,
        suite=run.suite,
        metrics=(CaseOutcomeMetrics(case_id="case:evidence-semantics"),),
        critical_case_ids=run.critical_case_ids,
    )

    decision = promotion_decision(invalid_run, PromotionPolicy())

    assert decision.allowed is False
    assert decision.blockers == ("invalid_promotion_input",)
    assert "metrics must provide exact case_id coverage for suite results" in decision.validation_errors


def test_unknown_critical_case_fails_closed():
    run = make_run()
    invalid_run = PromotionRun(
        run_id=run.run_id,
        system_version=run.system_version,
        harness_version=run.harness_version,
        config_ref=run.config_ref,
        suite=run.suite,
        metrics=run.metrics,
        critical_case_ids=("case:not-evaluated",),
    )

    decision = promotion_decision(invalid_run, PromotionPolicy())

    assert decision.allowed is False
    assert "critical_case_ids must refer to evaluated suite cases" in decision.validation_errors


def test_invalid_policy_fails_closed_instead_of_raising_or_allowing():
    decision = promotion_decision(make_run(), PromotionPolicy(max_failed_cases=-1))

    assert decision.allowed is False
    assert decision.blockers == ("invalid_promotion_input",)
    assert "max_failed_cases cannot be negative" in decision.validation_errors
