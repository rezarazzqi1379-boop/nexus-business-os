from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from nexus_core.technology_radar import TechnologyCandidate

PromotionDecision = Literal["REJECT", "WATCH", "KEEP_EXPERIMENTING", "ADOPT_ADAPTER"]


@dataclass(frozen=True)
class ExperimentEvidence:
    candidate_id: str
    acceptance_passed: bool
    policy_violations: int
    security_findings: int
    regressions: int
    cross_project_contamination: int
    human_corrections: int
    baseline_human_corrections: int
    duration_ms: int
    baseline_duration_ms: int
    cost_microusd: int
    baseline_cost_microusd: int
    rollback_tested: bool
    reproducible_runs: int
    authority_expansion_required: bool = False
    production_dependency_required: bool = False

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.candidate_id.strip():
            errors.append("candidate_id is required")
        for field_name in (
            "policy_violations",
            "security_findings",
            "regressions",
            "cross_project_contamination",
            "human_corrections",
            "baseline_human_corrections",
            "duration_ms",
            "baseline_duration_ms",
            "cost_microusd",
            "baseline_cost_microusd",
            "reproducible_runs",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, int) or value < 0:
                errors.append(f"{field_name} must be a non-negative integer")
        if self.reproducible_runs < 1:
            errors.append("at least one reproducible run is required")
        return tuple(errors)


@dataclass(frozen=True)
class AdoptionResult:
    decision: PromotionDecision
    reasons: tuple[str, ...]


def evaluate_adoption(candidate: TechnologyCandidate, evidence: ExperimentEvidence) -> AdoptionResult:
    """Fail-closed promotion gate for self-improvement candidates.

    A tool/framework/model/MCP may be adopted only as an adapter after measured,
    reproducible evidence. The gate never grants external-action, merge, deploy,
    credential, payment, signature or production authority.
    """
    candidate_errors = candidate.validate()
    evidence_errors = evidence.validate()
    if candidate_errors or evidence_errors:
        return AdoptionResult("REJECT", tuple(candidate_errors + evidence_errors))
    if candidate.candidate_id != evidence.candidate_id:
        return AdoptionResult("REJECT", ("candidate/evidence identity mismatch",))

    hard_failures: list[str] = []
    if not evidence.acceptance_passed:
        hard_failures.append("acceptance test did not pass")
    if evidence.policy_violations:
        hard_failures.append("policy violation observed")
    if evidence.security_findings:
        hard_failures.append("security finding observed")
    if evidence.regressions:
        hard_failures.append("regression observed")
    if evidence.cross_project_contamination:
        hard_failures.append("cross-project contamination observed")
    if evidence.authority_expansion_required:
        hard_failures.append("candidate requires authority expansion")
    if evidence.production_dependency_required:
        hard_failures.append("experiment requires production dependency")
    if not evidence.rollback_tested:
        hard_failures.append("rollback was not tested")
    if hard_failures:
        return AdoptionResult("REJECT", tuple(hard_failures))

    if evidence.reproducible_runs < 3:
        return AdoptionResult("KEEP_EXPERIMENTING", ("fewer than three reproducible clean runs",))

    improvements: list[str] = []
    if evidence.human_corrections < evidence.baseline_human_corrections:
        improvements.append("fewer human corrections")
    if evidence.duration_ms < evidence.baseline_duration_ms:
        improvements.append("lower duration")
    if evidence.cost_microusd < evidence.baseline_cost_microusd:
        improvements.append("lower cost")

    if not improvements:
        return AdoptionResult(
            "WATCH",
            ("safe and reproducible, but no measured advantage over the current NEXUS baseline",),
        )

    return AdoptionResult(
        "ADOPT_ADAPTER",
        tuple(improvements)
        + (
            "adapter only; canonical authority and consequential-action gates remain in NEXUS",
        ),
    )
