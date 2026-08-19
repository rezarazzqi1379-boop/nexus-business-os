from nexus_core.decision_learning import DecisionRecord, OutcomeObservation, validate_decision_chain
from nexus_core.policy import ActionApproval, ActionIntent, evaluate_action
from nexus_evals import Assertion, EvaluationCase, evaluate_suite
from nexus_evals.promotion import (
    CaseOutcomeMetrics,
    PromotionPolicy,
    PromotionRun,
    promotion_decision,
)
from nexus_verticals.procurement import Evidence
from nexus_verticals.readiness import RequirementInput, assess_requirement_readiness


def test_readiness_and_action_gate_remain_independent_controls():
    readiness = assess_requirement_readiness(
        [
            RequirementInput(
                requirement_id="hydrotester.od",
                name="Pipe OD range",
                state="approved",
                value="89-180 mm",
                source_ref="engineering-authority:hydrotester:od:v1",
            ),
            RequirementInput(
                requirement_id="hydrotester.max_pressure",
                name="Maximum machine rating target",
                state="approved",
                value="120 MPa",
                source_ref="engineering-authority:hydrotester:pressure:v1",
            ),
            RequirementInput(
                requirement_id="hydrotester.length",
                name="Pipe length range",
                state="approved",
                value="synthetic-approved-value-for-integration-test",
                source_ref="engineering-authority:hydrotester:length:v1",
            ),
            RequirementInput(
                requirement_id="hydrotester.wall_or_id",
                name="Wall thickness or ID range",
                state="approved",
                value="synthetic-approved-value-for-integration-test",
                source_ref="engineering-authority:hydrotester:wall:v1",
            ),
        ]
    )
    assert readiness.ready_for_final_request is True

    intent = ActionIntent(
        action_id="send:hydrotester-final-rfq:integration-test",
        kind="send_external_message",
        description="Send technically ready RFQ.",
    )
    assert evaluate_action(intent).allowed_now is False
    assert evaluate_action(
        intent,
        approval=ActionApproval(action_id=intent.action_id),
    ).allowed_now is True
    assert evaluate_action(
        intent,
        approval=ActionApproval(action_id="approve:all-future-emails"),
    ).allowed_now is False


def test_supplier_claim_preserves_epistemic_class_through_decision_learning():
    evidence = Evidence(
        evidence_id="evidence:supplier-feasibility-claim",
        source="gmail",
        source_ref="gmail:message:supplier-feasibility-claim",
        summary="Supplier states that a custom 120 MPa machine is feasible.",
        observed_at="2026-08-19",
        confidence=1.0,
        kind="claim",
    )
    assert evidence.kind == "claim"

    decision = DecisionRecord(
        decision_id="decision:verify-120mpa-capability",
        subject="120 MPa Hydrotester capability",
        decision="Require project-specific evidence before treating capability as verified.",
        rationale="Supplier statements do not prove compliance for the exact project envelope.",
        expected_outcome="Qualification remains open until project-specific evidence exists.",
        success_criterion="No verified-capability label is assigned from supplier claim alone.",
        review_at="2026-08-22",
        evidence_refs=(evidence.source_ref,),
        status="active",
    )
    observation = OutcomeObservation(
        observation_id="observation:supplier-120mpa-claim",
        decision_id=decision.decision_id,
        observed_at="2026-08-22T10:00:00+00:00",
        result=evidence.summary,
        source_refs=(evidence.source_ref,),
        kind="claim",
    )
    assert validate_decision_chain(decision, observation) == []
    assert observation.kind == "claim"


def test_canonical_eval_and_promotion_block_historical_blanket_approval_regression():
    suite = evaluate_suite(
        (
            EvaluationCase(
                case_id="case:action-gate",
                name="Mismatched approval remains blocked",
                input_ref="github:pr4",
                observations={
                    "gate": {
                        "allowed_now": True,
                        "requires_human_approval": False,
                    }
                },
                assertions=(
                    Assertion(
                        assertion_id="blocked",
                        path="gate.allowed_now",
                        operator="equals",
                        expected=False,
                    ),
                    Assertion(
                        assertion_id="approval-required",
                        path="gate.requires_human_approval",
                        operator="equals",
                        expected=True,
                    ),
                ),
                evidence_refs=("github:pr4",),
            ),
        )
    )
    assert suite.failed_cases == 1

    run = PromotionRun(
        run_id="integration:canonical-eval",
        system_version="integration:pr1+pr2+pr4+pr6+pr7",
        harness_version="evaluation-harness-v0.1",
        config_ref="notion:draft-pr-integration-map",
        suite=suite,
        metrics=(
            CaseOutcomeMetrics(
                case_id="case:action-gate",
                policy_violations=1,
                failure_tags=("human_gate_bypass",),
            ),
        ),
        critical_case_ids=("case:action-gate",),
    )
    decision = promotion_decision(
        run,
        PromotionPolicy(
            max_failed_cases=1,
            max_policy_violations=0,
            require_zero_critical_failures=True,
        ),
    )

    assert decision.allowed is False
    assert "policy_violation_budget_exceeded" in decision.blockers
    assert "critical_case_failure" in decision.blockers
