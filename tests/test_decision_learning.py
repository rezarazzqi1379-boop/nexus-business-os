from nexus_core.decision_learning import (
    DecisionEvaluation,
    DecisionRecord,
    OutcomeObservation,
    validate_decision_chain,
)


def make_yaxing_decision(status: str = "active") -> DecisionRecord:
    return DecisionRecord(
        decision_id="decision:yaxing-hydrotester-readiness",
        subject="YAXING hydrotester route",
        decision="Hold final quotation request until engineering confirms pipe length and wall thickness/ID.",
        rationale="Supplier engagement exists, but decision-critical buyer-side geometry remains unresolved.",
        expected_outcome="Engineering clarification prevents provisional geometry from being promoted to final technical authority.",
        success_criterion="Final quotation request uses engineering-approved geometry or explicitly remains blocked.",
        review_at="2026-08-22",
        evidence_refs=(
            "gmail:message:1a00d9e238e2941b",
            "notion:outcome:yaxing-engineering-input-blocker",
        ),
        unknowns=("minimum/maximum pipe length", "wall-thickness or ID range"),
        status=status,  # type: ignore[arg-type]
    )


def test_active_decision_without_outcome_is_valid():
    assert validate_decision_chain(make_yaxing_decision()) == []


def test_evaluated_decision_requires_observation_and_evaluation():
    decision = make_yaxing_decision(status="evaluated")
    errors = validate_decision_chain(decision)
    assert "evaluated decision requires an observation" in errors
    assert "evaluated decision requires an evaluation" in errors


def test_complete_inconclusive_learning_loop_is_valid():
    decision = make_yaxing_decision(status="evaluated")
    observation = OutcomeObservation(
        observation_id="observation:yaxing-2026-08-22",
        decision_id=decision.decision_id,
        observed_at="2026-08-22",
        result="Engineering input is still incomplete; supplier route remains open but final quotation is blocked.",
        source_refs=("gmail:message:future-engineer-or-supplier-evidence",),
        kind="fact",
    )
    evaluation = DecisionEvaluation(
        evaluation_id="evaluation:yaxing-2026-08-22",
        decision_id=decision.decision_id,
        observation_id=observation.observation_id,
        classification="inconclusive",
        learning="The readiness gate preserved uncertainty but the cycle-time effect is not yet measurable.",
        next_action="Obtain engineering-approved geometry and rerun the quotation step.",
    )
    assert validate_decision_chain(decision, observation, evaluation) == []


def test_evaluation_without_observation_is_rejected():
    decision = make_yaxing_decision(status="evaluated")
    evaluation = DecisionEvaluation(
        evaluation_id="evaluation:bad",
        decision_id=decision.decision_id,
        observation_id="observation:missing",
        classification="confirmed",
        learning="unsupported",
        next_action="none",
    )
    assert "evaluation requires an observation" in validate_decision_chain(
        decision, evaluation=evaluation
    )


def test_broken_observation_link_is_rejected():
    decision = make_yaxing_decision(status="active")
    observation = OutcomeObservation(
        observation_id="observation:wrong-link",
        decision_id="decision:other",
        observed_at="2026-08-22",
        result="reply received",
        source_refs=("gmail:message:example",),
        kind="fact",
    )
    assert "observation.decision_id must match decision.decision_id" in validate_decision_chain(
        decision, observation
    )


def test_decision_requires_retrievable_evidence():
    decision = DecisionRecord(
        decision_id="decision:no-proof",
        subject="test",
        decision="do something",
        rationale="because",
        expected_outcome="result",
        success_criterion="criterion",
        review_at="2026-08-22",
        evidence_refs=(),
        status="planned",
    )
    assert (
        "decision.evidence_refs must contain at least one retrievable reference"
        in validate_decision_chain(decision)
    )


def test_claim_observation_can_be_preserved_without_becoming_fact():
    decision = make_yaxing_decision(status="active")
    observation = OutcomeObservation(
        observation_id="observation:supplier-claim",
        decision_id=decision.decision_id,
        observed_at="2026-08-22",
        result="Supplier states that a custom 120 MPa solution is feasible.",
        source_refs=("gmail:message:supplier-claim",),
        kind="claim",
    )
    assert validate_decision_chain(decision, observation) == []
