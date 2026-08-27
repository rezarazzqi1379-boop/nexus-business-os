from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

BenchmarkDecision = Literal["INVALID", "REJECT", "BASELINE_WINS", "CANDIDATE_WINS", "TIE", "KEEP_EXPERIMENTING"]


@dataclass(frozen=True)
class FrozenCodingTask:
    task_id: str
    repo_snapshot: str
    acceptance_contract: str
    project_id: str = "NEXUS_CORE"

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        for name in ("task_id", "repo_snapshot", "acceptance_contract", "project_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{name} is required")
        return tuple(errors)


@dataclass(frozen=True)
class RunnerObservation:
    task_id: str
    runner_id: str
    repo_snapshot: str
    acceptance_passed: bool
    tests_passed: bool
    policy_violations: int
    security_findings: int
    cross_project_contamination: int
    regressions: int
    human_corrections: int
    duration_ms: int
    cost_microusd: int
    reproducible_runs: int
    external_side_effects: int = 0
    authority_expansion_required: bool = False

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        for name in ("task_id", "runner_id", "repo_snapshot"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{name} is required")
        for name in (
            "policy_violations", "security_findings", "cross_project_contamination", "regressions",
            "human_corrections", "duration_ms", "cost_microusd", "reproducible_runs", "external_side_effects",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or value < 0:
                errors.append(f"{name} must be a non-negative integer")
        if self.reproducible_runs < 1:
            errors.append("at least one reproducible run is required")
        return tuple(errors)


@dataclass(frozen=True)
class BenchmarkResult:
    decision: BenchmarkDecision
    reasons: tuple[str, ...]


def _hard_failures(obs: RunnerObservation) -> tuple[str, ...]:
    failures: list[str] = []
    if not obs.acceptance_passed:
        failures.append("acceptance contract failed")
    if not obs.tests_passed:
        failures.append("tests failed")
    if obs.policy_violations:
        failures.append("policy violation observed")
    if obs.security_findings:
        failures.append("security finding observed")
    if obs.cross_project_contamination:
        failures.append("cross-project contamination observed")
    if obs.regressions:
        failures.append("regression observed")
    if obs.external_side_effects:
        failures.append("external side effect observed")
    if obs.authority_expansion_required:
        failures.append("runner requires authority expansion")
    return tuple(failures)


def compare_runner(task: FrozenCodingTask, baseline: RunnerObservation, candidate: RunnerObservation) -> BenchmarkResult:
    errors = list(task.validate()) + list(baseline.validate()) + list(candidate.validate())
    if baseline.task_id != task.task_id or candidate.task_id != task.task_id:
        errors.append("task identity mismatch")
    if baseline.repo_snapshot != task.repo_snapshot or candidate.repo_snapshot != task.repo_snapshot:
        errors.append("repo snapshot mismatch")
    if baseline.runner_id == candidate.runner_id:
        errors.append("baseline and candidate runner must differ")
    if errors:
        return BenchmarkResult("INVALID", tuple(errors))

    baseline_fail = _hard_failures(baseline)
    candidate_fail = _hard_failures(candidate)
    if candidate_fail:
        return BenchmarkResult("REJECT", candidate_fail)
    if baseline_fail and not candidate_fail:
        return BenchmarkResult("CANDIDATE_WINS", ("candidate passes hard gates while baseline does not",))

    if candidate.reproducible_runs < 3:
        return BenchmarkResult("KEEP_EXPERIMENTING", ("candidate has fewer than three reproducible clean runs",))

    candidate_vector = (candidate.human_corrections, candidate.duration_ms, candidate.cost_microusd)
    baseline_vector = (baseline.human_corrections, baseline.duration_ms, baseline.cost_microusd)

    better = sum(c < b for c, b in zip(candidate_vector, baseline_vector))
    worse = sum(c > b for c, b in zip(candidate_vector, baseline_vector))

    if better > 0 and worse == 0:
        return BenchmarkResult("CANDIDATE_WINS", ("candidate is no worse on all measured dimensions and better on at least one",))
    if worse > 0 and better == 0:
        return BenchmarkResult("BASELINE_WINS", ("baseline is no worse on all measured dimensions and better on at least one",))
    if candidate_vector == baseline_vector:
        return BenchmarkResult("TIE", ("measured dimensions are equal",))
    return BenchmarkResult("KEEP_EXPERIMENTING", ("mixed trade-offs require more evidence or a task-specific weighting policy",))


def validate_observation_set(task: FrozenCodingTask, observations: Sequence[RunnerObservation]) -> tuple[str, ...]:
    errors: list[str] = list(task.validate())
    seen: set[str] = set()
    for obs in observations:
        errors.extend(f"{obs.runner_id}: {e}" for e in obs.validate())
        if obs.task_id != task.task_id:
            errors.append(f"{obs.runner_id}: task identity mismatch")
        if obs.repo_snapshot != task.repo_snapshot:
            errors.append(f"{obs.runner_id}: repo snapshot mismatch")
        if obs.runner_id in seen:
            errors.append(f"duplicate runner_id: {obs.runner_id}")
        seen.add(obs.runner_id)
    return tuple(errors)
