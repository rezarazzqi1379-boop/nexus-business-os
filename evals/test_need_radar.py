"""Tests for need_radar.py.

This module had no test coverage in the live repo before this change, despite backing
the buyer-need triage logic other modules (and now opportunity_suggestion_engine.py)
depend on. These tests lock in its evidence-discipline and disposition behavior.
"""

import pytest

from need_radar import (
    NeedEvidence,
    NeedSignal,
    assess_need,
    build_research_queue,
    research_brief,
)


def _fact_evidence(evidence_id="ev1", source_type="official"):
    return NeedEvidence(
        evidence_id=evidence_id,
        classification="FACT",
        source_type=source_type,
        source_ref="ref:" + evidence_id,
        observed_at="2026-09-14T00:00:00+00:00",
        statement="A verifiable statement.",
    )


def _signal(**overrides):
    defaults = dict(
        signal_id="sig1",
        company_id="company1",
        company_name="Acme Steel",
        company_role="buyer",
        project_id="PRJ-FAL-01",
        signal_type="procurement_request",
        need_hypothesis="Needs ferrosilicon for Q4.",
        fit="strong",
        timing="current",
        relationship="warm_referral",
        evidence=(_fact_evidence(),),
    )
    defaults.update(overrides)
    return NeedSignal(**defaults)


def test_evidence_requires_timezone():
    with pytest.raises(ValueError):
        NeedEvidence(
            evidence_id="ev1", classification="FACT", source_type="official",
            source_ref="ref", observed_at="2026-09-14T00:00:00", statement="x",
        ).validate()


def test_fact_requires_primary_source_type():
    with pytest.raises(ValueError):
        NeedEvidence(
            evidence_id="ev1", classification="FACT", source_type="customer_referral",
            source_ref="ref", observed_at="2026-09-14T00:00:00+00:00", statement="x",
        ).validate()


def test_signal_requires_at_least_one_evidence_item():
    with pytest.raises(ValueError):
        _signal(evidence=()).validate()


def test_priority_research_requires_strong_fit_current_timing_and_two_refs():
    single_ref_signal = _signal()
    assessment = assess_need(single_ref_signal)
    # Only one independent evidence ref -> not "priority_research" yet.
    assert assessment.disposition != "priority_research"


def test_priority_research_with_two_independent_refs():
    two_ref_signal = _signal(evidence=(
        _fact_evidence("ev1"),
        _fact_evidence("ev2", source_type="registry"),
    ))
    assessment = assess_need(two_ref_signal)
    assert assessment.disposition == "priority_research"


def test_supplier_role_routes_to_supply_research_not_buyer_pipeline():
    signal = _signal(company_role="supplier")
    assessment = assess_need(signal)
    assert assessment.disposition == "supply_research"


def test_contradiction_forces_manual_review_regardless_of_fit():
    signal = _signal(contradictions=("Conflicting account of budget.",))
    assessment = assess_need(signal)
    assert assessment.disposition == "manual_review"


def test_no_fit_holds_even_with_good_evidence():
    signal = _signal(fit="none")
    assessment = assess_need(signal)
    assert assessment.disposition == "hold"


def test_hypothesis_without_fact_evidence_requires_verification():
    claim_only = NeedEvidence(
        evidence_id="ev1", classification="CLAIM", source_type="customer_referral",
        source_ref="ref1", observed_at="2026-09-14T00:00:00+00:00", statement="Heard they need it.",
    )
    signal = _signal(evidence=(claim_only,))
    assessment = assess_need(signal)
    assert assessment.disposition == "verify"


def test_research_brief_never_authorizes_outreach():
    signal = _signal(evidence=(_fact_evidence("ev1"), _fact_evidence("ev2", source_type="registry")))
    assessment = assess_need(signal)
    brief = research_brief(assessment)
    assert brief["outreach_authorized"] is False
    assert brief["allowed_action"] == "research_only"


def test_research_brief_refuses_for_hold_disposition():
    signal = _signal(fit="none")
    assessment = assess_need(signal)
    with pytest.raises(ValueError):
        research_brief(assessment)


def test_build_research_queue_rejects_duplicate_company_need_with_different_content():
    s1 = _signal(signal_id="sig1")
    s2 = _signal(signal_id="sig2", need_hypothesis="A different hypothesis text entirely.")
    with pytest.raises(ValueError):
        build_research_queue([s1, s2])


def test_build_research_queue_orders_priority_first():
    priority = _signal(signal_id="sigA", evidence=(_fact_evidence("ev1"), _fact_evidence("ev2", source_type="registry")))
    hold = _signal(signal_id="sigB", company_id="company2", fit="none")
    queue = build_research_queue([hold, priority])
    assert queue[0].signal.signal_id == "sigA"
    assert queue[0].disposition == "priority_research"
