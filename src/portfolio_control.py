from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

ProjectState = Literal[
    "ACTIVE_QUALIFICATION",
    "PAUSED_BY_MANAGEMENT",
    "COMMERCIAL_REFRESH_HOLD",
    "ENGINEERING_CLARIFICATION",
]
ActionClass = Literal["READ", "RESEARCH", "DRAFT", "TEST", "EXTERNAL", "PRODUCTION"]
EvidenceClass = Literal["FACT", "MEASUREMENT", "CLAIM", "ESTIMATE", "ASSUMPTION", "HYPOTHESIS", "UNKNOWN"]

_ALLOWED_PROJECTS = {"PRJ-HYD-01", "PRJ-HTL-01", "PRJ-KCL-01", "PRJ-CAN-01"}
_SAFE_ACTIONS = {"READ", "RESEARCH", "DRAFT", "TEST"}
_GATED_ACTIONS = {"EXTERNAL", "PRODUCTION"}


@dataclass(frozen=True)
class PortfolioProject:
    project_id: str
    state: ProjectState
    canonical_source_id: str
    canonical_version: str
    next_action: str
    action_class: ActionClass
    evidence_refs: tuple[str, ...]
    blocking_unknowns: tuple[str, ...] = ()
    evidence_class: EvidenceClass = "FACT"


@dataclass(frozen=True)
class PortfolioValidation:
    valid: bool
    errors: tuple[str, ...]


def validate_portfolio(projects: Sequence[PortfolioProject]) -> PortfolioValidation:
    errors: list[str] = []
    if len(projects) != 4:
        errors.append("portfolio must contain exactly four canonical active programs")

    seen: set[str] = set()
    for item in projects:
        if not isinstance(item, PortfolioProject):
            errors.append("all portfolio entries must be PortfolioProject")
            continue
        if item.project_id not in _ALLOWED_PROJECTS:
            errors.append(f"unknown project_id: {item.project_id}")
        if item.project_id in seen:
            errors.append(f"duplicate project_id: {item.project_id}")
        seen.add(item.project_id)

        if not item.canonical_source_id.strip() or not item.canonical_version.strip():
            errors.append(f"{item.project_id}: canonical source identity/version required")
        if not item.next_action.strip():
            errors.append(f"{item.project_id}: next_action required")
        if not item.evidence_refs:
            errors.append(f"{item.project_id}: evidence refs required")
        if len(set(item.evidence_refs)) != len(item.evidence_refs):
            errors.append(f"{item.project_id}: duplicate evidence refs")

        if item.project_id == "PRJ-HTL-01" and item.state != "PAUSED_BY_MANAGEMENT":
            errors.append("PRJ-HTL-01 must remain PAUSED_BY_MANAGEMENT")
        if item.project_id == "PRJ-KCL-01" and item.state != "COMMERCIAL_REFRESH_HOLD":
            errors.append("PRJ-KCL-01 must remain COMMERCIAL_REFRESH_HOLD until dynamic refresh closes blockers")
        if item.project_id == "PRJ-CAN-01" and item.state != "ENGINEERING_CLARIFICATION":
            errors.append("PRJ-CAN-01 must remain ENGINEERING_CLARIFICATION")
        if item.project_id == "PRJ-HYD-01" and item.state != "ACTIVE_QUALIFICATION":
            errors.append("PRJ-HYD-01 must remain ACTIVE_QUALIFICATION until qualification gates close")

        if item.state == "PAUSED_BY_MANAGEMENT" and item.action_class not in {"READ", "RESEARCH", "TEST"}:
            errors.append(f"{item.project_id}: paused project cannot draft/restart external activity")

        if item.action_class in _GATED_ACTIONS:
            errors.append(f"{item.project_id}: consequential action cannot be auto-runnable")
        elif item.action_class not in _SAFE_ACTIONS:
            errors.append(f"{item.project_id}: unsupported action class")

    if seen != _ALLOWED_PROJECTS:
        errors.append("portfolio project set does not match canonical active programs")
    return PortfolioValidation(not errors, tuple(errors))


def auto_runnable(project: PortfolioProject) -> bool:
    result = validate_portfolio((
        project,
        *[p for p in canonical_portfolio() if p.project_id != project.project_id],
    ))
    return result.valid and project.action_class in _SAFE_ACTIONS


def canonical_portfolio() -> tuple[PortfolioProject, ...]:
    return (
        PortfolioProject(
            project_id="PRJ-HYD-01",
            state="ACTIVE_QUALIFICATION",
            canonical_source_id="PRJ-HYD-01-ENG",
            canonical_version="v1.1",
            next_action="Monitor signed GH and Marley addendum replies and reconcile any new evidence against Rev.1.2; no duplicate outreach.",
            action_class="READ",
            evidence_refs=(
                "master:Hydrostatic_Tester_Engineering_Master:v1.1",
                "gmail:1a03db0ec7ca5dfd",
                "gmail:1a042db3a19ce692",
                "decision-pack:NEXUS_Hydrotester_Decision_Pack:v1.0",
            ),
            blocking_unknowns=(
                "signed GH 10-point addendum",
                "signed Marley point-by-point addendum",
                "final duty/pressure envelope acceptance",
                "PO-ready commercial/technical closure",
            ),
        ),
        PortfolioProject(
            project_id="PRJ-HTL-01",
            state="PAUSED_BY_MANAGEMENT",
            canonical_source_id="PRJ-HTL-01-ENG",
            canonical_version="v1.1",
            next_action="Preserve technical reference and monitor only; do not restart RFQ until renewed management approval and throughput revalidation.",
            action_class="READ",
            evidence_refs=(
                "master:OCTG_Heat_Treatment_Master:v1.1",
                "gmail:1a032f33b0019d77",
            ),
            blocking_unknowns=("buyer-engineering throughput revalidation", "management restart approval"),
        ),
        PortfolioProject(
            project_id="PRJ-KCL-01",
            state="COMMERCIAL_REFRESH_HOLD",
            canonical_source_id="PRJ-KCL-01-ACC",
            canonical_version="v1.0",
            next_action="Reconcile direct Dehkanabad route, OM Supply permit block and EuroChem routing; build an internal refresh packet before any new outreach.",
            action_class="READ",
            evidence_refs=(
                "master:KCl_SOP_Acceptance_Master:v1.0",
                "gmail:1a03362c348d6993",
                "gmail:1a03290562e816d1",
                "gmail:1a032944cf64e85f",
            ),
            blocking_unknowns=(
                "current committed quantity/forecast",
                "permit/import owner and actual permit status",
                "destination and Incoterm",
                "target price and payment route",
                "sanctions/logistics feasibility",
            ),
        ),
        PortfolioProject(
            project_id="PRJ-CAN-01",
            state="ENGINEERING_CLARIFICATION",
            canonical_source_id="PRJ-CAN-01-ENG",
            canonical_version="v1.0",
            next_action="Consolidate engineer-confirmed geometry, mandatory operations and production-rate questions; prepare a single clarification packet before supplier contact.",
            action_class="DRAFT",
            evidence_refs=("master:Can_Forming_Engineering_Master:v1.0",),
            blocking_unknowns=("final geometry", "mandatory operations", "required production rate"),
        ),
    )


def portfolio_next_actions() -> tuple[PortfolioProject, ...]:
    portfolio = canonical_portfolio()
    validation = validate_portfolio(portfolio)
    if not validation.valid:
        raise RuntimeError("portfolio fails governance: " + "; ".join(validation.errors))
    return tuple(item for item in portfolio if auto_runnable(item))
