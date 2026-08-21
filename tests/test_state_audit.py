import pytest

from nexus_core.state_audit import build_rollback_plan, record_state_mutation
from nexus_core.state_promotion import CanonicalClaim, CandidateClaim, PromotionDecision


def _current():
    return CanonicalClaim(
        "hydrotester",
        "max-pressure",
        "70 MPa",
        "supplier_oem",
        "2026-08-20T10:00:00+00:00",
        ("supplier:quote:70",),
    )


def _candidate():
    return CandidateClaim(
        "hydrotester",
        "max-pressure",
        "120 MPa",
        "buyer_end_user",
        "2026-08-21T10:00:00+00:00",
        ("buyer:email:120",),
    )


def test_promoted_mutation_records_before_after_authority_and_provenance():
    audit = record_state_mutation(
        _current(),
        _candidate(),
        PromotionDecision("promote", "higher_authority_candidate", False, ("buyer:email:120",)),
        mutation_id="mut-001",
        recorded_at="2026-08-21T16:30:00+00:00",
    )
    assert audit.project_id == "hydrotester"
    assert audit.previous_value == "70 MPa"
    assert audit.candidate_value == "120 MPa"
    assert audit.previous_authority == "supplier_oem"
    assert audit.candidate_authority == "buyer_end_user"
    assert audit.previous_evidence_refs == ("supplier:quote:70",)
    assert audit.candidate_evidence_refs == ("buyer:email:120",)


def test_promoted_mutation_builds_explicit_rollback_to_previous_snapshot():
    audit = record_state_mutation(
        _current(),
        _candidate(),
        PromotionDecision("promote", "higher_authority_candidate", False, ("buyer:email:120",)),
        mutation_id="mut-002",
        recorded_at="2026-08-21T16:31:00+00:00",
    )
    rollback = build_rollback_plan(audit)
    assert rollback.allowed is True
    assert rollback.restore_value == "70 MPa"
    assert rollback.restore_authority == "supplier_oem"
    assert rollback.restore_evidence_refs == ("supplier:quote:70",)


def test_rejected_or_held_decision_cannot_produce_rollback_of_non_applied_mutation():
    audit = record_state_mutation(
        _current(),
        _candidate(),
        PromotionDecision("hold", "equal_authority_conflict", True, ("buyer:email:120",)),
        mutation_id="mut-003",
        recorded_at="2026-08-21T16:32:00+00:00",
    )
    rollback = build_rollback_plan(audit)
    assert rollback.allowed is False
    assert rollback.reason == "mutation_not_applied"


def test_audit_rejects_cross_project_claim_pair():
    other = CandidateClaim(
        "heat-treatment",
        "max-pressure",
        "120 MPa",
        "buyer_end_user",
        "2026-08-21T10:00:00+00:00",
        ("buyer:email:120",),
    )
    with pytest.raises(ValueError, match="audit_claim_mismatch"):
        record_state_mutation(
            _current(),
            other,
            PromotionDecision("reject", "cross_project_write", False, ("buyer:email:120",)),
            mutation_id="mut-004",
            recorded_at="2026-08-21T16:33:00+00:00",
        )


def test_audit_requires_timezone_aware_timestamp():
    with pytest.raises(ValueError, match="invalid_recorded_at"):
        record_state_mutation(
            _current(),
            _candidate(),
            PromotionDecision("promote", "higher_authority_candidate", False, ("buyer:email:120",)),
            mutation_id="mut-005",
            recorded_at="2026-08-21T16:34:00",
        )
