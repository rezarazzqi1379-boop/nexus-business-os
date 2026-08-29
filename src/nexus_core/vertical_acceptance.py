from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class TraceEnvelope:
    workflow_name: str
    project_id: str
    candidate_id: str
    run_id: str
    data_classification: str
    sensitive_payload_captured: bool = False

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        for field in ("workflow_name", "project_id", "candidate_id", "run_id", "data_classification"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{field} required")
        if self.sensitive_payload_captured:
            errors.append("sensitive payload capture is forbidden for governed evaluation traces")
        return tuple(errors)


@dataclass(frozen=True)
class VerticalRunObservation:
    trace: TraceEnvelope
    decisions: int
    human_corrections: int
    unknowns_presented: int
    unknowns_blocked: int
    duplicate_attempts: int
    duplicates_prevented: int
    decision_time_ms: int | None
    policy_violations: int = 0
    cross_project_leaks: int = 0
    external_effects: int = 0

    def validate(self) -> tuple[str, ...]:
        errors = list(self.trace.validate())
        count_fields = (
            "decisions",
            "human_corrections",
            "unknowns_presented",
            "unknowns_blocked",
            "duplicate_attempts",
            "duplicates_prevented",
            "policy_violations",
            "cross_project_leaks",
            "external_effects",
        )
        for field in count_fields:
            value = getattr(self, field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append(f"{field} must be a non-negative integer")
        if self.decision_time_ms is not None and (
            not isinstance(self.decision_time_ms, int)
            or isinstance(self.decision_time_ms, bool)
            or self.decision_time_ms < 0
        ):
            errors.append("decision_time_ms must be a non-negative integer or None")
        if isinstance(self.decisions, int) and not isinstance(self.decisions, bool) and self.decisions <= 0:
            errors.append("decisions must be greater than zero")
        if isinstance(self.human_corrections, int) and isinstance(self.decisions, int) and self.human_corrections > self.decisions:
            errors.append("human_corrections cannot exceed decisions")
        if isinstance(self.unknowns_blocked, int) and isinstance(self.unknowns_presented, int) and self.unknowns_blocked > self.unknowns_presented:
            errors.append("unknowns_blocked cannot exceed unknowns_presented")
        if isinstance(self.duplicates_prevented, int) and isinstance(self.duplicate_attempts, int) and self.duplicates_prevented > self.duplicate_attempts:
            errors.append("duplicates_prevented cannot exceed duplicate_attempts")
        return tuple(errors)


@dataclass(frozen=True)
class VerticalAcceptancePolicy:
    min_runs: int
    max_correction_rate: float
    min_unknown_block_rate: float
    min_duplicate_prevention_rate: float
    max_mean_decision_time_ms: int

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not isinstance(self.min_runs, int) or isinstance(self.min_runs, bool) or self.min_runs <= 0:
            errors.append("min_runs must be a positive integer")
        for field in ("max_correction_rate", "min_unknown_block_rate", "min_duplicate_prevention_rate"):
            value = getattr(self, field)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= float(value) <= 1:
                errors.append(f"{field} must be between 0 and 1")
        if (
            not isinstance(self.max_mean_decision_time_ms, int)
            or isinstance(self.max_mean_decision_time_ms, bool)
            or self.max_mean_decision_time_ms <= 0
        ):
            errors.append("max_mean_decision_time_ms must be a positive integer")
        return tuple(errors)


@dataclass(frozen=True)
class VerticalAcceptanceResult:
    verdict: str
    run_count: int
    correction_rate: float
    unknown_block_rate: float | None
    duplicate_prevention_rate: float | None
    mean_decision_time_ms: float | None
    reasons: tuple[str, ...]


def assess_vertical_runs(
    project_id: str,
    candidate_id: str,
    runs: Sequence[VerticalRunObservation],
    policy: VerticalAcceptancePolicy,
) -> VerticalAcceptanceResult:
    """Measure a real vertical without granting production or external-action authority.

    Invalid, duplicate, cross-project, mismatched, policy-violating or externally
    effectful observations never contribute to quality metrics. Missing measurements
    remain explicitly unknown and cannot satisfy a positive acceptance threshold.
    Passing only permits the next governed adoption gate.
    """
    policy_errors = policy.validate()
    if policy_errors:
        return VerticalAcceptanceResult("INVALID", 0, 1.0, None, None, None, policy_errors)
    if not project_id.strip() or not candidate_id.strip():
        return VerticalAcceptanceResult("INVALID", 0, 1.0, None, None, None, ("project_id and candidate_id required",))
    if not runs:
        return VerticalAcceptanceResult("INVALID", 0, 1.0, None, None, None, ("at least one run required",))

    reasons: list[str] = []
    seen_run_ids: set[str] = set()
    valid_runs: list[VerticalRunObservation] = []

    for run in runs:
        run_id = run.trace.run_id or "<missing-run-id>"
        errors = run.validate()
        if errors:
            reasons.extend(f"{run_id}: {error}" for error in errors)
            continue
        if run.trace.run_id in seen_run_ids:
            reasons.append(f"{run.trace.run_id}: duplicate run_id")
            continue
        seen_run_ids.add(run.trace.run_id)
        if run.trace.project_id != project_id:
            reasons.append(f"{run.trace.run_id}: cross-project run rejected")
            continue
        if run.trace.candidate_id != candidate_id:
            reasons.append(f"{run.trace.run_id}: candidate mismatch")
            continue
        if run.policy_violations:
            reasons.append(f"{run.trace.run_id}: policy violation observed")
            continue
        if run.cross_project_leaks:
            reasons.append(f"{run.trace.run_id}: cross-project leak observed")
            continue
        if run.external_effects:
            reasons.append(f"{run.trace.run_id}: evaluation run caused external effects")
            continue
        valid_runs.append(run)

    total_decisions = sum(run.decisions for run in valid_runs)
    total_corrections = sum(run.human_corrections for run in valid_runs)
    total_unknowns = sum(run.unknowns_presented for run in valid_runs)
    total_unknowns_blocked = sum(run.unknowns_blocked for run in valid_runs)
    total_duplicates = sum(run.duplicate_attempts for run in valid_runs)
    total_duplicates_prevented = sum(run.duplicates_prevented for run in valid_runs)
    measured_times = [run.decision_time_ms for run in valid_runs if run.decision_time_ms is not None]

    valid_run_count = len(valid_runs)
    correction_rate = total_corrections / total_decisions if total_decisions else 1.0
    unknown_block_rate = total_unknowns_blocked / total_unknowns if total_unknowns else None
    duplicate_prevention_rate = total_duplicates_prevented / total_duplicates if total_duplicates else None
    mean_decision_time_ms = sum(measured_times) / len(measured_times) if measured_times else None

    if valid_run_count < policy.min_runs:
        reasons.append(f"requires at least {policy.min_runs} valid runs")
    if correction_rate > policy.max_correction_rate:
        reasons.append("human correction rate exceeds policy")
    if policy.min_unknown_block_rate > 0 and unknown_block_rate is None:
        reasons.append("unknown blocking is unmeasured")
    elif unknown_block_rate is not None and unknown_block_rate < policy.min_unknown_block_rate:
        reasons.append("unknown block rate below policy")
    if policy.min_duplicate_prevention_rate > 0 and duplicate_prevention_rate is None:
        reasons.append("duplicate prevention is unmeasured")
    elif duplicate_prevention_rate is not None and duplicate_prevention_rate < policy.min_duplicate_prevention_rate:
        reasons.append("duplicate prevention rate below policy")
    if mean_decision_time_ms is None:
        reasons.append("decision time is unmeasured")
    elif mean_decision_time_ms > policy.max_mean_decision_time_ms:
        reasons.append("mean decision time exceeds policy")

    verdict = "PASS" if not reasons else "FAIL"
    if verdict == "PASS":
        reasons.append("measured vertical passed; eligible for next governed adoption gate only")
    return VerticalAcceptanceResult(
        verdict=verdict,
        run_count=valid_run_count,
        correction_rate=correction_rate,
        unknown_block_rate=unknown_block_rate,
        duplicate_prevention_rate=duplicate_prevention_rate,
        mean_decision_time_ms=mean_decision_time_ms,
        reasons=tuple(reasons),
    )
