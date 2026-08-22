from nexus_verticals.business_genome import Decision
from nexus_verticals.business_genome_learning import (
    NegativeKnowledgeEvent,
    OutcomeKind,
    OutcomeLedgerEntry,
)
from nexus_verticals.pattern_miner import mine_failure_patterns, mine_success_patterns


def neg(eid: str, oid: str, project: str, category: str = "scope_mismatch"):
    return NegativeKnowledgeEvent(
        event_id=eid,
        observation_id=oid,
        project_id=project,
        category=category,
        reason="observed failure",
        source_ref=f"source:{oid}",
    )


def ledger(lid: str, oid: str, project: str, stage: str = "reply"):
    return OutcomeLedgerEntry(
        ledger_id=lid,
        observation_id=oid,
        project_id=project,
        recommendation=Decision.PURSUE,
        human_decision=Decision.PURSUE,
        outcome_kind=OutcomeKind.STAGE_SUCCESS,
        outcome_stage=stage,
        source_ref=f"source:{oid}",
    )


def test_single_failure_is_not_generalized():
    patterns = mine_failure_patterns([neg("n1", "o1", "p1")])
    assert len(patterns) == 1
    assert patterns[0].eligible_for_improvement_proposal is False


def test_repeated_cross_project_failure_becomes_proposal_eligible():
    patterns = mine_failure_patterns([
        neg("n1", "o1", "p1"),
        neg("n2", "o2", "p2"),
    ])
    assert patterns[0].occurrences == 2
    assert patterns[0].distinct_projects == 2
    assert patterns[0].eligible_for_improvement_proposal is True


def test_same_project_repetition_does_not_satisfy_diversity_gate():
    patterns = mine_failure_patterns([
        neg("n1", "o1", "p1"),
        neg("n2", "o2", "p1"),
    ])
    assert patterns[0].eligible_for_improvement_proposal is False


def test_success_miner_only_uses_success_entries():
    rows = [
        ledger("l1", "o1", "p1"),
        OutcomeLedgerEntry(
            ledger_id="l2",
            observation_id="o2",
            project_id="p2",
            recommendation=Decision.RESEARCH,
            human_decision=Decision.RESEARCH,
            outcome_kind=OutcomeKind.ALIGNMENT,
            outcome_stage=None,
            source_ref="source:o2",
        ),
    ]
    patterns = mine_success_patterns(rows)
    assert len(patterns) == 1
    assert patterns[0].key == "reply"
    assert patterns[0].occurrences == 1


def test_repeated_cross_project_success_becomes_eligible():
    patterns = mine_success_patterns([
        ledger("l1", "o1", "p1", "reply"),
        ledger("l2", "o2", "p2", "reply"),
    ])
    assert patterns[0].eligible_for_improvement_proposal is True


def test_conflicting_duplicate_failure_event_fails_closed():
    a = neg("n1", "o1", "p1")
    b = NegativeKnowledgeEvent(
        event_id="n1",
        observation_id="o2",
        project_id="p2",
        category="scope_mismatch",
        reason="different",
        source_ref="source:o2",
    )
    try:
        mine_failure_patterns([a, b])
    except ValueError as exc:
        assert "conflicting duplicate" in str(exc)
    else:
        raise AssertionError("expected conflicting duplicate to fail closed")


def test_thresholds_cannot_be_weakened_to_single_anecdote():
    try:
        mine_failure_patterns([neg("n1", "o1", "p1")], min_occurrences=1)
    except ValueError as exc:
        assert "min_occurrences" in str(exc)
    else:
        raise AssertionError("expected single-occurrence threshold to be rejected")
