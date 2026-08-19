from __future__ import annotations

from collections import Counter
from dataclasses import replace
from datetime import datetime
from typing import Sequence

from nexus_core.autonomy import AutonomyPlan, PlannedWork, WorkItem, plan_autonomy, validate_work_item
from nexus_core.capabilities import Capability
from nexus_core.capability_health import CapabilityHealth, capability_can_satisfy


def _parse_now(now: str) -> datetime:
    current = datetime.fromisoformat(now.replace("Z", "+00:00"))
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("now must include a timezone offset")
    return current


def plan_autonomy_with_health(
    tasks: Sequence[WorkItem],
    capabilities: Sequence[Capability],
    health_records: Sequence[CapabilityHealth],
    *,
    now: str,
    max_age_seconds: int = 21_600,
) -> AutonomyPlan:
    """Plan autonomy work only through capabilities with fresh runtime health proof.

    This is a fail-closed integration layer over the canonical Capability Runtime.
    It does not create a second capability registry or authorization system.

    Rules:
    - missing, malformed, duplicated, future-dated or stale health cannot satisfy work;
    - read work requires fresh proven read access;
    - write work requires fresh explicit write proof;
    - unhealthy acceptable routes are removed before capability selection so a healthy
      alternative can be selected deterministically;
    - action-specific Human Gates remain owned by ``plan_autonomy`` / canonical policy.
    """
    current = _parse_now(now)
    if not isinstance(max_age_seconds, int) or isinstance(max_age_seconds, bool) or max_age_seconds < 0:
        raise ValueError("max_age_seconds must be a non-negative integer")

    capability_ids = {capability.capability_id for capability in capabilities}
    health_counts = Counter(
        record.capability_id
        for record in health_records
        if isinstance(record, CapabilityHealth) and isinstance(record.capability_id, str)
    )
    health_by_id = {
        record.capability_id: record
        for record in health_records
        if isinstance(record, CapabilityHealth)
        and isinstance(record.capability_id, str)
        and health_counts[record.capability_id] == 1
    }

    # Reuse the canonical planner's deterministic priority ordering without duplicating
    # its ranking taxonomy. With no capabilities every otherwise-valid task is blocked,
    # but the blocked queue still preserves canonical priority order.
    ordering_probe = plan_autonomy(tasks, ())
    ordered_tasks = tuple(item.task for item in ordering_probe.blocked)

    runnable: list[PlannedWork] = []
    human_gated: list[PlannedWork] = []
    blocked: list[PlannedWork] = []

    for task in ordered_tasks:
        if validate_work_item(task):
            result = plan_autonomy((task,), capabilities)
            blocked.extend(result.blocked)
            continue

        required_access = "write" if task.write_required else "read"
        unhealthy_ids: list[str] = []
        eligible_ids: set[str] = set()

        for capability_id in task.acceptable_capability_ids:
            if capability_id not in capability_ids:
                continue
            record = health_by_id.get(capability_id)
            if record is None or not capability_can_satisfy(
                record,
                required_access=required_access,
                now=current,
                max_age_seconds=max_age_seconds,
            ):
                unhealthy_ids.append(capability_id)
            else:
                eligible_ids.add(capability_id)

        eligible_capabilities = tuple(
            capability for capability in capabilities if capability.capability_id in eligible_ids
        )
        result = plan_autonomy((task,), eligible_capabilities)

        if result.runnable:
            runnable.extend(result.runnable)
        elif result.human_gated:
            human_gated.extend(result.human_gated)
        else:
            planned = result.blocked[0]
            health_blockers = tuple(
                f"capability health unavailable: {capability_id}" for capability_id in sorted(unhealthy_ids)
            )
            blocked.append(replace(planned, blockers=planned.blockers + health_blockers))

    return AutonomyPlan(tuple(runnable), tuple(human_gated), tuple(blocked))
