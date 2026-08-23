from __future__ import annotations

from dataclasses import dataclass

from nexus_control_plane.contradiction_graph import ContradictionGate
from nexus_control_plane.outcome_gate import OutcomeDecision, OutcomeGateResult
from nexus_control_plane.recursive_evolution import (
    GenerationAudit,
    GenerationDecision,
    finalize_stopped_generation,
)


@dataclass(frozen=True)
class GenerationDecisionGateResult:
    audit: GenerationAudit
    contradiction_refs: tuple[str, ...]
    outcome_signal_refs: tuple[str, ...]
    reason: str


def finalize_generation_with_evidence(
    audit: GenerationAudit,
    *,
    contradiction_gate: ContradictionGate,
    outcome_gate: OutcomeGateResult | None,
    outcome_required: bool,
    independent_audit_passed: bool,
    candidate_beats_baseline: bool,
) -> GenerationDecisionGateResult:
    """Compose Forge controls without replacing PR #7 or PR #19 authority."""
    if not isinstance(audit, GenerationAudit):
        raise ValueError("audit must be GenerationAudit")
    if audit.decision is GenerationDecision.CONTINUE:
        raise ValueError("running generation cannot be finalized")
    if not isinstance(contradiction_gate, ContradictionGate):
        raise ValueError("contradiction_gate must be ContradictionGate")
    if outcome_gate is not None and not isinstance(outcome_gate, OutcomeGateResult):
        raise ValueError("outcome_gate must be OutcomeGateResult or None")
    for name, value in (
        ("outcome_required", outcome_required),
        ("independent_audit_passed", independent_audit_passed),
        ("candidate_beats_baseline", candidate_beats_baseline),
    ):
        if not isinstance(value, bool):
            raise ValueError(f"{name} must be boolean")

    if contradiction_gate.promotion_blocked:
        held = GenerationAudit(
            audit.telemetry,
            audit.stop_reason,
            GenerationDecision.PLATEAU_RESEARCH_RESTART,
            False,
            False,
            True,
        )
        return GenerationDecisionGateResult(
            held,
            contradiction_gate.open_refs,
            () if outcome_gate is None else outcome_gate.signal_refs,
            "open contradictions require research refresh before promotion",
        )

    if outcome_required and outcome_gate is None:
        held = GenerationAudit(
            audit.telemetry,
            audit.stop_reason,
            GenerationDecision.PLATEAU_RESEARCH_RESTART,
            False,
            False,
            True,
        )
        return GenerationDecisionGateResult(held, (), (), "required outcome evidence is missing")

    if outcome_gate is not None:
        if outcome_gate.decision is OutcomeDecision.REGRESSED:
            rolled = GenerationAudit(
                audit.telemetry,
                audit.stop_reason,
                GenerationDecision.ROLLBACK_RESTART,
                False,
                True,
                False,
            )
            return GenerationDecisionGateResult(
                rolled,
                (),
                outcome_gate.signal_refs,
                "observed outcome regression requires rollback",
            )
        if outcome_required and not outcome_gate.promotion_support:
            held = GenerationAudit(
                audit.telemetry,
                audit.stop_reason,
                GenerationDecision.PLATEAU_RESEARCH_RESTART,
                False,
                False,
                True,
            )
            return GenerationDecisionGateResult(
                held,
                (),
                outcome_gate.signal_refs,
                "required outcomes do not yet support promotion",
            )

    finalized = finalize_stopped_generation(
        audit,
        independent_audit_passed=independent_audit_passed,
        candidate_beats_baseline=candidate_beats_baseline,
    )
    return GenerationDecisionGateResult(
        finalized,
        (),
        () if outcome_gate is None else outcome_gate.signal_refs,
        "technical audit finalized with contradiction/outcome controls",
    )
