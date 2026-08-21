import pytest

from nexus_verticals.capability_governor import (
    CapabilityScore,
    Decision,
    HardGates,
    evaluate_capability,
)


def score(total_case: str) -> CapabilityScore:
    cases = {
        "high": CapabilityScore(18, 13, 13, 9, 9, 9, 9, 4, 4),  # 88
        "watch": CapabilityScore(15, 11, 11, 8, 7, 7, 7, 3, 3),  # 72
        "low": CapabilityScore(10, 8, 8, 6, 6, 6, 6, 2, 2),      # 54
    }
    return cases[total_case]


def test_high_score_only_earns_reversible_test():
    assert evaluate_capability(score("high"), HardGates(evidence_verified=True)) == Decision.TEST


def test_watch_band_is_not_promoted():
    assert evaluate_capability(score("watch"), HardGates(evidence_verified=True)) == Decision.WATCH


def test_low_score_is_rejected():
    assert evaluate_capability(score("low"), HardGates(evidence_verified=True)) == Decision.REJECT


@pytest.mark.parametrize(
    "gate_override",
    [
        {"evidence_verified": False},
        {"evidence_verified": True, "no_approval_bypass": False},
        {"evidence_verified": True, "no_unauthorized_external_action": False},
        {"evidence_verified": True, "no_credential_leakage": False},
        {"evidence_verified": True, "no_false_completion": False},
        {"evidence_verified": True, "no_cross_project_contamination": False},
    ],
)
def test_any_failed_hard_gate_rejects_even_high_score(gate_override):
    assert evaluate_capability(score("high"), HardGates(**gate_override)) == Decision.REJECT


def test_out_of_range_score_is_rejected_at_construction():
    with pytest.raises(ValueError):
        CapabilityScore(21, 13, 13, 9, 9, 9, 9, 4, 4)


def test_bool_cannot_masquerade_as_integer_score():
    with pytest.raises(TypeError):
        CapabilityScore(True, 13, 13, 9, 9, 9, 9, 4, 4)
