from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Lifecycle = Literal["REJECT", "RESEARCH", "EXPERIMENT", "ADOPT_CANDIDATE"]


@dataclass(frozen=True)
class CapabilityCandidate:
    capability_id: str
    solves_repeated_problem: bool
    existing_capability_sufficient: bool
    acceptance_test_defined: bool
    rollback_defined: bool
    project_isolation_proven: bool
    provenance_supported: bool
    approval_boundary_preserved: bool
    portable_data_contract: bool
    measurable_outcome_defined: bool
    live_credentials_required: bool = False
    production_mutation_required: bool = False


@dataclass(frozen=True)
class AdmissionDecision:
    lifecycle: Lifecycle
    reasons: tuple[str, ...]
    gates: tuple[str, ...]


def assess_capability(c: CapabilityCandidate) -> AdmissionDecision:
    """Fail-closed admission gate for new NEXUS infrastructure/capabilities.

    A tool, agent, memory layer, database, router or orchestration framework is an
    adapter, never authority. Promotion requires evidence that it solves a repeated
    problem better than the existing mechanism without weakening NEXUS invariants.
    """
    if not c.capability_id.strip():
        return AdmissionDecision("REJECT", ("stable capability_id is required",), ())
    if not c.solves_repeated_problem:
        return AdmissionDecision("REJECT", ("no measurable repeated problem",), ())
    if c.existing_capability_sufficient:
        return AdmissionDecision("REJECT", ("existing capability is sufficient",), ())

    missing = []
    if not c.acceptance_test_defined:
        missing.append("define a reproducible acceptance test")
    if not c.rollback_defined:
        missing.append("define tested rollback")
    if not c.project_isolation_proven:
        missing.append("prove project isolation and cross-project contamination resistance")
    if not c.provenance_supported:
        missing.append("preserve evidence provenance and source locators")
    if not c.approval_boundary_preserved:
        missing.append("preserve exact-scope human approval boundaries")
    if not c.portable_data_contract:
        missing.append("use stable IDs and a portable explicit data contract")
    if not c.measurable_outcome_defined:
        missing.append("define measurable improvement and stopping rule")

    gates = [
        "candidate output is evidence/operational state, never Tier A authority",
        "pin version/release for every experiment",
        "record input, output, version, duration, corrections and policy findings",
        "require disconfirming/adversarial test cases before promotion",
        "promotion is versioned and rollbackable",
    ]
    if c.live_credentials_required:
        gates.append("sandbox without live credentials first; exact credential scope requires separate approval")
    if c.production_mutation_required:
        gates.append("production mutation/deployment requires separate exact-target approval")

    if missing:
        return AdmissionDecision("RESEARCH", ("admission controls incomplete",), tuple(missing + gates))

    if c.live_credentials_required or c.production_mutation_required:
        return AdmissionDecision(
            "EXPERIMENT",
            ("controls are defined but live/production boundary remains unproven",),
            tuple(gates),
        )

    return AdmissionDecision(
        "ADOPT_CANDIDATE",
        ("minimum governed admission controls are present", "measured Adoption Gate evidence is still required"),
        tuple(gates),
    )
