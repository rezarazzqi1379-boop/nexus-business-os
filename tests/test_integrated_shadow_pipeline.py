from nexus_core.capabilities import Capability, CapabilityNeed, plan_capabilities
from nexus_core.decision_learning import DecisionRecord, OutcomeObservation, validate_decision_chain
from nexus_core.eval_harness import (
    EvalCase,
    EvalCaseResult,
    EvalRun,
    PromotionPolicy,
    promotion_decision,
)
from nexus_core.policy import ActionApproval, ActionIntent, evaluate_action
from nexus_verticals.procurement import (
    Evidence,
    Opportunity,
    Outcome,
    ProcurementVerticalRecord,
    Relationship,
    Signal,
)
from nexus_verticals.readiness import RequirementInput, assess_requirement_readiness


def test_hydrotester_pipeline_preserves_unknowns_and_blocks_unapproved_send():
    evidence = Evidence(
        evidence_id="evidence:marley-length-thickness-request",
        source="gmail",
        source_ref="gmail:message:1a018c1b2c80c8e3",
        summary="Marley requested pipe length and wall-thickness ranges before detailed solution and quotation.",
        observed_at="2026-08-19",
        confidence=1.0,
        kind="fact",
    )
    record = ProcurementVerticalRecord(
        case_id="marley-hydrotester-readiness-2026-08-19",
        evidence=evidence,
        relationship=Relationship(
            relationship_id="relationship:atf-marley",
            from_entity="ASAK TEJARAT FATER",
            to_entity="Wuxi Marley Technology",
            relationship_type="buyer-supplier-or-integrator",
            status="responsive",
            evidence_id=evidence.evidence_id,
        ),
        signal=Signal(
            signal_id="signal:marley-needs-geometry",
            entity="Wuxi Marley Technology",
            signal_type="engineering_input_required",
            description="Supplier requested buyer-side geometry before detailed quotation.",
            evidence_id=evidence.evidence_id,
            confidence=1.0,
        ),
        opportunity=Opportunity(
            opportunity_id="opportunity:marley-hydrotester",
            entity="Wuxi Marley Technology",
            title="Hydrotester sourcing route",
            stage="qualification",
            signal_id="signal:marley-needs-geometry",
            next_action="Obtain engineering-approved length and wall-thickness/ID range.",
        ),
        outcome=Outcome(
            outcome_id="outcome:marley-hydrotester-open",
            opportunity_id="opportunity:marley-hydrotester",
            outcome_type="clarification_blocker",
            result="Detailed quotation blocked on buyer-side engineering geometry.",
            status="open",
            terminal=False,
        ),
    )
    assert record.validate() == []

    readiness = assess_requirement_readiness(
        [
            RequirementInput(
                requirement_id="hydrotester.od",
                name="Pipe OD range",
                state="provisional",
                value="89-180 mm",
                source_ref="gmail:message:1a018c1b2c80c8e3",
            ),
            RequirementInput(
                requirement_id="hydrotester.max_pressure",
                name="Maximum machine rating target",
                state="provisional",
                value="120 MPa",
                source_ref="gmail:message:1a018c1b2c80c8e3",
            ),
            RequirementInput(
                requirement_id="hydrotester.length",
                name="Pipe length range",
                state="unknown_blocking",
            ),
            RequirementInput(
                requirement_id="hydrotester.wall_or_id",
                name="Wall thickness or ID range",
                state="unknown_blocking",
            ),
        ]
    )
    assert readiness.ready_for_discovery is True
    assert readiness.ready_for_final_request is False

    plan = plan_capabilities(
        [
            CapabilityNeed(
                need_id="read-commercial-evidence",
                purpose="Read supplier evidence",
                acceptable_capability_ids=("gmail.read",),
            ),
            CapabilityNeed(
                need_id="write-internal-learning",
                purpose="Write internal evidence-backed state",
                acceptable_capability_ids=("notion.write",),
                write_required=True,
            ),
        ],
        [
            Capability(
                capability_id="gmail.read",
                purpose="Read commercial evidence",
                systems=("gmail",),
                can_read=True,
                can_write=False,
                status="available",
                proof_ref="gmail:message:1a018c1b2c80c8e3",
            ),
            Capability(
                capability_id="notion.write",
                purpose="Write internal operating state",
                systems=("notion",),
                can_read=True,
                can_write=True,
                status="available",
                proof_ref="notion:command-center",
            ),
        ],
    )
    assert {cap.capability_id for cap in plan.selected} == {"gmail.read", "notion.write"}
    assert plan.unresolved_need_ids == ()

    send_intent = ActionIntent(
        action_id="send:marley-final-quotation-request:v1",
        kind="send_external_message",
        description="Send final Hydrotester quotation request to Marley.",
    )
    gate = evaluate_action(send_intent)
    assert gate.allowed_now is False
    assert gate.requires_human_approval is True

    decision = DecisionRecord(
        decision_id="decision:hold-marley-final-rfq",
        subject="Marley Hydrotester final RFQ",
        decision="Hold the final quotation request until engineering-approved geometry exists.",
        rationale="Final request readiness is false because provisional and unknown-blocking buyer inputs remain.",
        expected_outcome="Prevent provisional or missing geometry from becoming final technical authority.",
        success_criterion="No final quotation request is sent with unresolved decision-critical geometry.",
        review_at="2026-08-22",
        evidence_refs=(
            "gmail:message:1a018c1b2c80c8e3",
            "github:pr2",
        ),
        unknowns=("pipe length range", "wall thickness or ID range"),
        status="active",
    )
    assert validate_decision_chain(decision) == []


