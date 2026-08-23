from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class VerificationMode(str, Enum):
    DETERMINISTIC = "deterministic"
    STRUCTURED_EVIDENCE = "structured_evidence"
    HUMAN_REVIEW = "human_review"
    ADVISORY_LLM = "advisory_llm"


@dataclass(frozen=True)
class VerificationRequest:
    consequential: bool
    deterministic_check_available: bool
    structured_evidence_available: bool
    external_side_effect: bool
    ambiguity: float
    irreversible: bool = False


@dataclass(frozen=True)
class VerificationPlan:
    primary: VerificationMode
    secondary: tuple[VerificationMode, ...]
    llm_judge_is_authority: bool
    allow_commit: bool
    reasons: tuple[str, ...]


def build_verification_plan(req: VerificationRequest) -> VerificationPlan:
    if not isinstance(req, VerificationRequest):
        raise TypeError("req must be VerificationRequest")
    if not isinstance(req.ambiguity, (int, float)) or isinstance(req.ambiguity, bool) or not 0 <= float(req.ambiguity) <= 1:
        raise ValueError("ambiguity must be within [0, 1]")
    for field in ("consequential", "deterministic_check_available", "structured_evidence_available", "external_side_effect", "irreversible"):
        if not isinstance(getattr(req, field), bool):
            raise ValueError(f"{field} must be boolean")

    reasons: list[str] = []
    secondary: list[VerificationMode] = []

    if req.deterministic_check_available:
        primary = VerificationMode.DETERMINISTIC
        reasons.append("deterministic verification is available and should outrank model judgment")
    elif req.structured_evidence_available:
        primary = VerificationMode.STRUCTURED_EVIDENCE
        reasons.append("use structured evidence-backed verification because no deterministic oracle exists")
    else:
        primary = VerificationMode.ADVISORY_LLM
        reasons.append("no stronger automatic verifier exists; LLM assessment remains advisory only")

    if req.structured_evidence_available and primary != VerificationMode.STRUCTURED_EVIDENCE:
        secondary.append(VerificationMode.STRUCTURED_EVIDENCE)
    if req.ambiguity >= 0.4:
        secondary.append(VerificationMode.ADVISORY_LLM)

    human_required = req.consequential or req.external_side_effect or req.irreversible
    if human_required:
        secondary.append(VerificationMode.HUMAN_REVIEW)
        reasons.append("consequential/external/irreversible action requires human review before commit")

    allow_commit = primary in (VerificationMode.DETERMINISTIC, VerificationMode.STRUCTURED_EVIDENCE) and not human_required
    return VerificationPlan(
        primary=primary,
        secondary=tuple(dict.fromkeys(secondary)),
        llm_judge_is_authority=False,
        allow_commit=allow_commit,
        reasons=tuple(reasons),
    )
