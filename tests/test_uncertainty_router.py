from nexus_core.uncertainty_router import (
    EvidenceItem,
    NextAction,
    UncertaintyKind,
    classify_uncertainty,
)


def ev(eid: str, value: str, confidence: float, source: str) -> EvidenceItem:
    return EvidenceItem(evidence_id=eid, value=value, confidence=confidence, source_ref=source)


def test_no_evidence_routes_to_collection():
    decision = classify_uncertainty(())
    assert decision.kind is UncertaintyKind.EVIDENCE_GAP
    assert decision.next_action is NextAction.COLLECT_EVIDENCE


def test_strong_conflicting_evidence_routes_to_conflict_resolution():
    decision = classify_uncertainty(
        (
            ev("e1", "70 MPa", 0.95, "official:boyu"),
            ev("e2", "120 MPa", 0.92, "photo:machine-plate"),
        )
    )
    assert decision.kind is UncertaintyKind.CONFLICT
    assert decision.next_action is NextAction.RESOLVE_CONFLICT


def test_single_source_same_value_is_still_evidence_gap():
    decision = classify_uncertainty((ev("e1", "1200 MT", 0.9, "gmail:oms"),))
    assert decision.kind is UncertaintyKind.EVIDENCE_GAP
    assert decision.next_action is NextAction.COLLECT_EVIDENCE


def test_low_confidence_mixed_values_go_to_experiment():
    decision = classify_uncertainty(
        (
            ev("e1", "A", 0.5, "source:a"),
            ev("e2", "B", 0.6, "source:b"),
        )
    )
    assert decision.kind is UncertaintyKind.LOW_CONFIDENCE
    assert decision.next_action is NextAction.RUN_EXPERIMENT


def test_consistent_strong_evidence_can_promote():
    decision = classify_uncertainty(
        (
            ev("e1", "same", 0.9, "source:a"),
            ev("e2", "same", 0.85, "source:b"),
        )
    )
    assert decision.kind is UncertaintyKind.NONE
    assert decision.next_action is NextAction.PROMOTE
