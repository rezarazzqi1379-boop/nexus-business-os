from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AuthorityTier(str, Enum):
    A_CANONICAL = "A"
    B_LIVE_EVIDENCE = "B"
    C_OPERATIONAL_STATE = "C"
    D_RESEARCH_CLAIM = "D"


class AuthorityDecision(str, Enum):
    ACCEPT = "accept"
    HOLD_REFRESH = "hold_refresh"
    BLOCK_CONFLICT = "block_conflict"
    REJECT_NON_AUTHORITY = "reject_non_authority"


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    project_id: str
    version: str
    status: str
    tier: AuthorityTier
    authority_scope: str
    effective_date: str
    dynamic: bool = False
    fresh: bool = True
    superseded: bool = False

    def __post_init__(self) -> None:
        for name in ("source_id", "project_id", "version", "status", "authority_scope", "effective_date"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(f"{name} must be a non-empty normalized string")
        if not isinstance(self.tier, AuthorityTier):
            raise ValueError("tier must be AuthorityTier")
        if not isinstance(self.dynamic, bool) or not isinstance(self.fresh, bool) or not isinstance(self.superseded, bool):
            raise ValueError("dynamic/fresh/superseded must be boolean")


@dataclass(frozen=True)
class AuthorityAssessment:
    decision: AuthorityDecision
    governing_source_id: str | None
    reason: str
    requires_live_refresh: bool


def assess_source_for_use(
    source: SourceRecord,
    *,
    expected_project_id: str,
    consequential: bool,
) -> AuthorityAssessment:
    """Fail closed on source-authority misuse.

    Tier A governs stable requirements until explicitly superseded. Tier B may
    govern dynamic current facts only when fresh. Tier C is operational state and
    must not silently create stable requirements. Tier D is research/claim input,
    never operating authority. This function does not choose between conflicting
    canonical sources; callers must resolve that conflict explicitly.
    """
    if not isinstance(source, SourceRecord):
        raise ValueError("source must be SourceRecord")
    if not isinstance(expected_project_id, str) or not expected_project_id.strip():
        raise ValueError("expected_project_id is required")
    if not isinstance(consequential, bool):
        raise ValueError("consequential must be boolean")

    if source.project_id != expected_project_id:
        return AuthorityAssessment(
            AuthorityDecision.BLOCK_CONFLICT,
            None,
            "cross-project source contamination",
            False,
        )
    if source.superseded:
        return AuthorityAssessment(
            AuthorityDecision.REJECT_NON_AUTHORITY,
            None,
            "source is superseded",
            False,
        )
    if source.tier is AuthorityTier.D_RESEARCH_CLAIM:
        return AuthorityAssessment(
            AuthorityDecision.REJECT_NON_AUTHORITY,
            None,
            "research/claim source cannot govern operational knowledge",
            False,
        )
    if source.tier is AuthorityTier.C_OPERATIONAL_STATE:
        return AuthorityAssessment(
            AuthorityDecision.REJECT_NON_AUTHORITY if consequential else AuthorityDecision.ACCEPT,
            source.source_id if not consequential else None,
            "operational state may inform workflow but cannot create consequential stable authority",
            False,
        )
    if source.tier is AuthorityTier.B_LIVE_EVIDENCE:
        if not source.dynamic:
            return AuthorityAssessment(
                AuthorityDecision.REJECT_NON_AUTHORITY,
                None,
                "live evidence cannot silently rewrite a stable Tier A requirement",
                False,
            )
        if not source.fresh:
            return AuthorityAssessment(
                AuthorityDecision.HOLD_REFRESH,
                None,
                "dynamic live evidence is stale and must be refreshed",
                True,
            )
        return AuthorityAssessment(
            AuthorityDecision.ACCEPT,
            source.source_id,
            "fresh Tier B evidence may govern its explicitly dynamic point",
            False,
        )

    # Tier A canonical authority.
    return AuthorityAssessment(
        AuthorityDecision.ACCEPT,
        source.source_id,
        "current canonical Tier A source",
        False,
    )


def resolve_same_scope_candidates(
    candidates: tuple[SourceRecord, ...],
    *,
    expected_project_id: str,
    consequential: bool,
) -> AuthorityAssessment:
    """Resolve a same-scope candidate set without averaging or guessing.

    More than one non-superseded Tier A candidate for the same scope is a conflict
    and must stop consequential use until authority is resolved/versioned.
    """
    if not isinstance(candidates, tuple) or not candidates:
        raise ValueError("candidates must be a non-empty tuple")
    active_a = tuple(
        src for src in candidates
        if isinstance(src, SourceRecord)
        and src.project_id == expected_project_id
        and src.tier is AuthorityTier.A_CANONICAL
        and not src.superseded
    )
    if len(active_a) > 1:
        return AuthorityAssessment(
            AuthorityDecision.BLOCK_CONFLICT,
            None,
            "multiple active Tier A candidates for the same scope",
            False,
        )
    if len(active_a) == 1:
        return assess_source_for_use(active_a[0], expected_project_id=expected_project_id, consequential=consequential)

    # No Tier A candidate: allow only a valid fresh dynamic Tier B fact.
    accepted_b: list[AuthorityAssessment] = []
    refresh_needed = False
    for src in candidates:
        assessment = assess_source_for_use(src, expected_project_id=expected_project_id, consequential=consequential)
        if assessment.decision is AuthorityDecision.ACCEPT and src.tier is AuthorityTier.B_LIVE_EVIDENCE:
            accepted_b.append(assessment)
        if assessment.decision is AuthorityDecision.HOLD_REFRESH:
            refresh_needed = True
    if len(accepted_b) == 1:
        return accepted_b[0]
    if len(accepted_b) > 1:
        return AuthorityAssessment(AuthorityDecision.BLOCK_CONFLICT, None, "multiple live candidates require explicit reconciliation", False)
    if refresh_needed:
        return AuthorityAssessment(AuthorityDecision.HOLD_REFRESH, None, "dynamic evidence requires refresh", True)
    return AuthorityAssessment(AuthorityDecision.REJECT_NON_AUTHORITY, None, "no governing authority candidate", False)
