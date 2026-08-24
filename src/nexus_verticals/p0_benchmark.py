from dataclasses import dataclass
from enum import IntEnum
from typing import Literal


class AuthorityLevel(IntEnum):
    A0_BINDING = 0
    A1_BUYER_CONFIRMED = 1
    A2_INTERNAL_MASTER = 2
    A3_PROJECT_VERIFIED = 3
    A4_INDEPENDENT_TECHNICAL = 4
    A5_SUPPLIER_CLAIM = 5
    A6_MARKET_RESEARCH = 6
    A7_AI_INFERENCE = 7
    A8_OTHER_PROJECT_HISTORY = 8


BenchmarkStage = Literal[
    "discovered",
    "researched",
    "verified",
    "recommended",
    "approved",
    "executed",
    "measured",
]


@dataclass(frozen=True)
class AuthorityRecord:
    record_id: str
    project_id: str
    entity_id: str
    field_name: str
    value: str
    authority_level: AuthorityLevel
    source_ref: str
    version: int = 1
    status: str = "active"

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name, value in (
            ("record_id", self.record_id),
            ("project_id", self.project_id),
            ("entity_id", self.entity_id),
            ("field_name", self.field_name),
            ("value", self.value),
            ("source_ref", self.source_ref),
            ("status", self.status),
        ):
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{name} is required")
        if not isinstance(self.authority_level, AuthorityLevel):
            errors.append("authority_level must be AuthorityLevel")
        if not isinstance(self.version, int) or isinstance(self.version, bool) or self.version < 1:
            errors.append("version must be a positive integer")
        return errors


def can_supersede(current: AuthorityRecord, candidate: AuthorityRecord) -> bool:
    """Fail closed unless candidate belongs to the same project/entity/field and has
    equal-or-stronger authority. Lower numeric enum value means stronger authority.
    """
    if current.validate() or candidate.validate():
        return False
    if (
        current.project_id != candidate.project_id
        or current.entity_id != candidate.entity_id
        or current.field_name != candidate.field_name
    ):
        return False
    if candidate.version <= current.version:
        return False
    return candidate.authority_level <= current.authority_level


@dataclass(frozen=True)
class BenchmarkObservation:
    observation_id: str
    project_id: str
    case_type: Literal["hydrotester", "can_forming"]
    stage: BenchmarkStage
    source_ref: str
    failure_mode: str
    metric_name: str
    metric_value: float
    accepted_by_human: bool | None = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name, value in (
            ("observation_id", self.observation_id),
            ("project_id", self.project_id),
            ("source_ref", self.source_ref),
            ("failure_mode", self.failure_mode),
            ("metric_name", self.metric_name),
        ):
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{name} is required")
        if self.case_type not in {"hydrotester", "can_forming"}:
            errors.append("unsupported case_type")
        if self.stage not in {
            "discovered", "researched", "verified", "recommended",
            "approved", "executed", "measured",
        }:
            errors.append("unsupported stage")
        if not isinstance(self.metric_value, (int, float)) or isinstance(self.metric_value, bool):
            errors.append("metric_value must be numeric")
        if self.accepted_by_human not in {True, False, None}:
            errors.append("accepted_by_human must be bool or None")
        return errors


@dataclass(frozen=True)
class BenchmarkPairResult:
    hydrotester: tuple[BenchmarkObservation, ...]
    can_forming: tuple[BenchmarkObservation, ...]

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.hydrotester:
            errors.append("hydrotester benchmark observations are required")
        if not self.can_forming:
            errors.append("can_forming benchmark observations are required")
        for observation in self.hydrotester:
            errors.extend(observation.validate())
            if observation.case_type != "hydrotester":
                errors.append("hydrotester bucket contains wrong case_type")
        for observation in self.can_forming:
            errors.extend(observation.validate())
            if observation.case_type != "can_forming":
                errors.append("can_forming bucket contains wrong case_type")
        return errors

    def accepted_precision(self) -> float | None:
        decisions = [
            obs.accepted_by_human
            for obs in (*self.hydrotester, *self.can_forming)
            if obs.accepted_by_human is not None
        ]
        if not decisions:
            return None
        return sum(1 for value in decisions if value is True) / len(decisions)
