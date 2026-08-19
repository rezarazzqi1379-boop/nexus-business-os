from dataclasses import dataclass
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

        if not capability.systems:
            errors.append(f"capability {capability_id or '<missing>'} needs at least one system")

        if capability.status in {"available", "degraded"} and not capability.proof_ref.strip():
            errors.append(
                f"capability {capability_id or '<missing>'} needs proof_ref when status is {capability.status}"
            )

        if capability.can_write and capability.status == "not_connected":
            errors.append(
                f"capability {capability_id or '<missing>'} cannot advertise writes while not_connected"
            )

    return errors


def plan_capabilities(
    needs: Sequence[CapabilityNeed],
    capabilities: Sequence[Capability],
) -> CapabilityPlan:
    """Select the smallest currently usable capability set for the declared needs.

    Resolution policy:
    - available capabilities are preferred over degraded ones;
    - blocked/candidate/not_connected capabilities are never selected as executable;
    - a write need cannot resolve to a read-only capability;
    - human approval requirements are surfaced, never bypassed.
    """
    by_id = {capability.capability_id: capability for capability in capabilities}
    selected: list[Capability] = []
    selected_ids: set[str] = set()
    unresolved: list[str] = []
    approval_required: set[str] = set()

    status_rank = {"available": 0, "degraded": 1}

    for need in needs:
        candidates: list[Capability] = []
        for capability_id in need.acceptable_capability_ids:
            capability = by_id.get(capability_id)
            if capability is None:
                continue
            if capability.status not in status_rank:
                continue
            if need.write_required and not capability.can_write:
                continue
            candidates.append(capability)

        candidates.sort(key=lambda item: status_rank[item.status])

        if not candidates:
            unresolved.append(need.need_id)
            continue

        chosen = candidates[0]
        if chosen.capability_id not in selected_ids:
            selected.append(chosen)
            selected_ids.add(chosen.capability_id)

        if need.write_required and chosen.approval_mode != "none":
            approval_required.add(chosen.capability_id)

    return CapabilityPlan(
        selected=tuple(selected),
        unresolved_need_ids=tuple(unresolved),
        approval_required_capability_ids=tuple(sorted(approval_required)),
    )
