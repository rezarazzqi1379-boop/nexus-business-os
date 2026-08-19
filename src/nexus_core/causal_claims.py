from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CausalEvidence:
    claim_id: str
    design: str
    evidence_refs: tuple[str, ...]
    counterfactual_defined: bool
    assumptions_documented: bool
    confounding_addressed: bool
    sample_size: int
    replicated: bool = False


_ALLOWED_DESIGNS = {
    "randomized",
    "quasi_experimental",
    "natural_experiment",
    "observational_adjusted",
    "observational_only",
}


def validate_causal_evidence(item: CausalEvidence) -> tuple[str, ...]:
    errors: list[str] = []
    if not item.claim_id.strip():
        errors.append("missing_claim_id")
    if item.design not in _ALLOWED_DESIGNS:
        errors.append("invalid_design")
    if not item.evidence_refs or any(not isinstance(ref, str) or not ref.strip() for ref in item.evidence_refs):
        errors.append("missing_evidence_refs")
    if len(item.evidence_refs) != len(set(item.evidence_refs)):
        errors.append("duplicate_evidence_refs")
    if item.sample_size < 1:
        errors.append("invalid_sample_size")
    return tuple(errors)


def causal_confidence(item: CausalEvidence) -> str:
    """Return a conservative causal-evidence band, not an effect estimate.

    Observational attribution never upgrades to causal confidence merely because
    it has many samples. Strong causal language requires a counterfactual design,
    documented assumptions and explicit handling of confounding.
    """
    errors = validate_causal_evidence(item)
    if errors:
        raise ValueError(",".join(errors))

    if item.design == "randomized":
        if item.counterfactual_defined and item.assumptions_documented and item.sample_size >= 20:
            return "strong" if item.replicated else "moderate"
        return "weak"

    if item.design in {"quasi_experimental", "natural_experiment"}:
        if item.counterfactual_defined and item.assumptions_documented and item.confounding_addressed and item.sample_size >= 30:
            return "moderate" if item.replicated else "limited"
        return "weak"

    if item.design == "observational_adjusted":
        if item.counterfactual_defined and item.assumptions_documented and item.confounding_addressed and item.sample_size >= 50:
            return "limited"
        return "weak"

    return "attribution_only"


def may_use_causal_language(item: CausalEvidence) -> bool:
    return causal_confidence(item) in {"moderate", "strong"}
