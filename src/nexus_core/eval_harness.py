from dataclasses import dataclass


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    domain: str
    objective: str
    input_ref: str
    critical: bool = False


@dataclass(frozen=True)
class EvalCaseResult:
    case_id: str
    passed: bool
    unsupported_claims: int = 0
    policy_violations: int = 0
    human_overrides: int = 0
    failure_tags: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvalRun:
    run_id: str
    system_version: str
    harness_version: str
    config_ref: str
    cases: tuple[EvalCase, ...]
    results: tuple[EvalCaseResult, ...]


@dataclass(frozen=True)
class PromotionPolicy:
    min_pass_rate: float
    max_unsupported_claims: int
    max_policy_violations: int = 0
    require_zero_critical_failures: bool = True


@dataclass(frozen=True)
class EvalSummary:
    total_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate: float
    unsupported_claims: int
    policy_violations: int
    human_overrides: int
    critical_failures: tuple[str, ...]
    failure_tags: tuple[str, ...]


def validate_eval_run(run: EvalRun) -> list[str]:
    errors: list[str] = []

    for name, value in (
        ("run.run_id", run.run_id),
        ("run.system_version", run.system_version),
        ("run.harness_version", run.harness_version),
        ("run.config_ref", run.config_ref),
    ):
        if not value.strip():
            errors.append(f"{name} is required")

    if not run.cases:
        errors.append("run.cases must contain at least one case")

    case_ids = [case.case_id for case in run.cases]
    if len(case_ids) != len(set(case_ids)):
        errors.append("run.cases cannot contain duplicate case_id values")

    result_ids = [result.case_id for result in run.results]
    if len(result_ids) != len(set(result_ids)):
        errors.append("run.results cannot contain duplicate case_id values")

    known_case_ids = set(case_ids)
    unknown_result_ids = set(result_ids) - known_case_ids
    if unknown_result_ids:
        errors.append("run.results contains unknown case_id values")

    missing_result_ids = known_case_ids - set(result_ids)
    if missing_result_ids:
        errors.append("every eval case requires exactly one result")

    for case in run.cases:
        for name, value in (
            ("case.case_id", case.case_id),
            ("case.domain", case.domain),
            ("case.objective", case.objective),
            ("case.input_ref", case.input_ref),
        ):
            if not value.strip():
                errors.append(f"{name} is required")

    for result in run.results:
        if not result.case_id.strip():
            errors.append("result.case_id is required")

        if result.unsupported_claims < 0:
            errors.append("result.unsupported_claims cannot be negative")
        if result.policy_violations < 0:
            errors.append("result.policy_violations cannot be negative")
        if result.human_overrides < 0:
            errors.append("result.human_overrides cannot be negative")

        if not result.evidence_refs:
            errors.append("result.evidence_refs must contain at least one retrievable reference")
        elif any(not ref.strip() for ref in result.evidence_refs):
            errors.append("result.evidence_refs cannot contain blank references")

        if any(not tag.strip() for tag in result.failure_tags):
            errors.append("result.failure_tags cannot contain blank tags")

        if not result.passed and not result.failure_tags:
            errors.append("failed result must contain at least one failure tag")

        if result.passed and (result.policy_violations > 0 or result.failure_tags):
            errors.append("passed result cannot contain policy violations or failure tags")

    return errors


def summarize_eval_run(run: EvalRun) -> EvalSummary:
    errors = validate_eval_run(run)
    if errors:
        raise ValueError("invalid eval run: " + "; ".join(errors))

    case_by_id = {case.case_id: case for case in run.cases}
    passed_cases = sum(1 for result in run.results if result.passed)
    failed_cases = len(run.results) - passed_cases
    unsupported_claims = sum(result.unsupported_claims for result in run.results)
    policy_violations = sum(result.policy_violations for result in run.results)
    human_overrides = sum(result.human_overrides for result in run.results)

    critical_failures = tuple(
        result.case_id
        for result in run.results
        if not result.passed and case_by_id[result.case_id].critical
    )
    failure_tags = tuple(
        sorted({tag for result in run.results for tag in result.failure_tags})
    )

    return EvalSummary(
        total_cases=len(run.results),
        passed_cases=passed_cases,
        failed_cases=failed_cases,
        pass_rate=passed_cases / len(run.results),
        unsupported_claims=unsupported_claims,
        policy_violations=policy_violations,
        human_overrides=human_overrides,
        critical_failures=critical_failures,
        failure_tags=failure_tags,
    )


def promotion_decision(run: EvalRun, policy: PromotionPolicy) -> tuple[bool, tuple[str, ...]]:
    if not 0 <= policy.min_pass_rate <= 1:
        raise ValueError("policy.min_pass_rate must be between 0 and 1")
    if policy.max_unsupported_claims < 0:
        raise ValueError("policy.max_unsupported_claims cannot be negative")
    if policy.max_policy_violations < 0:
        raise ValueError("policy.max_policy_violations cannot be negative")

    summary = summarize_eval_run(run)
    blockers: list[str] = []

    if summary.pass_rate < policy.min_pass_rate:
        blockers.append("pass_rate_below_threshold")
    if summary.unsupported_claims > policy.max_unsupported_claims:
        blockers.append("unsupported_claim_budget_exceeded")
    if summary.policy_violations > policy.max_policy_violations:
        blockers.append("policy_violation_budget_exceeded")
    if policy.require_zero_critical_failures and summary.critical_failures:
        blockers.append("critical_case_failure")

    return (not blockers, tuple(blockers))
