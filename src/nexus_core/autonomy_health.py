from __future__ import annotations

from collections import Counter
from dataclasses import replace
from datetime import datetime
from typing import Sequence

from nexus_core.autonomy import AutonomyPlan, PlannedWork, WorkItem, plan_autonomy, validate_work_item
from nexus_core.capabilities import Capability
from nexus_core.capability_health import CapabilityHealth, capability_can_satisfy


# Default health freshness window: six hours.
# This is intentionally conservative. A connector that was healthy yesterday is not
# automatically considered safe enough for autonomous planning today.
_DEFAULT_MAX_AGE_SECONDS = 21_600


def _parse_now(now: str) -> datetime:
    """Parse the planner clock and reject timezone-ambiguous timestamps.

    Capability health is time-sensitive evidence. Accepting a naive datetime would make
    freshness depend on the machine's local timezone and could silently turn stale proof
    into apparently valid proof.
    """
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
    max_age_seconds: int = _DEFAULT_MAX_AGE_SECONDS,
) -> AutonomyPlan:
    """Plan work only through capabilities backed by fresh runtime health evidence.

    Architecture boundary
    ---------------------
    ``Capability`` remains the canonical registry record (what a route is supposed to
    support). ``CapabilityHealth`` is runtime evidence (what was actually proven recently).
    This function joins the two; it does not create a second capability registry or a
    second authorization system.

    Fail-closed invariants
    ----------------------
    1. Missing, malformed, duplicate, future-dated or stale health cannot satisfy work.
    2. Duplicate capability IDs are ambiguous registry state and cannot satisfy work.
    3. Read work requires explicit fresh read proof.
    4. Write work requires explicit fresh ``verified_write`` proof; registry ``can_write``
       alone is insufficient.
    5. Unhealthy candidate routes are removed *before* canonical capability selection so a
       healthy alternative can win deterministically.
    6. Action-specific Human Gates remain owned by ``plan_autonomy`` / canonical policy.

    The output is still the normal ``AutonomyPlan`` contract, so downstream code does not
    need a parallel planner model.
    """
    current = _parse_now(now)
    if not isinstance(max_age_seconds, int) or isinstance(max_age_seconds, bool) or max_age_seconds < 0:
        raise ValueError("max_age_seconds must be a non-negative integer")

    # Registry membership and runtime health are deliberately separate. A route may exist
    # in configuration while its authentication, permission, or provider state has drifted.
    # Duplicate registry IDs are also ambiguous: the planner must not let dictionary/order
    # behavior silently decide which definition owns the route.
    capability_counts = Counter(
        capability.capability_id
        for capability in capabilities
        if isinstance(capability, Capability) and isinstance(capability.capability_id, str)
    )
    capability_ids = {
        capability_id for capability_id, count in capability_counts.items() if count == 1
    }
    duplicate_capability_ids = {
        capability_id for capability_id, count in capability_counts.items() if count > 1
    }

    # Duplicate health evidence is ambiguous: we do not guess which record is authoritative.
    # Only capability IDs with exactly one record are eligible for runtime proof.
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

    # Preserve canonical priority semantics without copying its ranking tables here.
    # Planning with zero capabilities blocks valid tasks, but retains the canonical ordering.
    ordering_probe = plan_autonomy(tasks, ())
    ordered_tasks = tuple(item.task for item in ordering_probe.blocked)

    runnable: list[PlannedWork] = []
    human_gated: list[PlannedWork] = []
    blocked: list[PlannedWork] = []

    for task in ordered_tasks:
        # Invalid WorkItems must fail before health filtering or capability selection.
        if validate_work_item(task):
            result = plan_autonomy((task,), capabilities)
            blocked.extend(result.blocked)
            continue

        required_access = "write" if task.write_required else "read"
        unhealthy_ids: list[str] = []
        ambiguous_registry_ids: list[str] = []
        eligible_ids: set[str] = set()

        for capability_id in task.acceptable_capability_ids:
            if capability_id in duplicate_capability_ids:
                ambiguous_registry_ids.append(capability_id)
                continue

            # Unknown registry IDs are handled by the canonical planner as unresolved needs.
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

        # Feed only uniquely-defined, health-proven routes back into the canonical planner.
        eligible_capabilities = tuple(
            capability
            for capability in capabilities
            if capability.capability_id in eligible_ids
            and capability_counts.get(capability.capability_id) == 1
        )
        result = plan_autonomy((task,), eligible_capabilities)

        if result.runnable:
            runnable.extend(result.runnable)
        elif result.human_gated:
            human_gated.extend(result.human_gated)
        else:
            planned = result.blocked[0]
            health_blockers = tuple(
                f"capability health unavailable: {capability_id}"
                for capability_id in sorted(set(unhealthy_ids))
            )
            registry_blockers = tuple(
                f"capability registry ambiguous: {capability_id}"
                for capability_id in sorted(set(ambiguous_registry_ids))
            )
            blocked.append(
                replace(
                    planned,
                    blockers=planned.blockers + registry_blockers + health_blockers,
                )
            )

    return AutonomyPlan(tuple(runnable), tuple(human_gated), tuple(blocked))
