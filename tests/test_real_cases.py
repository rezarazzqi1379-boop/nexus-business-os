from nexus_verticals.procurement import (
    Evidence,
    EvidenceKind,
    Opportunity,
    Outcome,
    ProcurementVerticalRecord,
    Relationship,
    Signal,
)


def _record(
    *,
    case_id: str,
    supplier: str,
    gmail_message_id: str,
    evidence_summary: str,
    evidence_kind: EvidenceKind,
    signal_type: str,
    signal_description: str,
    opportunity_title: str,
    next_action: str,
    outcome_type: str,
    outcome_result: str,
) -> ProcurementVerticalRecord:
    evidence_id = f"evidence:{case_id}"
    signal_id = f"signal:{case_id}"
    opportunity_id = f"opportunity:{case_id}"

    return ProcurementVerticalRecord(
        case_id=case_id,
        evidence=Evidence(
            evidence_id=evidence_id,
            source="gmail",
            source_ref=f"gmail:message:{gmail_message_id}",
            summary=evidence_summary,
            observed_at="2026-08-19",
            confidence=0.95,
            kind=evidence_kind,
        ),
        relationship=Relationship(
            relationship_id=f"relationship:{case_id}",
            from_entity="ASAK TEJARAT FATER",
            to_entity=supplier,
            relationship_type="buyer-supplier-or-sourcing-partner",
            status="responsive",
            evidence_id=evidence_id,
        ),
        signal=Signal(
            signal_id=signal_id,
            entity=supplier,
            signal_type=signal_type,
            description=signal_description,
            evidence_id=evidence_id,
            confidence=0.95,
        ),
        opportunity=Opportunity(
            opportunity_id=opportunity_id,
            entity=supplier,
            title=opportunity_title,
            stage="qualification",
            signal_id=signal_id,
            next_action=next_action,
        ),
        outcome=Outcome(
            outcome_id=f"outcome:{case_id}",
            opportunity_id=opportunity_id,
            outcome_type=outcome_type,
            result=outcome_result,
            status="open",
            terminal=False,
        ),
    )


def test_suppliertr_real_case_closes_the_structural_loop():
    record = _record(
        case_id="suppliertr-2026-08-18",
        supplier="SupplierTR",
        gmail_message_id="1a014a58e73ec883",
        evidence_summary="SupplierTR stated that its engineering team had started evaluating both projects.",
        evidence_kind="claim",
        signal_type="engineering_evaluation_started",
        signal_description="Engineering evaluation started for the OCTG equipment packages.",
        opportunity_title="Turkey sourcing route for OCTG equipment",
        next_action="Wait for supplier shortlist and engineering feedback.",
        outcome_type="qualified_reply",
        outcome_result="Engineering evaluation started.",
    )
    assert record.validate() == []


def test_gh_petro_real_case_closes_the_structural_loop():
    record = _record(
        case_id="gh-petro-2026-08-18",
        supplier="GH Petro",
        gmail_message_id="1a0154f33233ec08",
        evidence_summary="GH Petro stated that it has experience with OCTG and steel-pipe production lines.",
        evidence_kind="claim",
        signal_type="qualified_supplier_reply",
        signal_description="Supplier claims relevant OCTG and steel-pipe line experience.",
        opportunity_title="Direct technical supplier route via GH Petro",
        next_action="Qualify technical scope, references, deviations, lead time and commercial terms.",
        outcome_type="qualified_reply",
        outcome_result="Relevant-capability reply received; qualification remains open.",
    )
    assert record.validate() == []


def test_yaxing_real_case_closes_the_structural_loop():
    record = _record(
        case_id="yaxing-2026-08-17",
        supplier="Karat Machinery / YAXING",
        gmail_message_id="1a00d9e238e2941b",
        evidence_summary="YAXING replied to the hydrotester inquiry and supplied its machinery catalog.",
        evidence_kind="fact",
        signal_type="technical_supplier_reply",
        signal_description="Supplier engaged and supplied catalog evidence for hydrotester evaluation.",
        opportunity_title="China hydrotester route via YAXING",
        next_action="Resolve final pipe-length and wall-thickness requirements before technical quotation.",
        outcome_type="technical_engagement",
        outcome_result="Catalog received; technical clarification remains open.",
    )
    assert record.validate() == []
