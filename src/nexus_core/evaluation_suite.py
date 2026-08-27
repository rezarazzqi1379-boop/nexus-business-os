from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from nexus_core.evaluation_constitution import EvalCase, EvalObservation, EvalResult, evaluate_case


@dataclass(frozen=True)
class SuiteResult:
    candidate_id: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    invalid_cases: int
    total_human_corrections: int
    promotable_to_adoption_gate: bool
    reasons: tuple[str, ...]
    case_results: tuple[tuple[str, EvalResult], ...]


def evaluate_suite(
    candidate_id: str,
    cases: Sequence[EvalCase],
    observations: Sequence[EvalObservation],
) -> SuiteResult:
    """Evaluate one candidate against the frozen NEXUS corpus.

    Passing this suite never grants merge/deploy/external-action/production authority.
    It only makes the candidate eligible to proceed to the existing measured Adoption Gate.
    """
    if not candidate_id.strip():
        raise ValueError("candidate_id is required")
    if not cases:
        raise ValueError("at least one eval case is required")

    case_by_id = {case.case_id: case for case in cases}
    if len(case_by_id) != len(cases):
        raise ValueError("duplicate case_id in suite")

    obs_by_id = {obs.case_id: obs for obs in observations}
    if len(obs_by_id) != len(observations):
        raise ValueError("duplicate observation case_id")

    missing_obs = sorted(set(case_by_id) - set(obs_by_id))
    extra_obs = sorted(set(obs_by_id) - set(case_by_id))
    reasons: list[str] = []
    if missing_obs:
        reasons.append("missing observations: " + ", ".join(missing_obs))
    if extra_obs:
        reasons.append("observations for unknown cases: " + ", ".join(extra_obs))

    case_results: list[tuple[str, EvalResult]] = []
    total_corrections = 0
    passed = failed = invalid = 0

    for case in cases:
        obs = obs_by_id.get(case.case_id)
        if obs is None:
            result = EvalResult("INVALID", ("missing observation",))
        else:
            total_corrections += obs.human_corrections
            result = evaluate_case(case, obs)
        case_results.append((case.case_id, result))
        if result.verdict == "PASS":
            passed += 1
        elif result.verdict == "FAIL":
            failed += 1
        else:
            invalid += 1

    if failed:
        reasons.append(f"{failed} frozen case(s) failed")
    if invalid:
        reasons.append(f"{invalid} frozen case(s) invalid")

    promotable = not reasons and passed == len(cases)
    if promotable:
        reasons.append("all frozen cases passed; candidate may proceed to measured Adoption Gate only")

    return SuiteResult(
        candidate_id=candidate_id,
        total_cases=len(cases),
        passed_cases=passed,
        failed_cases=failed,
        invalid_cases=invalid,
        total_human_corrections=total_corrections,
        promotable_to_adoption_gate=promotable,
        reasons=tuple(reasons),
        case_results=tuple(case_results),
    )
