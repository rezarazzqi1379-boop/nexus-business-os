from __future__ import annotations

from dataclasses import dataclass

from nexus_control_plane.forge_preflight import (
    ForgePreflightRequest,
    ForgePreflightResult,
    PreflightDecision,
    evaluate_registered_forge_preflight,
)
from nexus_control_plane.source_authority import (
    AuthorityDecision,
    SourceRecord,
    resolve_same_scope_candidates,
)


@dataclass(frozen=True)
class ProjectPreflightRequest:
    forge: ForgePreflightRequest
    project_id: str
    source_candidates: tuple[SourceRecord, ...]
    stable_requirement_change: bool
    consequential: bool


def evaluate_project_preflight(request: ProjectPreflightRequest) -> ForgePreflightResult:
    """Compose Forge checks with canonical source authority for project work.

    Stable requirement changes require an accepted Tier A source. Dynamic points may
    use a fresh Tier B source. This function never promotes a supplier quote, chat,
    checkpoint or research claim to canonical authority on its own.
    """
    if not isinstance(request, ProjectPreflightRequest):
        return ForgePreflightResult(PreflightDecision.BLOCK, ("request must be ProjectPreflightRequest",), ())
    if not isinstance(request.project_id, str) or not request.project_id.strip() or request.project_id != request.project_id.strip():
        return ForgePreflightResult(PreflightDecision.BLOCK, ("project_id is invalid",), ())
    if not isinstance(request.source_candidates, tuple) or not request.source_candidates:
        return ForgePreflightResult(PreflightDecision.BLOCK, ("source_candidates are required",), ())
    if not isinstance(request.stable_requirement_change, bool) or not isinstance(request.consequential, bool):
        return ForgePreflightResult(PreflightDecision.BLOCK, ("project preflight flags must be boolean",), ())

    source_assessment = resolve_same_scope_candidates(
        request.source_candidates,
        expected_project_id=request.project_id,
        consequential=request.consequential,
    )
    if source_assessment.decision is AuthorityDecision.BLOCK_CONFLICT:
        return ForgePreflightResult(PreflightDecision.BLOCK, (f"source authority conflict: {source_assessment.reason}",), ())
    if source_assessment.decision is AuthorityDecision.HOLD_REFRESH:
        return ForgePreflightResult(PreflightDecision.HOLD, (), (f"source refresh required: {source_assessment.reason}",))
    if source_assessment.decision is AuthorityDecision.REJECT_NON_AUTHORITY:
        return ForgePreflightResult(PreflightDecision.BLOCK, (f"non-authoritative source: {source_assessment.reason}",), ())

    if request.stable_requirement_change:
        governing = next(
            (src for src in request.source_candidates if src.source_id == source_assessment.governing_source_id),
            None,
        )
        if governing is None or governing.tier.value != "A":
            return ForgePreflightResult(
                PreflightDecision.BLOCK,
                ("stable requirement change requires current Tier A canonical authority",),
                (),
            )

    forge_result = evaluate_registered_forge_preflight(request.forge)
    if forge_result.decision is not PreflightDecision.SHADOW_READY:
        return forge_result
    return ForgePreflightResult(
        PreflightDecision.SHADOW_READY,
        (),
        (f"governing source: {source_assessment.governing_source_id}",),
        False,
    )
