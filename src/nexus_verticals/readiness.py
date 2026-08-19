from dataclasses import dataclass
from typing import Literal, Sequence


RequirementState = Literal["approved", "provisional", "unknown_blocking"]

_ALLOWED_STATES = {"approved", "provisional", "unknown_blocking"}


@dataclass(frozen=True)
class RequirementInput:
    requirement_id: str
    name: str
    state: RequirementState
    value: str = ""
    source_ref: str = ""


@dataclass(frozen=True)
class ReadinessAssessment:
    ready_for_discovery: bool
    ready_for_final_request: bool
    blocking_ids: tuple[str, ...]
    provisional_ids: tuple[str, ...]
    errors: tuple[str, ...]


def assess_requirement_readiness(
    requirements: Sequence[RequirementInput],
) -> ReadinessAssessment:
    """Evaluate buyer-side requirement readiness without taking external action.

    Shadow-mode policy:
    - discovery can proceed when the inputs are structurally valid, even if some
      requirements are provisional or unknown-blocking;
    - a final quotation/compliance request is ready only when every requirement
      is approved and structurally valid;
    - provisional values are surfaced explicitly so they cannot silently become
      technical authority;
    - unknown-blocking values remain blockers rather than being guessed.
    """
    errors: list[str] = []
    blocking_ids: list[str] = []
    provisional_ids: list[str] = []
    seen_ids: set[str] = set()

    if not requirements:
        errors.append("at least one requirement is required")

    for item in requirements:
        requirement_id = item.requirement_id.strip()
        name = item.name.strip()
        value = item.value.strip()
        source_ref = item.source_ref.strip()

        if not requirement_id:
            errors.append("requirement_id is required")
        elif requirement_id in seen_ids:
            errors.append(f"duplicate requirement_id: {requirement_id}")
        else:
            seen_ids.add(requirement_id)

        if not name:
            errors.append(f"requirement {requirement_id or '<missing>'} name is required")

        if item.state not in _ALLOWED_STATES:
            errors.append(
                f"requirement {requirement_id or '<missing>'} has unsupported state"
            )
            continue

        if item.state == "approved":
            if not value:
                errors.append(f"approved requirement {requirement_id} needs a value")
            if not source_ref:
                errors.append(
                    f"approved requirement {requirement_id} needs a source_ref"
                )
        elif item.state == "provisional":
            provisional_ids.append(requirement_id)
            if not value:
                errors.append(f"provisional requirement {requirement_id} needs a value")
            if not source_ref:
                errors.append(
                    f"provisional requirement {requirement_id} needs a source_ref"
                )
        elif item.state == "unknown_blocking":
            blocking_ids.append(requirement_id)
            if value:
                errors.append(
                    f"unknown_blocking requirement {requirement_id} must not carry an authoritative value"
                )

    ready_for_discovery = not errors
    ready_for_final_request = (
        not errors and not blocking_ids and not provisional_ids and bool(requirements)
    )

    return ReadinessAssessment(
        ready_for_discovery=ready_for_discovery,
        ready_for_final_request=ready_for_final_request,
        blocking_ids=tuple(blocking_ids),
        provisional_ids=tuple(provisional_ids),
        errors=tuple(errors),
    )
