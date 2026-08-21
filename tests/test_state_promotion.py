import pytest

from nexus_core.state_promotion import CanonicalClaim, CandidateClaim, evaluate_state_promotion


def current(**overrides):
    data = dict(
        project_id="hydrotester",
        canonical_key="max_pressure_mpa",
        value="70",
        authority="supplier_oem",
        observed_at="2026-08-20T10:00:00+00:00",
        evidence_refs=("email:supplier:70",),
    )
    data.update(overrides)
    return CanonicalClaim(**data)


def candidate(**overrides):
    data = dict(
        project_id="hydrotester",
        canonical_key="max_pressure_mpa",
        value="120",
        authority="buyer_end_user",
        observed_at="2026-08-21T10:00:00+00:00",
        evidence_refs=("email:buyer:120",),
    )
    data.update(overrides)
    return CandidateClaim(**data)


def test_higher_authority_candidate_can_correct_lower_authority_canonical_state():
    decision = evaluate_state_promotion(current(), candidate())
    assert decision.action == "promote"
    assert decision.reason == "higher_authority_candidate"
    assert decision.requires_human_review is False


def test_lower_authority_supplier_cannot_overwrite_buyer_requirement():
    existing = current(value="120", authority="buyer_end_user")
    incoming = candidate(value="70", authority="supplier_oem")
    decision = evaluate_state_promotion(existing, incoming)
    assert decision.action == "reject"
    assert decision.reason == "lower_authority_than_canonical"


def test_equal_authority_conflict_is_held_for_human_review():
    existing = current(value="120", authority="buyer_end_user")
    incoming = candidate(value="100", authority="buyer_end_user")
    decision = evaluate_state_promotion(existing, incoming)
    assert decision.action == "hold"
    assert decision.requires_human_review is True


def test_cross_project_candidate_fails_closed_even_with_high_authority():
    decision = evaluate_state_promotion(current(), candidate(project_id="heat-treatment"))
    assert decision.action == "reject"
    assert decision.reason == "cross_project_write"


def test_same_value_never_counts_as_state_change():
    existing = current(value="120", authority="buyer_end_user")
    incoming = candidate(value="120", authority="buyer_end_user")
    decision = evaluate_state_promotion(existing, incoming)
    assert decision.action == "no_change"


def test_missing_or_duplicate_provenance_fails_closed():
    with pytest.raises(ValueError, match="invalid_evidence_refs"):
        evaluate_state_promotion(current(), candidate(evidence_refs=()))
    with pytest.raises(ValueError, match="duplicate_evidence_ref"):
        evaluate_state_promotion(current(), candidate(evidence_refs=("ref:a", "ref:a")))


def test_naive_timestamp_is_rejected():
    with pytest.raises(ValueError, match="invalid_observed_at"):
        evaluate_state_promotion(current(), candidate(observed_at="2026-08-21T10:00:00"))


def test_canonical_key_mismatch_is_rejected():
    decision = evaluate_state_promotion(current(), candidate(canonical_key="pipe_length_m"))
    assert decision.action == "reject"
    assert decision.reason == "canonical_key_mismatch"
