"""Capacity-multiplier planning for NEXUS.

This module identifies work that can be delegated to bounded helpers (worker,
scheduler, cache/index, connector or experimental app) without silently
broadening authorization. Delegation is an efficiency decision, not an
authorization decision.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class HelperKind(str, Enum):
    WORKER = "worker"
    SCHEDULER = "scheduler"
    CACHE = "cache"
    INDEX = "index"
    CONNECTOR = "connector"
    EXPERIMENTAL_APP = "experimental_app"


@dataclass(frozen=True)
class CapacityTask:
    task_id: str
    repeat_frequency: int
    estimated_minutes: int
    deterministic: bool
    consequential_external_action: bool = False
    sensitive: bool = False


@dataclass(frozen=True)
class DelegationCandidate:
    task_id: str
    helper_kind: HelperKind
    estimated_minutes_saved: int
    requires_human_gate: bool
    reason: str


def plan_capacity_multiplier(tasks: Iterable[CapacityTask]) -> tuple[DelegationCandidate, ...]:
    """Return bounded delegation candidates ranked by expected capacity gain.

    Consequential external actions are never made autonomous here. Sensitive
    work can be delegated only to internal workers and remains human-gated when
    consequential.
    """
    candidates: list[DelegationCandidate] = []
    for task in tasks:
        if not task.task_id or task.repeat_frequency < 1 or task.estimated_minutes < 1:
            continue
        saved = task.repeat_frequency * task.estimated_minutes
        if task.deterministic and task.repeat_frequency >= 2:
            kind = HelperKind.WORKER if task.sensitive else HelperKind.SCHEDULER
            reason = "repeated deterministic work can be precomputed or scheduled"
        elif task.repeat_frequency >= 3:
            kind = HelperKind.CACHE
            reason = "repeated retrieval/analysis can benefit from reusable cached state"
        else:
            continue
        candidates.append(DelegationCandidate(
            task_id=task.task_id,
            helper_kind=kind,
            estimated_minutes_saved=saved,
            requires_human_gate=task.consequential_external_action,
            reason=reason,
        ))
    return tuple(sorted(candidates, key=lambda c: (-c.estimated_minutes_saved, c.task_id)))
