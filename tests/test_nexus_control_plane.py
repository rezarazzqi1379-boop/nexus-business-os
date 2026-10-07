import pytest

from nexus_control_plane import (
    Admission,
    CapabilityCandidate,
    CommercialEvidence,
    ConversionStage,
    commercial_conversion_stage,
    evaluate_capability_admission,
)


def cap(name, functions, **kwargs):
    return CapabilityCandidate(
        name,
        frozenset(functions),
        ("evidence:fixture",),
        ("test:acceptance",),
        **kwargs,
    )


def test_duplicate_agent_is_merged_not_multiplied():
    incumbent = cap("native-search", {"search", "fetch", "dedup"})
    candidate = cap("new-agent", {"search", "fetch", "dedup"}, sandboxed=True)
    decision = evaluate_capability_admission(candidate, (incumbent,))
    assert decision.action is Admission.MERGE
    assert decision.overlap_ratio == 1.0


def test_secret_or_external_write_stays_sandboxed_and_needs_approval():
    candidate = cap("crm-writer", {"crm_write"}, sandboxed=True, external_write=True)
    decision = evaluate_capability_admission(candidate, ())
    assert decision.action is Admission.SANDBOX
    assert decision.requires_exact_approval


def test_new_read_capability_requires_sandbox_before_keep():
    decision = evaluate_capability_admission(cap("reader", {"read"}), ())
    assert decision.action is Admission.SANDBOX
    accepted = evaluate_capability_admission(cap("reader", {"read"}, sandboxed=True), ())
    assert accepted.action is Admission.KEEP


def test_candidate_without_evidence_or_acceptance_test_fails_closed():
    with pytest.raises(ValueError, match="evidence"):
        CapabilityCandidate("x", frozenset({"read"}), (), ("t",)).validate()
    with pytest.raises(ValueError, match="acceptance"):
        CapabilityCandidate("x", frozenset({"read"}), ("e",), ()).validate()


def test_commercial_volume_does_not_equal_conversion():
    e = CommercialEvidence(company_identity=True, product_application=True, independent_sources=5)
    assert commercial_conversion_stage(e) is ConversionStage.EVIDENCED


def test_buyer_needs_role_and_procurement_signal():
    base = dict(company_identity=True, product_application=True, independent_sources=2)
    assert commercial_conversion_stage(CommercialEvidence(**base, buyer_role=True)) is ConversionStage.EVIDENCED
    assert commercial_conversion_stage(
        CommercialEvidence(**base, buyer_role=True, procurement_signal=True)
    ) is ConversionStage.BUYER_VERIFIED


def test_outreach_ready_requires_decision_maker_and_verified_contact():
    e = CommercialEvidence(
        company_identity=True,
        product_application=True,
        procurement_signal=True,
        buyer_role=True,
        decision_maker=True,
        verified_contact=True,
        independent_sources=2,
    )
    assert commercial_conversion_stage(e) is ConversionStage.OUTREACH_READY


def test_unresolved_contradiction_forces_discovery_stage():
    e = CommercialEvidence(
        company_identity=True,
        product_application=True,
        procurement_signal=True,
        buyer_role=True,
        decision_maker=True,
        verified_contact=True,
        independent_sources=4,
        unresolved_contradiction=True,
    )
    assert commercial_conversion_stage(e) is ConversionStage.DISCOVERED
