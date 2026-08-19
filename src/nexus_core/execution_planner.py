from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal


StepKind = Literal["read", "research", "draft", "code", "test", "record", "external"]
_ALLOWED_KINDS = {"read", "research", "draft", "code", "test", "record", "external"}


@dataclass(frozen=True)
class ExecutionStep:
    step_id: str
    kind: StepKind
    objective: str
    depends_on: tuple[str, ...] = ()
    reversible: bool = True
    human_gate: bool = False


@dataclass(frozen=True)
class ExecutionPlan:
    runnable: tuple[ExecutionStep, ...]
    gated: tuple[ExecutionStep, ...]
    blocked: tuple[tuple[ExecutionStep, tuple[str, ...]], ...]


def _validate(step: ExecutionStep) -> tuple[str, ...]:
    errors: list[str] = []
    if not isinstance(step, ExecutionStep):
        return ("invalid_step_type",)
    if not isinstance(step.step_id, str) or not step.step_id.strip():
        errors.append("invalid_step_id")
    if not isinstance(step.kind, str) or step.kind not in _ALLOWED_KINDS:
        errors.append("invalid_kind")
    if not isinstance(step.objective, str) or not step.objective.strip():
        errors.append("invalid_objective")
    if not isinstance(step.depends_on, tuple):
        errors.append("invalid_depends_on_type")
    elif any(not isinstance(dep, str) or not dep.strip() for dep in step.depends_on):
        errors.append("invalid_dependency")
    elif len(step.depends_on) != len(set(step.depends_on)):
        errors.append("duplicate_dependency")
    if not isinstance(step.reversible, bool):
        errors.append("invalid_reversible")
    if not isinstance(step.human_gate, bool):
        errors.append("invalid_human_gate")
    if step.kind == "external" and not step.human_gate:
        errors.append("external_step_requires_human_gate")
    if step.reversible is False and not step.human_gate:
        errors.append("irreversible_step_requires_human_gate")
    return tuple(errors)


def build_execution_plan(steps: Iterable[ExecutionStep]) -> ExecutionPlan:
    items = tuple(steps)
    seen: set[str] = set()
    valid: dict[str, ExecutionStep] = {}
    blocked: list[tuple[ExecutionStep, tuple[str, ...]]] = []

    for step in items:
        errors = list(_validate(step))
        if isinstance(step, ExecutionStep) and isinstance(step.step_id, str) and step.step_id in seen:
            errors.append("duplicate_step_id")
        if errors:
            blocked.append((step, tuple(errors)))
            continue
        seen.add(step.step_id)
        valid[step.step_id] = step

    for step_id, step in tuple(valid.items()):
        missing = tuple(dep for dep in step.depends_on if dep not in valid)
        if missing:
            blocked.append((step, tuple(f"missing_dependency:{dep}" for dep in missing)))
            valid.pop(step_id)

    # Detect dependency cycles without executing anything.
    visiting: set[str] = set()
    visited: set[str] = set()
    cyclic: set[str] = set()

    def visit(step_id: str) -> None:
        if step_id in visited or step_id not in valid:
            return
        if step_id in visiting:
            cyclic.update(visiting)
            return
        visiting.add(step_id)
        for dep in valid[step_id].depends_on:
            visit(dep)
        visiting.discard(step_id)
        visited.add(step_id)

    for step_id in tuple(valid):
        visit(step_id)

    for step_id in sorted(cyclic):
        if step_id in valid:
            step = valid.pop(step_id)
            blocked.append((step, ("dependency_cycle",)))

    ordered: list[ExecutionStep] = []
    remaining = dict(valid)
    completed: set[str] = set()
    while remaining:
        ready = sorted(
            (step for step in remaining.values() if set(step.depends_on) <= completed),
            key=lambda step: step.step_id,
        )
        if not ready:
            for step in remaining.values():
                blocked.append((step, ("unresolvable_dependency_graph",)))
            break
        for step in ready:
            ordered.append(step)
            completed.add(step.step_id)
            remaining.pop(step.step_id)

    runnable = tuple(step for step in ordered if not step.human_gate)
    gated = tuple(step for step in ordered if step.human_gate)
    return ExecutionPlan(runnable=runnable, gated=gated, blocked=tuple(blocked))
