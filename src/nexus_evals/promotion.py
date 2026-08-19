from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .harness import EvaluationSuiteResult


@dataclass(frozen=True)
class CaseOutcomeMetrics:
    """Observed counters attached to one evaluated case.

    These values are measurements supplied by an adapter or human/domain review;
    the promotion layer does not infer them from model text.
    """

    case_id: str
    unsupported_claims: int = 0
    policy_violations: int = 0
    human_overrides: int = 0
    failure_tags: tuple[str, ...] = ()

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.case_id.strip():
            errors.append("case_id is required")
        if self.unsupported_claims < 0:
            errors.append("unsupported_claims cannot be negative")
        if self.policy_violations < 0:
            errors.append("policy_violations cannot be negative")
        if self.human_overrides < 0:
            errors.append("human_overrides cannot be negative")
        if any(not tag.strip() for tag in self.failure_tags):
            errors.append("failure_tags cannot contain blank tags")
        return errors


@dataclass(frozen=True)
class PromotionRun:
    run_id: str
    system_version: str
    harness_version: str
    config_ref: str
    suite: EvaluationSuiteResult
    metrics: Sequence[CaseOutcomeMetrics]
    critical_case_ids: Sequence[str] = ()

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name, value in (
            ("run_id", self.run_id),
            ("system_version", self.system_version),
            ("harness_version", self.harness_version),
            ("config_ref", self.config_ref),
        ):
            if not value.strip():
                errors.append(f"{name} is required")

        if self.suite.total_cases <= 0:
            errors.append("suite must contain at least one evaluated case")
        if self.suite.validation_errors:
            errors.append("suite contains validation errors")

        result_ids = [result.case_id for result in self.suite.results]
        result_id_set = set(result_ids)
        if len(result_ids) != len(result_id_set):
            errors.append("suite results cannot contain duplicate case_id values")

        metric_ids = [metric.case_id for metric in self.metrics]
        metric_id_set = set(metric_ids)
        if len(metric_ids) != len(metric_id_set):
            errors.append("metrics cannot contain duplicate case_id values")
        if metric_id_set != result_id_set:
            errors.append("metrics must provide exact case_id coverage for suite results")

        critical_ids = list(self.critical_case_ids)
        if len(critical_ids) != len(set(critical_ids)):
            errors.append("critical_case_ids cannot contain duplicates")
        if set(critical_ids) - result_id_set:
            errors.append("critical_case_ids must refer to evaluated suite cases")

        for metric in self.metrics:
            errors.extend(
                f"metric[{metric.case_id or '?'}]: {error}"
                for error in metric.validate()
            )
        return errors


@dataclass(frozen=True)
class PromotionPolicy:
    """Explicit fail-closed promotion limits.

    Counts are used deliberately instead of an opaque aggregate intelligence
    score. Critical failures can block promotion regardless of aggregate counts.
    """

    max_failed_cases: int = 0
    max_unsupported_claims: int = 0
    max_policy_violations: int = 0
    require_zero_critical_failures: bool = True

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.max_failed_cases < 0:
            errors.append("max_failed_cases cannot be negative")
        if self.max_unsupported_claims < 0:
            errors.append("max_unsupported_claims cannot be negative")
        if self.max_policy_violations < 0:
            errors.append("max_policy_violations cannot be negative")
        return errors


@dataclass(frozen=True)
class PromotionSummary:
    total_cases: int
    passed_cases: int
    failed_cases: int
    unsupported_claims: int
    policy_violations: int
    human_overrides: int
    critical_failures: tuple[str, ...]
    failure_tags: tuple[str, ...]


@dataclass(frozen=True)
class PromotionDecision:
    allowed: bool
    blockers: tuple[str, ...]
    summary: PromotionSummary | None
    validation_errors: tuple[str, ...] = ()


def summarize_promotion_run(run: PromotionRun) -> PromotionSummary:
    errors = run.validate()
    if errors:
        raise ValueError("invalid promotion run: " + "; ".join(errors))

    result_by_id = {result.case_id: result for result in run.suite.results}
    critical_failures = tuple(
        case_id
        for case_id in run.critical_case_ids
        if not result_by_id[case_id].passed
    )

    return PromotionSummary(
        total_cases=run.suite.total_cases,
        passed_cases=run.suite.passed_cases,
        failed_cases=run.suite.failed_cases,
        unsupported_claims=sum(metric.unsupported_claims for metric in run.metrics),
        policy_violations=sum(metric.policy_violations for metric in run.metrics),
        human_overrides=sum(metric.human_overrides for metric in run.metrics),
        critical_failures=critical_failures,
        failure_tags=tuple(
            sorted({tag for metric in run.metrics for tag in metric.failure_tags})
        ),
    )


def promotion_decision(
    run: PromotionRun, policy: PromotionPolicy
) -> PromotionDecision:
    validation_errors = tuple(run.validate() + policy.validate())
    if validation_errors:
        return PromotionDecision(
            allowed=False,
            blockers=("invalid_promotion_input",),
            summary=None,
            validation_errors=validation_errors,
        )

    summary = summarize_promotion_run(run)
    blockers: list[str] = []

    if summary.failed_cases > policy.max_failed_cases:
        blockers.append("failed_case_budget_exceeded")
    if summary.unsupported_claims > policy.max_unsupported_claims:
        blockers.append("unsupported_claim_budget_exceeded")
    if summary.policy_violations > policy.max_policy_violations:
        blockers.append("policy_violation_budget_exceeded")
    if policy.require_zero_critical_failures and summary.critical_failures:
        blockers.append("critical_case_failure")

    return PromotionDecision(
        allowed=not blockers,
        blockers=tuple(blockers),
        summary=summary,
    )