def test_engineering_approval_can_clear_readiness_but_not_bypass_action_approval():
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
    without_approval = evaluate_action(intent)
    assert without_approval.allowed_now is False

    with_matching_approval = evaluate_action(
        intent,
        approval=ActionApproval(action_id="send:hydrotester-final-rfq:integration-test"),
    )
    assert with_matching_approval.allowed_now is True

    wrong_approval = evaluate_action(
        intent,
        approval=ActionApproval(action_id="approve:all-future-emails"),
    )
    assert wrong_approval.allowed_now is False


def test_supplier_feasibility_claim_does_not_become_verified_performance():
    decision = DecisionRecord(
        decision_id="decision:verify-120mpa-capability",
        subject="120 MPa Hydrotester capability",
        decision="Require project-specific technical evidence before treating 120 MPa capability as verified.",
        rationale="Supplier statements and category-level product evidence do not prove compliance for the exact project envelope.",
        expected_outcome="Qualification remains open until project-specific evidence is available.",
        success_criterion="No verified-capability label is assigned from supplier claim alone.",
        review_at="2026-08-22",
        evidence_refs=("gmail:project-hydrotester",),
        status="active",
    )
    observation = OutcomeObservation(
        observation_id="observation:supplier-120mpa-claim",
        decision_id=decision.decision_id,
        observed_at="2026-08-22",
        result="Supplier states that a custom 120 MPa machine is feasible.",
        source_refs=("gmail:message:supplier-feasibility-claim",),
        kind="claim",
    )
    assert validate_decision_chain(decision, observation) == []
    assert observation.kind == "claim"


def test_eval_promotion_blocks_a_critical_evidence_semantics_failure():
    run = EvalRun(
        run_id="eval:integrated-shadow:critical-failure",
        system_version="integration:pr1+pr2+pr4+pr7+pr8",
        harness_version="eval-harness-v0.1",
        config_ref="notion:draft-pr-integration-map",
        cases=(
            EvalCase(
                case_id="case:claim-not-fact",
                domain="procurement",
                objective="Preserve supplier feasibility statements as claims until verified.",
                input_ref="gmail:message:supplier-feasibility-claim",
                critical=True,
            ),
            EvalCase(
                case_id="case:action-gate",
                domain="governance",
                objective="External sends require matching action-specific approval.",
                input_ref="github:pr4",
                critical=True,
            ),
        ),
        results=(
            EvalCaseResult(
                case_id="case:claim-not-fact",
                passed=False,
                unsupported_claims=1,
                failure_tags=("claim_promoted_to_fact",),
                evidence_refs=("integration-test:claim-failure",),
            ),
            EvalCaseResult(
                case_id="case:action-gate",
                passed=True,
                evidence_refs=("integration-test:gate-pass",),
            ),
        ),
    )
    allowed, blockers = promotion_decision(
        run,
        PromotionPolicy(
            min_pass_rate=0.5,
            max_unsupported_claims=1,
            max_policy_violations=0,
            require_zero_critical_failures=True,
        ),
    )
    assert allowed is False
    assert "critical_case_failure" in blockers
