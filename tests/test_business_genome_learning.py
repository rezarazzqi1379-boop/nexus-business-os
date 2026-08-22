from nexus_verticals.business_genome import Decision
from nexus_verticals.business_genome_evaluation import ShadowDecisionObservation
from nexus_verticals.business_genome_learning import (
    OutcomeKind,
    build_learning_batch,
    classify_outcome,
)


def obs(
    oid: str,
    recommendation: Decision,
    human: Decision | None = None,
    success: bool | None = None,
    stage: str | None = None,
    safety: bool = False,
):
    return ShadowDecisionObservation(
        observation_id=oid,
        project_id="project:test",
        case_type="test",
        recommendation=recommendation,
        human_decision=human,
        outcome_success=success,
        outcome_stage=stage,
        safety_violation=safety,
        source_ref=f"source:{oid}",
    )


def test_reply_success_is_not_final_success():
    row = obs("reply", Decision.PURSUE, Decision.PURSUE, True, "reply")
    assert classify_outcome(row) == OutcomeKind.STAGE_SUCCESS


def test_order_success_is_final_success():
    row = obs("order", Decision.PURSUE, Decision.PURSUE, True, "order")
    assert classify_outcome(row) == OutcomeKind.FINAL_SUCCESS


def test_pursue_failure_creates_negative_knowledge():
    row = obs("fp", Decision.PURSUE, Decision.PURSUE, False, "quote")
    ledger, negative = build_learning_batch([row])
    assert ledger[0].outcome_kind == OutcomeKind.FALSE_POSITIVE
    assert len(negative) == 1
    assert negative[0].category == "pursue_false_positive"


def test_research_alignment_without_outcome_is_not_failure():
    row = obs("alignment", Decision.RESEARCH, Decision.RESEARCH)
    ledger, negative = build_learning_batch([row])
    assert ledger[0].outcome_kind == OutcomeKind.ALIGNMENT
    assert negative == ()


def test_safety_violation_always_enters_negative_knowledge():
    row = obs("unsafe", Decision.RESEARCH, Decision.RESEARCH, safety=True)
    ledger, negative = build_learning_batch([row])
    assert ledger[0].outcome_kind == OutcomeKind.SAFETY_FAILURE
    assert negative[0].category == "safety_failure"


def test_batch_deduplicates_identical_observation_ids():
    row = obs("same", Decision.RESEARCH, Decision.RESEARCH)
    ledger, negative = build_learning_batch([row, row])
    assert len(ledger) == 1
    assert negative == ()


def test_batch_rejects_conflicting_duplicate_observation_ids():
    a = obs("same", Decision.RESEARCH, Decision.RESEARCH)
    b = obs("same", Decision.PURSUE, Decision.PURSUE)
    try:
        build_learning_batch([a, b])
    except ValueError as exc:
        assert "conflicting duplicate" in str(exc)
    else:
        raise AssertionError("conflicting duplicate should fail closed")
