from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from nexus_control_plane.forge_failure_memory import FailureSeverity, relevant_failures


class MemoryIntervention(str, Enum):
    SILENT = "silent"
    REMIND = "remind"
    VERIFY_FIRST = "verify_first"
    HOLD = "hold"


@dataclass(frozen=True)
class MemoryInterventionRequest:
    concern: str
    project_id: str
    applicability_match: bool
    memory_fresh: bool
    dynamic_state: bool
    consequential: bool
    trajectory_binding_changed: bool = False


@dataclass(frozen=True)
class MemoryInterventionDecision:
    intervention: MemoryIntervention
    failure_refs: tuple[str, ...]
    required_checks: tuple[str, ...]
    reason: str
    action_authorized: bool = False


def _clean(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def evaluate_memory_intervention(request: MemoryInterventionRequest) -> MemoryInterventionDecision:
    """Selectively surface memory without treating memory as authority.

    The gate is intentionally advisory/containment-only. It never authorizes an
    external or consequential action. Stale or binding-shifted memory triggers
    verification rather than direct trajectory reuse.
    """
    if not isinstance(request, MemoryInterventionRequest):
        raise TypeError("request must be MemoryInterventionRequest")
    if not _clean(request.concern) or not _clean(request.project_id):
        raise ValueError("concern and project_id must be normalized non-empty strings")
    for name in ("applicability_match", "memory_fresh", "dynamic_state", "consequential", "trajectory_binding_changed"):
        if not isinstance(getattr(request, name), bool):
            raise ValueError(f"{name} must be boolean")

    failures = relevant_failures(request.concern)
    refs = tuple(pattern.failure_id for pattern in failures)
    checks = tuple(dict.fromkeys(check for pattern in failures for check in pattern.required_checks))

    if not request.applicability_match:
        return MemoryInterventionDecision(
            MemoryIntervention.SILENT,
            refs,
            checks,
            "retrieved memory does not match the current task/project applicability conditions",
        )
    if request.trajectory_binding_changed:
        return MemoryInterventionDecision(
            MemoryIntervention.VERIFY_FIRST,
            refs,
            tuple(dict.fromkeys(checks + ("rebind_current_entities", "verify_current_constraints"))),
            "past trajectory bindings changed; reuse procedure only after rebinding and verification",
        )
    if request.dynamic_state and not request.memory_fresh:
        return MemoryInterventionDecision(
            MemoryIntervention.VERIFY_FIRST,
            refs,
            tuple(dict.fromkeys(checks + ("refresh_dynamic_state",))),
            "dynamic memory is stale and must be refreshed against ground truth",
        )

    severe = any(pattern.severity in {FailureSeverity.CRITICAL, FailureSeverity.HIGH} for pattern in failures)
    if request.consequential and severe:
        return MemoryInterventionDecision(
            MemoryIntervention.REMIND,
            refs,
            checks,
            "relevant high-severity failure history should be injected before consequential reasoning",
        )
    if failures:
        return MemoryInterventionDecision(
            MemoryIntervention.REMIND,
            refs,
            checks,
            "relevant prior failure history should be surfaced selectively",
        )
    return MemoryInterventionDecision(
        MemoryIntervention.SILENT,
        (),
        (),
        "no relevant failure memory requires intervention",
    )
