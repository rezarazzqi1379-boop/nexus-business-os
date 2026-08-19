from dataclasses import dataclass
from itertools import combinations
from typing import Literal, Sequence


CapabilityStatus = Literal[
    "available",
    "degraded",
    "blocked",
    "candidate",
    "not_connected",
]
ApprovalMode = Literal[
    "none",
    "human_before_external_write",
    "human_before_irreversible",
]

_ALLOWED_STATUSES = {
    "available",
    "degraded",
    "blocked",
    "candidate",
    "not_connected",
}
_ALLOWED_APPROVAL_MODES = {
    "none",
    "human_before_external_write",
    "human_before_irreversible",
}
_EXECUTABLE_STATUSES = {"available", "degraded"}
_STATUS_RANK = {"available": 0, "degraded": 1}


@dataclass(frozen=True)
class Capability:
    capability_id: str
    purpose: str
    systems: tuple[str, ...]
    can_read: bool
    can_write: bool
    status: CapabilityStatus
    approval_mode: ApprovalMode = "none"
    proof_ref: str = ""
    notes: str = ""


@dataclass(frozen=True)
class CapabilityNeed:
    need_id: str
    purpose: str
    acceptable_capability_ids: tuple[str, ...]
    write_required: bool = False


@dataclass(frozen=True)
class CapabilityPlan:
    selected: tuple[Capability, ...]
    unresolved_need_ids: tuple[str, ...]
    approval_required_capability_ids: tuple[str, ...]


def validate_capabilities(capabilities: Sequence[Capability]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()

    for capability in capabilities:
        capability_id = capability.capability_id.strip()
        purpose = capability.purpose.strip()

        if not capability_id:
            errors.append("capability_id is required")
        elif capability_id in seen_ids:
            errors.append(f"duplicate capability_id: {capability_id}")
        else:
            seen_ids.add(capability_id)

        if not purpose:
            errors.append(f"capability {capability_id or '<missing>'} purpose is required")

        if not capability.systems or any(not system.strip() for system in capability.systems):
            errors.append(
                f"capability {capability_id or '<missing>'} needs nonblank system identifiers"
            )

        if capability.status not in _ALLOWED_STATUSES:
            errors.append(f"capability {capability_id or '<missing>'} has unsupported status")

        if capability.approval_mode not in _ALLOWED_APPROVAL_MODES:
            errors.append(
                f"capability {capability_id or '<missing>'} has unsupported approval_mode"
            )

        if capability.status in _EXECUTABLE_STATUSES and not capability.proof_ref.strip():
            errors.append(
                f"capability {capability_id or '<missing>'} needs proof_ref when status is {capability.status}"
            )

        if capability.can_write and capability.status == "not_connected":
            errors.append(
                f"capability {capability_id or '<missing>'} cannot advertise writes while not_connected"
            )

    return errors


def validate_needs(needs: Sequence[CapabilityNeed]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()

    for need in needs:
        need_id = need.need_id.strip()
        if not need_id:
            errors.append("need_id is required")
        elif need_id in seen_ids:
            errors.append(f"duplicate need_id: {need_id}")
        else:
            seen_ids.add(need_id)

        if not need.purpose.strip():
            errors.append(f"need {need_id or '<missing>'} purpose is required")

        if not need.acceptable_capability_ids:
            errors.append(
                f"need {need_id or '<missing>'} requires at least one acceptable capability"
            )

    return errors


def _can_satisfy(need: CapabilityNeed, capability: Capability) -> bool:
    if capability.capability_id not in need.acceptable_capability_ids:
        return False
    if capability.status not in _EXECUTABLE_STATUSES:
        return False
    if need.write_required and not capability.can_write:
        return False
    if not need.write_required and not (capability.can_read or capability.can_write):
        return False
    return True


def plan_capabilities(
    needs: Sequence[CapabilityNeed],
    capabilities: Sequence[Capability],
) -> CapabilityPlan:
    """Build a deterministic, reliability-first capability plan.

    Planning policy:
    - only available/degraded capabilities are executable;
    - write needs cannot resolve to read-only capabilities;
    - plans with fewer degraded capabilities are preferred;
    - among equally reliable plans, fewer capabilities are preferred;
    - among remaining ties, fewer approval-gated capabilities and lexical IDs win;
    - unresolved needs are surfaced instead of inventing a connector.

    The exact subset search is intentional: the live NEXUS registry is small, and a
    deterministic minimal plan is more valuable here than adding a general optimizer.
    """
    by_id = {capability.capability_id: capability for capability in capabilities}
    candidate_ids_by_need: dict[str, tuple[str, ...]] = {}
    unresolved: list[str] = []

    for need in needs:
        candidate_ids = tuple(
            capability_id
            for capability_id in need.acceptable_capability_ids
            if capability_id in by_id and _can_satisfy(need, by_id[capability_id])
        )
        if not candidate_ids:
            unresolved.append(need.need_id)
        else:
            candidate_ids_by_need[need.need_id] = candidate_ids

    resolvable_needs = [
        need for need in needs if need.need_id in candidate_ids_by_need
    ]
    usable_ids = sorted(
        {
            capability_id
            for candidate_ids in candidate_ids_by_need.values()
            for capability_id in candidate_ids
        }
    )

    best_combo: tuple[str, ...] = ()
    best_score: tuple[object, ...] | None = None

    for combo_size in range(1, len(usable_ids) + 1):
        for combo in combinations(usable_ids, combo_size):
            combo_set = set(combo)
            if not all(
                combo_set.intersection(candidate_ids_by_need[need.need_id])
                for need in resolvable_needs
            ):
                continue

            degraded_count = sum(
                1 for capability_id in combo if by_id[capability_id].status == "degraded"
            )
            approval_count = sum(
                1
                for capability_id in combo
                if by_id[capability_id].approval_mode != "none"
            )
            score: tuple[object, ...] = (
                degraded_count,
                combo_size,
                approval_count,
                combo,
            )
            if best_score is None or score < best_score:
                best_score = score
                best_combo = combo

        if best_score is not None and best_score[0] == 0:
            # Once an all-available plan exists at this size, larger all-available plans
            # cannot improve the capability-count objective.
            break

    selected = tuple(by_id[capability_id] for capability_id in best_combo)
    selected_ids = set(best_combo)

    approval_required: set[str] = set()
    for need in resolvable_needs:
        if not need.write_required:
            continue
        for capability_id in candidate_ids_by_need[need.need_id]:
            if capability_id in selected_ids and by_id[capability_id].approval_mode != "none":
                approval_required.add(capability_id)

    return CapabilityPlan(
        selected=selected,
        unresolved_need_ids=tuple(unresolved),
        approval_required_capability_ids=tuple(sorted(approval_required)),
    )
