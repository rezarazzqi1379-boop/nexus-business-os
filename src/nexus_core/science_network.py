from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExperimentStatus(str, Enum):
    PROPOSED = "proposed"
    READY = "ready"
    RUNNING = "running"
    KEEP = "keep"
    MODIFY = "modify"
    SCALE = "scale"
    KILL = "kill"
    NO_ACTION = "no_action"


@dataclass(frozen=True)
class ExperimentSpec:
    experiment_id: str
    hypothesis: str
    mechanism: str
    evidence_refs: tuple[str, ...]
    project_refs: tuple[str, ...]
    smallest_reversible_test: str
    success_metric: str
    failure_metric: str


@dataclass(frozen=True)
class ExperimentResult:
    experiment_id: str
    status: ExperimentStatus
    observation_refs: tuple[str, ...]
    measured_outcome: str
    learning: str


def validate_experiment(spec: ExperimentSpec) -> tuple[str, ...]:
    errors: list[str] = []
    required_text = {
        "experiment_id": spec.experiment_id,
        "hypothesis": spec.hypothesis,
        "mechanism": spec.mechanism,
        "smallest_reversible_test": spec.smallest_reversible_test,
        "success_metric": spec.success_metric,
        "failure_metric": spec.failure_metric,
    }
    for field, value in required_text.items():
        if not isinstance(value, str) or not value.strip():
            errors.append(f"missing_{field}")
    if not spec.evidence_refs or len(spec.evidence_refs) != len(set(spec.evidence_refs)):
        errors.append("invalid_evidence_refs")
    if not spec.project_refs or len(spec.project_refs) != len(set(spec.project_refs)):
        errors.append("invalid_project_refs")
    if spec.success_metric.strip() == spec.failure_metric.strip():
        errors.append("ambiguous_metrics")
    return tuple(errors)


def can_start_experiment(spec: ExperimentSpec) -> bool:
    return not validate_experiment(spec)


def validate_result(spec: ExperimentSpec, result: ExperimentResult) -> tuple[str, ...]:
    errors = list(validate_experiment(spec))
    if result.experiment_id != spec.experiment_id:
        errors.append("experiment_id_mismatch")
    if result.status in {ExperimentStatus.PROPOSED, ExperimentStatus.READY, ExperimentStatus.RUNNING}:
        errors.append("non_terminal_result_status")
    if not result.observation_refs or len(result.observation_refs) != len(set(result.observation_refs)):
        errors.append("invalid_observation_refs")
    if not result.measured_outcome.strip():
        errors.append("missing_measured_outcome")
    if not result.learning.strip():
        errors.append("missing_learning")
    return tuple(errors)
