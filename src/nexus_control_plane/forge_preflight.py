from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from nexus_control_plane.forge import content_write_needed
from nexus_control_plane.forge_registry import CANONICAL_OWNERS, validate_canonical_owner_registry


class PreflightDecision(str, Enum):
    BLOCK = "block"
    HOLD = "hold"
    SHADOW_READY = "shadow_ready"


@dataclass(frozen=True)
class ForgePreflightRequest:
    change_id: str
    concern: str
    proposed_owner: str
    evidence_refs: tuple[str, ...]
    runtime_sensitive: bool = False
    live_verified: bool = False
    prior_failure_refs: tuple[str, ...] = ()
    prior_failures_consulted: bool = False
    current_content: str | None = None
    proposed_content: str | None = None


@dataclass(frozen=True)
class ForgePreflightResult:
    decision: PreflightDecision
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    execution_authorized: bool = False


def _non_empty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def _valid_unique_refs(refs: object, *, required: bool) -> bool:
    if not isinstance(refs, tuple):
        return False
    if required and not refs:
        return False
    normalized: list[str] = []
    for ref in refs:
        if not _non_empty_text(ref):
            return False
        normalized.append(ref)
    return len(set(normalized)) == len(normalized)


def evaluate_forge_preflight(
    request: ForgePreflightRequest,
    *,
    canonical_owners: Mapping[str, str],
) -> ForgePreflightResult:
    """Check whether a proposed change is eligible for shadow work.

    This is not an execution or promotion gate. It only blocks obvious architecture
    duplication, stale runtime assumptions, ignored prior failures, malformed evidence,
    and byte-identical writes before implementation work proceeds.
    """

    if not isinstance(request, ForgePreflightRequest):
        return ForgePreflightResult(PreflightDecision.BLOCK, ("request must be ForgePreflightRequest",), ())
    if not isinstance(canonical_owners, Mapping):
        return ForgePreflightResult(PreflightDecision.BLOCK, ("canonical_owners must be a mapping",), ())

    blockers: list[str] = []
    warnings: list[str] = []

    valid_concern = _non_empty_text(request.concern)
    for name, value in (
        ("change_id", request.change_id),
        ("concern", request.concern),
        ("proposed_owner", request.proposed_owner),
    ):
        if not _non_empty_text(value):
            blockers.append(f"{name} is invalid")

    if not _valid_unique_refs(request.evidence_refs, required=True):
        blockers.append("evidence_refs must be unique non-empty strings")

    if valid_concern:
        existing_owner = canonical_owners.get(request.concern)
        if existing_owner is not None:
            if not _non_empty_text(existing_owner):
                blockers.append("canonical owner registry contains invalid owner metadata")
            elif existing_owner != request.proposed_owner:
                blockers.append(
                    f"canonical owner conflict: {request.concern} is owned by {existing_owner}, not {request.proposed_owner}"
                )
        else:
            warnings.append("concern has no canonical owner yet; consolidation review required before promotion")

    if not isinstance(request.runtime_sensitive, bool) or not isinstance(request.live_verified, bool):
        blockers.append("runtime verification flags must be boolean")
    elif request.runtime_sensitive and not request.live_verified:
        warnings.append("runtime-sensitive claim is not live-verified")

    if not _valid_unique_refs(request.prior_failure_refs, required=False):
        blockers.append("prior_failure_refs must be unique non-empty strings")
    elif request.prior_failure_refs and request.prior_failures_consulted is not True:
        warnings.append("relevant prior failures exist but have not been consulted")

    if not isinstance(request.prior_failures_consulted, bool):
        blockers.append("prior_failures_consulted must be boolean")

    content_values = (request.current_content, request.proposed_content)
    if any(value is not None and not isinstance(value, str) for value in content_values):
        blockers.append("content comparison values must be strings or None")
    elif request.current_content is not None and request.proposed_content is not None:
        if not content_write_needed(request.current_content, request.proposed_content):
            blockers.append("byte-identical/no-op write blocked")

    if blockers:
        return ForgePreflightResult(PreflightDecision.BLOCK, tuple(blockers), tuple(warnings))
    if warnings:
        return ForgePreflightResult(PreflightDecision.HOLD, (), tuple(warnings))
    return ForgePreflightResult(PreflightDecision.SHADOW_READY, (), (), False)


def evaluate_registered_forge_preflight(request: ForgePreflightRequest) -> ForgePreflightResult:
    """Run preflight against the project-wide canonical owner registry.

    A broken registry blocks shadow work rather than silently falling back to an empty
    mapping or permitting a new competing owner.
    """

    registry_errors = validate_canonical_owner_registry()
    if registry_errors:
        return ForgePreflightResult(
            PreflightDecision.BLOCK,
            tuple(f"canonical registry invalid: {error}" for error in registry_errors),
            (),
        )
    return evaluate_forge_preflight(request, canonical_owners=CANONICAL_OWNERS)
