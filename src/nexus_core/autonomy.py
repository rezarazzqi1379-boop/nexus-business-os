from dataclasses import dataclass
from typing import Literal, Sequence
from unicodedata import category

from nexus_core.capabilities import Capability, CapabilityNeed, plan_capabilities
from nexus_core.policy import ActionIntent, GateDecision, evaluate_action


WorkDomain = Literal[
    "research",
    "market_intelligence",
    "customer_network",
    "inbox_monitoring",
    "coding_learning",
    "backup",
    "knowledge_management",
    "innovation",
    "security",
    "news_monitoring",
]
PriorityTier = Literal["critical", "high", "medium", "low"]
EvidenceTier = Literal["strong", "partial", "weak"]
CostTier = Literal["low", "medium", "high"]
PlanStatus = Literal["runnable", "human_gate", "blocked"]

_ALLOWED_DOMAINS = {
    "research",
    "market_intelligence",
    "customer_network",
    "inbox_monitoring",
    "coding_learning",
    "backup",
    "knowledge_management",
    "innovation",
    "security",
    "news_monitoring",
}
_ALLOWED_PRIORITY = {"critical", "high", "medium", "low"}
_ALLOWED_EVIDENCE = {"strong", "partial", "weak"}
_ALLOWED_COST = {"low", "medium", "high"}
_PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_EVIDENCE_RANK = {"strong": 0, "partial": 1, "weak": 2}
_COST_RANK = {"low": 0, "medium": 1, "high": 2}
_MAX_META_LENGTH = 256
_MAX_OBJECTIVE_LENGTH = 2048
_DISALLOWED_UNICODE_CATEGORIES = {"Cc", "Cf", "Zl", "Zp"}


@dataclass(frozen=True)
class WorkItem:
    task_id: str
    domain: WorkDomain
    objective: str
    action_kind: str
    acceptable_capability_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    value: PriorityTier = "medium"
    urgency: PriorityTier = "medium"
    evidence: EvidenceTier = "partial"
    cost: CostTier = "medium"
    write_required: bool = False
    reversible: bool = True


@dataclass(frozen=True)
class PlannedWork:
    task: WorkItem
    status: PlanStatus
    selected_capability_ids: tuple[str, ...]
    blockers: tuple[str, ...]
    gate: GateDecision


@dataclass(frozen=True)
class AutonomyPlan:
    runnable: tuple[PlannedWork, ...]
    human_gated: tuple[PlannedWork, ...]
    blocked: tuple[PlannedWork, ...]


def _text_errors(name: str, value: object, max_length: int) -> list[str]:
    if not isinstance(value, str):
        return [f"{name} must be a string"]
    errors: list[str] = []
    if not value.strip():
        errors.append(f"{name} is required")
    if value != value.strip():
        errors.append(f"{name} cannot have leading or trailing whitespace")
    if len(value) > max_length:
        errors.append(f"{name} must be at most {max_length} characters")
    if any(category(ch) in _DISALLOWED_UNICODE_CATEGORIES for ch in value):
        errors.append(f"{name} cannot contain control or formatting characters")
    return errors


def _ref_errors(name: str, refs: object) -> list[str]:
    if not isinstance(refs, tuple):
        return [f"{name} must be a tuple"]
    if not refs:
        return [f"{name} requires at least one retrievable reference"]
    errors: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        errors.extend(_text_errors(name, ref, _MAX_META_LENGTH))
        if isinstance(ref, str):
            if ref in seen:
                errors.append(f"{name} cannot contain duplicate references")
            seen.add(ref)
    return errors


