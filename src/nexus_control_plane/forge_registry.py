from __future__ import annotations

from types import MappingProxyType
from typing import Mapping


_CANONICAL_OWNERS = {
    "evidence_semantics": "PR1",
    "requirement_readiness": "PR2",
    "capability_action_routing": "PR4",
    "evaluation": "PR6",
    "decision_outcome_learning": "PR7",
    "audit_metadata": "PR10",
    "security_policy_threat_model": "PR12",
    "evolution": "PR19",
    "capability_adoption_governor": "PR28",
    "hydrotester_authority": "PR29",
    "business_genome": "PR33",
    "public_pattern_reconstruction": "PR35",
    "forge_lifecycle": "PR36",
    "exact_external_approval": "PR37",
}

CANONICAL_OWNERS: Mapping[str, str] = MappingProxyType(_CANONICAL_OWNERS)


def canonical_owner(concern: str) -> str | None:
    if not isinstance(concern, str) or not concern.strip() or concern != concern.strip():
        return None
    return CANONICAL_OWNERS.get(concern)


def validate_canonical_owner_registry() -> tuple[str, ...]:
    errors: list[str] = []
    seen_owners: dict[str, list[str]] = {}
    for concern, owner in CANONICAL_OWNERS.items():
        if not isinstance(concern, str) or not concern.strip() or concern != concern.strip():
            errors.append("invalid concern metadata")
            continue
        if not isinstance(owner, str) or not owner.strip() or owner != owner.strip():
            errors.append(f"invalid owner metadata for {concern}")
            continue
        seen_owners.setdefault(owner, []).append(concern)

    # A PR can intentionally own more than one concern, but every concern must have
    # exactly one owner. Dict construction guarantees concern uniqueness; this check
    # keeps the validation contract explicit and fail-closed for malformed values.
    if len(CANONICAL_OWNERS) != len(set(CANONICAL_OWNERS.keys())):
        errors.append("duplicate canonical concern")
    return tuple(errors)
