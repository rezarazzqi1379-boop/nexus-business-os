from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ConstraintKind(str, Enum):
    POLICY = "policy"
    PERMISSION = "permission"
    SECURITY = "security"
    BILLING = "billing"
    QUOTA = "quota"
    CONNECTIVITY = "connectivity"
    CAPABILITY = "capability"
    DATA = "data"
    RELIABILITY = "reliability"
    HUMAN_GATE = "human_gate"


class Decision(str, Enum):
    RESPECT_BOUNDARY = "respect_boundary"
    CONFIGURE = "configure"
    USE_EXISTING = "use_existing"
    BUILD_ADAPTER = "build_adapter"
    BUILD_PROOF = "build_proof"
    DEFER = "defer"


_HARD_BOUNDARIES = {
    ConstraintKind.POLICY,
    ConstraintKind.PERMISSION,
    ConstraintKind.SECURITY,
    ConstraintKind.BILLING,
    ConstraintKind.HUMAN_GATE,
}


@dataclass(frozen=True)
class Constraint:
    constraint_id: str
    title: str
    kind: ConstraintKind
    evidence: str
    value_blocked: int
    recurrence: int
    existing_option_score: int
    build_cost: int
    maintenance_cost: int
    risk: int
    owner: str
    success_metric: str
    rollback: str
    status: str = "observed"

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Constraint":
        if not isinstance(raw, dict):
            raise ValueError("constraint_must_be_mapping")
        data = dict(raw)
        try:
            data["kind"] = ConstraintKind(data["kind"])
            item = cls(**data)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid_constraint") from exc

        for field in (
            "value_blocked",
            "recurrence",
            "existing_option_score",
            "build_cost",
            "maintenance_cost",
            "risk",
        ):
            value = getattr(item, field)
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 5:
                raise ValueError(f"invalid_{field}")
        for field in (
            "constraint_id",
            "title",
            "evidence",
            "owner",
            "success_metric",
            "rollback",
            "status",
        ):
            value = getattr(item, field)
            if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 512:
                raise ValueError(f"invalid_{field}")
        return item


@dataclass(frozen=True)
class ConstraintDecision:
    constraint_id: str
    decision: Decision
    reason: str
    requires_human_gate: bool


def evaluate_constraint(item: Constraint) -> ConstraintDecision:
    """Route a verified limitation without weakening policy or safety boundaries."""
    if not isinstance(item, Constraint):
        raise ValueError("invalid_constraint")
    if item.kind in _HARD_BOUNDARIES:
        return ConstraintDecision(
            item.constraint_id,
            Decision.RESPECT_BOUNDARY,
            "Use approved access or exact human confirmation; do not bypass the boundary.",
            True,
        )

    if item.existing_option_score >= 4:
        return ConstraintDecision(
            item.constraint_id,
            Decision.USE_EXISTING,
            "A supported existing option is preferable to new code.",
            False,
        )

    value = item.value_blocked + item.recurrence
    burden = item.build_cost + item.maintenance_cost + item.risk

    if item.kind in {ConstraintKind.CONNECTIVITY, ConstraintKind.DATA} and value > burden:
        decision = Decision.BUILD_ADAPTER
        reason = "Build a narrow reversible adapter and measure the blocked workflow."
    elif value >= burden + 2:
        decision = Decision.BUILD_PROOF
        reason = "Build only a measured proof before production admission."
    elif item.kind == ConstraintKind.QUOTA and item.existing_option_score >= 2:
        decision = Decision.CONFIGURE
        reason = "Batch, cache, reduce demand, or use a supported plan."
    else:
        decision = Decision.DEFER
        reason = "Expected value does not justify build and maintenance cost."

    return ConstraintDecision(item.constraint_id, decision, reason, False)


def audit_constraints(records: list[dict[str, Any]]) -> tuple[ConstraintDecision, ...]:
    """Validate and audit a bounded batch; duplicate identities fail closed."""
    if not isinstance(records, list) or len(records) > 1_000:
        raise ValueError("invalid_constraint_batch")
    constraints = tuple(Constraint.from_dict(record) for record in records)
    identities = [item.constraint_id for item in constraints]
    if len(identities) != len(set(identities)):
        raise ValueError("duplicate_constraint_id")
    return tuple(evaluate_constraint(item) for item in constraints)