def validate_work_item(task: WorkItem) -> list[str]:
    if not isinstance(task, WorkItem):
        return ["task must be a WorkItem"]
    errors: list[str] = []
    errors.extend(_text_errors("task_id", task.task_id, _MAX_META_LENGTH))
    errors.extend(_text_errors("objective", task.objective, _MAX_OBJECTIVE_LENGTH))

    if not isinstance(task.domain, str) or task.domain not in _ALLOWED_DOMAINS:
        errors.append("domain must be supported")
    if not isinstance(task.value, str) or task.value not in _ALLOWED_PRIORITY:
        errors.append("value must be supported")
    if not isinstance(task.urgency, str) or task.urgency not in _ALLOWED_PRIORITY:
        errors.append("urgency must be supported")
    if not isinstance(task.evidence, str) or task.evidence not in _ALLOWED_EVIDENCE:
        errors.append("evidence must be supported")
    if not isinstance(task.cost, str) or task.cost not in _ALLOWED_COST:
        errors.append("cost must be supported")
    if not isinstance(task.write_required, bool):
        errors.append("write_required must be a boolean")
    if not isinstance(task.reversible, bool):
        errors.append("reversible must be a boolean")

    errors.extend(_ref_errors("evidence_refs", task.evidence_refs))

    if not isinstance(task.acceptable_capability_ids, tuple):
        errors.append("acceptable_capability_ids must be a tuple")
    elif not task.acceptable_capability_ids:
        errors.append("acceptable_capability_ids requires at least one capability")
    else:
        seen: set[str] = set()
        for capability_id in task.acceptable_capability_ids:
            errors.extend(
                _text_errors(
                    "acceptable_capability_ids",
                    capability_id,
                    _MAX_META_LENGTH,
                )
            )
            if isinstance(capability_id, str):
                if capability_id in seen:
                    errors.append("acceptable_capability_ids cannot contain duplicates")
                seen.add(capability_id)
    return errors


def _priority_key(task: WorkItem) -> tuple[object, ...]:
    """Ordinal, deterministic prioritization without pseudo-precise business scores."""
    return (
        _PRIORITY_RANK[task.value],
        _PRIORITY_RANK[task.urgency],
        _EVIDENCE_RANK[task.evidence],
        _COST_RANK[task.cost],
        task.task_id,
    )


def plan_autonomy(
    tasks: Sequence[WorkItem],
    capabilities: Sequence[Capability],
) -> AutonomyPlan:
    """Plan safe NEXUS work without executing external actions.

    The fabric chooses capabilities deterministically, preserves unresolved needs,
    and applies the canonical action-specific human gate. It is a planner, not a
    self-modifying runtime and not an authorization system.
    """
    planned: list[PlannedWork] = []

    for task in sorted(tasks, key=_priority_key):
        validation_errors = validate_work_item(task)
        gate = evaluate_action(
            ActionIntent(
                action_id=f"autonomy:{task.task_id}",
                kind=task.action_kind,  # type: ignore[arg-type]
                description=task.objective,
                reversible=task.reversible,
            )
        )
        if validation_errors:
            planned.append(
                PlannedWork(
                    task=task,
                    status="blocked",
                    selected_capability_ids=(),
                    blockers=tuple(validation_errors),
                    gate=gate,
                )
            )
            continue

        capability_plan = plan_capabilities(
            (
                CapabilityNeed(
                    need_id=task.task_id,
                    purpose=task.objective,
                    acceptable_capability_ids=task.acceptable_capability_ids,
                    write_required=task.write_required,
                ),
            ),
            capabilities,
        )
        selected_ids = tuple(cap.capability_id for cap in capability_plan.selected)
        blockers = list(capability_plan.unresolved_need_ids)

        if blockers:
            status: PlanStatus = "blocked"
        elif gate.requires_human_approval or capability_plan.approval_required_capability_ids:
            status = "human_gate"
            blockers.extend(
                f"capability approval required: {capability_id}"
                for capability_id in capability_plan.approval_required_capability_ids
            )
            if gate.requires_human_approval:
                blockers.append(gate.reason)
        elif gate.allowed_now:
            status = "runnable"
        else:
            status = "blocked"
            blockers.append(gate.reason)

        planned.append(
            PlannedWork(
                task=task,
                status=status,
                selected_capability_ids=selected_ids,
                blockers=tuple(blockers),
                gate=gate,
            )
        )

    return AutonomyPlan(
        runnable=tuple(item for item in planned if item.status == "runnable"),
        human_gated=tuple(item for item in planned if item.status == "human_gate"),
        blocked=tuple(item for item in planned if item.status == "blocked"),
    )
