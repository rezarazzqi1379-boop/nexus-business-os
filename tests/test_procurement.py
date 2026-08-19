from nexus_verticals.procurement import (
    Evidence,
    Opportunity,
    Outcome,
    ProcurementVerticalRecord,
    Relationship,
    Signal,
)


def make_suppliertr_record() -> ProcurementVerticalRecord:
    return ProcurementVerticalRecord(
        case_id="suppliertr-2026-08-19",
        evidence=Evidence(
            evidence_id="ev-suppliertr-1",
            source="gmail",
            source_ref="gmail:thread:suppliertr",
            summary="SupplierTR stated that engineering evaluation had started",
            observed_at="2026-08-19",
            confidence=0.95,
            kind="claim",
        ),
        relationship=Relationship(
            relationship_id="rel-atf-suppliertr",
            from_entity="ASAK TEJARAT FATER",
            to_entity="SupplierTR",
            relationship_type="buyer-sourcing-intermediary",
            status="responsive",
            evidence_id="ev-suppliertr-1",
        ),
        signal=Signal(
            signal_id="sig-suppliertr-eval",
            entity="SupplierTR",
            signal_type="engineering_evaluation_started",
            description="SupplierTR reports engineering evaluation started",
            evidence_id="ev-suppliertr-1",
            confidence=0.95,
        ),
        opportunity=Opportunity(
            opportunity_id="opp-turkey-octg",
            entity="SupplierTR",
            title="Turkey sourcing route for OCTG equipment",
            stage="qualification",
            signal_id="sig-suppliertr-eval",
            next_action="await supplier shortlist",
        ),
        outcome=Outcome(
            outcome_id="out-suppliertr-1",
            opportunity_id="opp-turkey-octg",
            outcome_type="qualified_reply",
            result="SupplierTR reported engineering evaluation started",
            status="open",
            terminal=False,
        ),
    )


def test_suppliertr_closed_loop_is_valid():
    assert make_suppliertr_record().validate() == []


def test_broken_evidence_link_is_rejected():
    record = make_suppliertr_record()
    broken = ProcurementVerticalRecord(
        case_id=record.case_id,
        evidence=record.evidence,
        relationship=Relationship(
            relationship_id=record.relationship.relationship_id,
            from_entity=record.relationship.from_entity,
            to_entity=record.relationship.to_entity,
            relationship_type=record.relationship.relationship_type,
            status=record.relationship.status,
            evidence_id="ev-wrong",
        ),
        signal=record.signal,
        opportunity=record.opportunity,
        outcome=record.outcome,
    )
    assert "relationship.evidence_id must match evidence.evidence_id" in broken.validate()


def test_terminal_open_outcome_is_rejected():
    record = make_suppliertr_record()
    broken = ProcurementVerticalRecord(
        case_id=record.case_id,
        evidence=record.evidence,
        relationship=record.relationship,
        signal=record.signal,
        opportunity=record.opportunity,
        outcome=Outcome(
            outcome_id="out-terminal-bad",
            opportunity_id=record.opportunity.opportunity_id,
            outcome_type="final_result",
            result="closed",
            status="open",
            terminal=True,
        ),
    )
    assert "terminal outcome must have status won or lost" in broken.validate()


def test_entity_drift_is_rejected():
    record = make_suppliertr_record()
    broken = ProcurementVerticalRecord(
        case_id=record.case_id,
        evidence=record.evidence,
        relationship=record.relationship,
        signal=record.signal,
        opportunity=Opportunity(
            opportunity_id=record.opportunity.opportunity_id,
            entity="Different Supplier",
            title=record.opportunity.title,
            stage=record.opportunity.stage,
            signal_id=record.opportunity.signal_id,
            next_action=record.opportunity.next_action,
        ),
        outcome=record.outcome,
    )
    assert "opportunity.entity must match signal.entity" in broken.validate()


def test_missing_evidence_source_ref_is_rejected():
    record = make_suppliertr_record()
    broken = ProcurementVerticalRecord(
        case_id=record.case_id,
        evidence=Evidence(
            evidence_id=record.evidence.evidence_id,
            source=record.evidence.source,
            source_ref="",
            summary=record.evidence.summary,
            observed_at=record.evidence.observed_at,
            confidence=record.evidence.confidence,
            kind=record.evidence.kind,
        ),
        relationship=record.relationship,
        signal=record.signal,
        opportunity=record.opportunity,
        outcome=record.outcome,
    )
    assert "evidence.source_ref is required" in broken.validate()


def test_missing_stable_identifier_is_rejected():
    record = make_suppliertr_record()
    broken = ProcurementVerticalRecord(
        case_id=record.case_id,
        evidence=record.evidence,
        relationship=record.relationship,
        signal=Signal(
            signal_id="",
            entity=record.signal.entity,
            signal_type=record.signal.signal_type,
            description=record.signal.description,
            evidence_id=record.signal.evidence_id,
            confidence=record.signal.confidence,
        ),
        opportunity=record.opportunity,
        outcome=record.outcome,
    )
    assert "signal.signal_id is required" in broken.validate()


def test_unsupported_evidence_kind_is_rejected():
    record = make_suppliertr_record()
    broken = ProcurementVerticalRecord(
        case_id=record.case_id,
        evidence=Evidence(
            evidence_id=record.evidence.evidence_id,
            source=record.evidence.source,
            source_ref=record.evidence.source_ref,
            summary=record.evidence.summary,
            observed_at=record.evidence.observed_at,
            confidence=record.evidence.confidence,
            kind="certain",  # type: ignore[arg-type]
        ),
        relationship=record.relationship,
        signal=record.signal,
        opportunity=record.opportunity,
        outcome=record.outcome,
    )
    assert "evidence.kind must be a supported epistemic class" in broken.validate()
