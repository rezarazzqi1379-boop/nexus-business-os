from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Mapping

from nexus_core.access_authority_registry import ActionClass, ConnectorAccess, decide_authority


class OperatorDisposition(str, Enum):
    EXECUTE_INTERNAL = "EXECUTE_INTERNAL"
    PREPARE_APPROVAL = "PREPARE_APPROVAL"
    REFRESH_ACCESS = "REFRESH_ACCESS"
    HOLD = "HOLD"


@dataclass(frozen=True)
class AccessObservation:
    access: ConnectorAccess
    observed_at: datetime
    max_age: timedelta = timedelta(hours=24)

    def validate(self) -> tuple[str, ...]:
        errors = list(self.access.validate())
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            errors.append("observed_at must be timezone-aware")
        if self.max_age <= timedelta(0):
            errors.append("max_age must be positive")
        return tuple(errors)

    def is_fresh(self, now: datetime) -> bool:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        return now <= self.observed_at + self.max_age


@dataclass(frozen=True)
class DelegatedWork:
    work_id: str
    project_id: str
    connector: str
    action_class: ActionClass
    reversible: bool
    payload_digest: str

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        for field in ("work_id", "project_id", "connector", "payload_digest"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{field} required")
        if self.action_class is ActionClass.INTERNAL_WRITE and not self.reversible:
            errors.append("internal write must be reversible")
        return tuple(errors)


@dataclass(frozen=True)
class OperatorDecision:
    disposition: OperatorDisposition
    exact_approval_required: bool
    reasons: tuple[str, ...]


def route_delegated_work(
    work: DelegatedWork,
    observations: Mapping[str, AccessObservation],
    *,
    now: datetime | None = None,
) -> OperatorDecision:
    """Route work through live access evidence without granting new authority.

    This is a routing layer only. It does not execute connectors, consume approvals,
    mutate production, or change project governance. Consequential work is prepared
    for the canonical exact-approval path; stale access observations are refreshed first.
    """
    errors = work.validate()
    if errors:
        return OperatorDecision(OperatorDisposition.HOLD, False, errors)

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        return OperatorDecision(OperatorDisposition.HOLD, False, ("now must be timezone-aware",))

    key = work.connector.strip().lower()
    observation = observations.get(key)
    if observation is None:
        return OperatorDecision(
            OperatorDisposition.REFRESH_ACCESS,
            False,
            ("no live access observation for connector",),
        )

    observation_errors = observation.validate()
    if observation_errors:
        return OperatorDecision(OperatorDisposition.HOLD, False, observation_errors)
    if observation.access.connector.strip().lower() != key:
        return OperatorDecision(
            OperatorDisposition.HOLD,
            False,
            ("connector observation binding mismatch",),
        )
    if not observation.is_fresh(current):
        return OperatorDecision(
            OperatorDisposition.REFRESH_ACCESS,
            False,
            ("connector access observation is stale",),
        )

    authority = decide_authority(observation.access, work.action_class)
    if authority.allowed:
        if work.action_class not in {ActionClass.READ, ActionClass.INTERNAL_WRITE}:
            return OperatorDecision(
                OperatorDisposition.HOLD,
                True,
                ("unexpected authority expansion rejected",),
            )
        return OperatorDecision(
            OperatorDisposition.EXECUTE_INTERNAL,
            False,
            authority.reasons,
        )

    if authority.exact_approval_required:
        return OperatorDecision(
            OperatorDisposition.PREPARE_APPROVAL,
            True,
            authority.reasons,
        )

    return OperatorDecision(OperatorDisposition.HOLD, False, authority.reasons)
