from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

EvidenceClass = Literal["FACT", "MEASUREMENT", "CLAIM", "ESTIMATE", "ASSUMPTION", "HYPOTHESIS", "UNKNOWN"]
RequirementStatus = Literal["READY", "MISSING_EVIDENCE", "CONFLICT", "OUT_OF_SCOPE"]


@dataclass(frozen=True)
class FATRequirement:
    requirement_id: str
    project_id: str
    parameter: str
    canonical_value: str
    evidence_class: EvidenceClass
    source_refs: tuple[str, ...]
    measurement_method: str
    acceptance_criterion: str
    witness_evidence: str

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        for field in (
            "requirement_id",
            "project_id",
            "parameter",
            "canonical_value",
            "measurement_method",
            "acceptance_criterion",
            "witness_evidence",
        ):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{field} required")
        if len(set(self.source_refs)) != len(self.source_refs):
            errors.append("duplicate source_refs")
        if self.evidence_class in {"CLAIM", "ESTIMATE", "ASSUMPTION", "HYPOTHESIS", "UNKNOWN"}:
            errors.append("canonical FAT requirement must be backed by FACT or MEASUREMENT")
        return tuple(errors)


@dataclass(frozen=True)
class FATCase:
    case_id: str
    project_id: str
    requirement_id: str
    parameter: str
    expected_value: str
    measurement_method: str
    acceptance_criterion: str
    witness_evidence: str
    source_refs: tuple[str, ...]


@dataclass(frozen=True)
class FATBuildResult:
    status: RequirementStatus
    cases: tuple[FATCase, ...]
    reasons: tuple[str, ...]


def build_fat(project_id: str, requirements: Sequence[FATRequirement]) -> FATBuildResult:
    if not project_id.strip():
        return FATBuildResult("OUT_OF_SCOPE", (), ("project_id required",))
    ids: set[str] = set()
    cases: list[FATCase] = []
    reasons: list[str] = []
    for req in requirements:
        if req.project_id != project_id:
            return FATBuildResult("OUT_OF_SCOPE", (), ("cross-project requirement rejected",))
        if req.requirement_id in ids:
            return FATBuildResult("CONFLICT", (), ("duplicate requirement_id",))
        ids.add(req.requirement_id)
        errors = req.validate()
        if errors:
            reasons.extend(f"{req.requirement_id}: {e}" for e in errors)
            continue
        cases.append(
            FATCase(
                case_id=f"FAT-{project_id}-{req.requirement_id}",
                project_id=project_id,
                requirement_id=req.requirement_id,
                parameter=req.parameter,
                expected_value=req.canonical_value,
                measurement_method=req.measurement_method,
                acceptance_criterion=req.acceptance_criterion,
                witness_evidence=req.witness_evidence,
                source_refs=req.source_refs,
            )
        )
    if reasons:
        return FATBuildResult("MISSING_EVIDENCE", tuple(cases), tuple(reasons))
    if not cases:
        return FATBuildResult("MISSING_EVIDENCE", (), ("no FAT-ready canonical requirements",))
    return FATBuildResult("READY", tuple(cases), ())
