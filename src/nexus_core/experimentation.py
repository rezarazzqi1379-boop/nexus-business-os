from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence


ExperimentStatus = Literal["proposed", "running", "passed", "failed", "killed"]
EvidenceClass = Literal["fact", "claim", "estimate", "hypothesis", "unknown"]


@dataclass(frozen=True)
class ExperimentSpec:
    experiment_id: str
    domain: str
    hypothesis: str
    mechanism: str
    evidence_class: EvidenceClass
    evidence_refs: tuple[str, ...]
    success_metric: str
    failure_metric: str
    reversibility: bool
    status: ExperimentStatus = "proposed"


@dataclass(frozen=True)
class ExperimentResult:
    experiment_id: str
    status: ExperimentStatus
    observed_signal: str
    evidence_refs: tuple[str, ...]
    recommendation: Literal["keep", "modify", "scale", "kill", "no_action"]


def validate_experiment(spec: ExperimentSpec) -> list[str]:
    if not isinstance(spec, ExperimentSpec):
        return ["experiment must be an ExperimentSpec"]
    errors: list[str] = []
    for name, value in (
        ("experiment_id", spec.experiment_id),
        ("domain", spec.domain),
        ("hypothesis", spec.hypothesis),
        ("mechanism", spec.mechanism),
        ("success_metric", spec.success_metric),
        ("failure_metric", spec.failure_metric),
    ):
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{name} is required")
    if not isinstance(spec.reversibility, bool):
        errors.append("reversibility must be boolean")
    if spec.evidence_class not in {"fact", "claim", "estimate", "hypothesis", "unknown"}:
        errors.append("evidence_class must be supported")
    if not isinstance(spec.evidence_refs, tuple) or not spec.evidence_refs:
        errors.append("evidence_refs requires at least one retrievable reference")
    if spec.status not in {"proposed", "running", "passed", "failed", "killed"}:
        errors.append("status must be supported")
    return errors


def select_experiments(specs: Sequence[ExperimentSpec]) -> tuple[ExperimentSpec, ...]:
    valid = [spec for spec in specs if not validate_experiment(spec)]
    # Deterministic order: reversible first, then stronger epistemic footing, then ID.
    rank = {"fact": 0, "claim": 1, "estimate": 2, "hypothesis": 3, "unknown": 4}
    return tuple(sorted(valid, key=lambda s: (not s.reversibility, rank[s.evidence_class], s.experiment_id)))


def record_result(spec: ExperimentSpec, *, passed: bool, observed_signal: str, evidence_refs: tuple[str, ...]) -> ExperimentResult:
    errors = validate_experiment(spec)
    if errors:
        raise ValueError("; ".join(errors))
    if not isinstance(observed_signal, str) or not observed_signal.strip():
        raise ValueError("observed_signal is required")
    if not evidence_refs:
        raise ValueError("result evidence_refs are required")
    status: ExperimentStatus = "passed" if passed else "failed"
    recommendation = "keep" if passed else "modify"
    return ExperimentResult(spec.experiment_id, status, observed_signal, evidence_refs, recommendation)
