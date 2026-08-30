from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence


AssertionOperator = Literal[
    "equals",
    "not_equals",
    "present",
    "absent",
    "contains",
    "not_contains",
]

_ALLOWED_OPERATORS = {
    "equals",
    "not_equals",
    "present",
    "absent",
    "contains",
    "not_contains",
}


@dataclass(frozen=True)
class Assertion:
    """A deterministic assertion over a structured observation.

    `path` uses dot-separated dictionary keys (for example `decision.status`).
    The harness deliberately avoids executing arbitrary expressions or code.
    """

    assertion_id: str
    path: str
    operator: AssertionOperator
    expected: Any = None
    rationale: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.assertion_id.strip():
            errors.append("assertion_id is required")
        if not self.path.strip():
            errors.append("path is required")
        elif any(not segment for segment in self.path.split(".")):
            errors.append("path segments must be nonblank")
        if self.operator not in _ALLOWED_OPERATORS:
            errors.append("operator is unsupported")
        if self.operator in {"present", "absent"} and self.expected is not None:
            errors.append(f"{self.operator} assertion must not define expected")
        return errors


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    name: str
    input_ref: str
    observations: Mapping[str, Any]
    assertions: Sequence[Assertion]
    evidence_refs: Sequence[str]

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.case_id.strip():
            errors.append("case_id is required")
        if not self.name.strip():
            errors.append("name is required")
        if not self.input_ref.strip():
            errors.append("input_ref is required")
        if not isinstance(self.observations, Mapping):
            errors.append("observations must be a mapping")
        if not self.assertions:
            errors.append("at least one assertion is required")
        if not self.evidence_refs:
            errors.append("at least one evidence_ref is required")
        for ref in self.evidence_refs:
            if not ref.strip():
                errors.append("evidence_ref must be nonblank")
        seen_ids: set[str] = set()
        for assertion in self.assertions:
            errors.extend(
                f"assertion[{assertion.assertion_id or '?'}]: {error}"
                for error in assertion.validate()
            )
            if assertion.assertion_id in seen_ids:
                errors.append(f"duplicate assertion_id: {assertion.assertion_id}")
            seen_ids.add(assertion.assertion_id)
        return errors


@dataclass(frozen=True)
class AssertionResult:
    assertion_id: str
    passed: bool
    observed: Any
    message: str


@dataclass(frozen=True)
class EvaluationResult:
    case_id: str
    passed: bool
    validation_errors: tuple[str, ...]
    assertion_results: tuple[AssertionResult, ...]

    @property
    def failed_assertion_ids(self) -> tuple[str, ...]:
        return tuple(
            result.assertion_id
            for result in self.assertion_results
            if not result.passed
        )


@dataclass(frozen=True)
class EvaluationSuiteResult:
    total_cases: int
    passed_cases: int
    failed_cases: int
    results: tuple[EvaluationResult, ...]
    validation_errors: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return (
            self.total_cases > 0
            and self.failed_cases == 0
            and not self.validation_errors
        )


def _resolve_path(observations: Mapping[str, Any], path: str) -> tuple[bool, Any]:
    current: Any = observations
    for segment in path.split("."):
        if not isinstance(current, Mapping) or segment not in current:
            return False, None
        current = current[segment]
    return True, current


def _membership(container: Any, expected: Any) -> tuple[bool, bool]:
    """Return (supported, contains) and never guess membership semantics."""

    if isinstance(container, str):
        if not isinstance(expected, str):
            return False, False
        return True, expected in container
    if isinstance(container, Mapping):
        return True, expected in container
    if isinstance(container, (list, tuple, set, frozenset)):
        return True, expected in container
    return False, False


def _evaluate_assertion(
    observations: Mapping[str, Any], assertion: Assertion
) -> AssertionResult:
    exists, observed = _resolve_path(observations, assertion.path)

    if assertion.operator == "present":
        passed = exists and observed is not None
        message = "value present" if passed else "value missing"
    elif assertion.operator == "absent":
        passed = not exists or observed is None
        message = "value absent" if passed else "unexpected value present"
    elif not exists:
        passed = False
        message = "path missing"
    elif assertion.operator == "equals":
        passed = observed == assertion.expected
        message = "values equal" if passed else "values differ"
    elif assertion.operator == "not_equals":
        passed = observed != assertion.expected
        message = "values differ" if passed else "unexpected equality"
    elif assertion.operator in {"contains", "not_contains"}:
        supported, contains = _membership(observed, assertion.expected)
        if not supported:
            passed = False
            message = "membership unsupported for observed value"
        elif assertion.operator == "contains":
            passed = contains
            message = "expected member found" if passed else "expected member not found"
        else:
            passed = not contains
            message = "forbidden member absent" if passed else "forbidden member found"
    else:  # guarded by validate(); retained as a safe fallback.
        passed = False
        message = "unsupported operator"

    return AssertionResult(
        assertion_id=assertion.assertion_id,
        passed=passed,
        observed=observed,
        message=message,
    )


def evaluate_case(case: EvaluationCase) -> EvaluationResult:
    validation_errors = tuple(case.validate())
    if validation_errors:
        return EvaluationResult(
            case_id=case.case_id,
            passed=False,
            validation_errors=validation_errors,
            assertion_results=(),
        )

    assertion_results = tuple(
        _evaluate_assertion(case.observations, assertion)
        for assertion in case.assertions
    )
    return EvaluationResult(
        case_id=case.case_id,
        passed=all(result.passed for result in assertion_results),
        validation_errors=(),
        assertion_results=assertion_results,
    )


def evaluate_suite(cases: Sequence[EvaluationCase]) -> EvaluationSuiteResult:
    results = tuple(evaluate_case(case) for case in cases)
    passed_cases = sum(1 for result in results if result.passed)
    total_cases = len(results)

    seen_case_ids: set[str] = set()
    duplicate_case_ids: set[str] = set()
    for case in cases:
        if case.case_id in seen_case_ids:
            duplicate_case_ids.add(case.case_id)
        seen_case_ids.add(case.case_id)

    suite_errors = tuple(
        f"duplicate case_id: {case_id}"
        for case_id in sorted(duplicate_case_ids)
    )

    return EvaluationSuiteResult(
        total_cases=total_cases,
        passed_cases=passed_cases,
        failed_cases=total_cases - passed_cases,
        results=results,
        validation_errors=suite_errors,
    )
