from nexus_verticals.procurement import (
    Evidence,
    Opportunity,
    Outcome,
    ProcurementVerticalRecord,
    Relationship,
    Signal,
)


def test_suppliertr_closed_loop_is_valid():
    record = ProcurementVerticalRecord(
        case_id="suppliertr-2026-08-19",
        evidence=Evidence(
            source="gmail",
            source_ref="gmail:thread:suppliertr",
            summary="SupplierTR confirmed engineering evaluation",
            observed_at="2026-08-19",
            confidence=0.95,
        ),
        relationship=Relationship(
            from_entity="ASAK TEJARAT FATER",
            to_entity="SupplierTR",
            relationship_type="buyer-sourcing-intermediary",
            status="responsive",
            evidence_ref="gmail:thread:suppliertr",
        ),
        signal=Signal(
            entity="SupplierTR",
            signal_type="engineering_evaluation_started",
            description="SupplierTR started engineering evaluation",
            evidence_ref="gmail:thread:suppliertr",
            confidence=0.95,
        ),
        opportunity=Opportunity(
            entity="SupplierTR",
            title="Turkey sourcing route for OCTG equipment",
            stage="qualification",
            signal_ref="SupplierTR started engineering evaluation",
            next_action="await supplier shortlist",
        ),
        outcome=Outcome(
            opportunity_ref="Turkey sourcing route for OCTG equipment",
            outcome_type="qualified_reply",
            result="engineering evaluation started",
            terminal=False,
        ),
    )

    assert record.validate() == []


def test_broken_evidence_link_is_rejected():
    record = ProcurementVerticalRecord(
        case_id="broken-case",
        evidence=Evidence("gmail", "gmail:1", "reply", "2026-08-19", 0.9),
        relationship=Relationship("ATF", "Supplier", "commercial", "responsive", "gmail:2"),
        signal=Signal("Supplier", "reply", "supplier replied", "gmail:1", 0.9),
        opportunity=Opportunity("Supplier", "Opportunity", "qualification", "supplier replied", "review"),
        outcome=Outcome("Opportunity", "micro_outcome", "reply received"),
    )

    assert "relationship.evidence_ref must match evidence.source_ref" in record.validate()
