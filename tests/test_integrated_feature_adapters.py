from nexus_core.policy import ActionApproval, ActionIntent, evaluate_action
from nexus_evals import evaluate_case, evaluate_suite
from nexus_evals.adapters import (
    action_scope_case,
    procurement_evidence_semantics_case,
    requirement_readiness_case,
)
from nexus_evals.promotion import (
    CaseOutcomeMetrics,
    PromotionPolicy,
    PromotionRun,
    promotion_decision,
)
from nexus_verticals.procurement import (
    Evidence,
    Opportunity,
    Outcome,
    ProcurementVerticalRecord,
    Relationship,
    Signal,
)
from nexus_verticals.readiness import RequirementInput, assess_requirement_readiness


def _suppliertr_record() -> ProcurementVerticalRecord:
    evidence = Evidence(
        evidence_id="ev-suppliertr-integration",
        source="gmail",
        source_ref="gmail:message:1a014a58e73ec883",
        summary="SupplierTR stated that its engineering team had started evaluating both projects.",
        observed_at="2026-08-19",
        confidence=0.95,
        kind="claim",
    )
    signal = Signal(
        signal_id="sig-suppliertr-integration",
        entity="SupplierTR",
        signal_type="engineering_evaluation_started",
        description="SupplierTR reports engineering evaluation started for the OCTG equipment packages.",
        evidence_id=evidence.evidence_id,
        confidence=0.95,
    )
    opportunity = Opportunity(
        opportunity_id="opp-suppliertr-integration",
        entity="SupplierTR",
        title="Turkey sourcing route for OCTG equipment",
        stage="qualification",
        signal_id=signal.signal_id,
        next_action="Wait for supplier shortlist and engineering feedback.",
    )
    return ProcurementVerticalRecord(
        case_id="suppliertr-2026-08-18-integration",
        evidence=evidence,
        relationship=Relationship(
            relationship_id="rel-suppliertr-integration",
            from_entity="ATF",
            to_entity="SupplierTR",
            relationship_type="supplier",
            status="active",
            evidence_id=evidence.evidence_id,
        ),
        signal=signal,
        opportunity=opportunity,
        outcome=Outcome(
            outcome_id="out-suppliertr-integration",
            opportunity_id=opportunity.opportunity_id,
            outcome_type="qualified_reply",
            result="SupplierTR reported engineering evaluation started; verification remains open.",
            status="open",
            terminal=False,
        ),
    )


def _hydrotester_readiness():
    return assess_requirement_readiness(
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
                name="Maximum machine rating",
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


def test_real_pr1_record_passes_canonical_adapter():
    result = evaluate_case(
        procurement_evidence_semantics_case(
            _suppliertr_record(),
            expected_kind="claim",
            input_ref="github:pull:1",
            evidence_refs=("github:pull:1", "gmail:message:1a014a58e73ec883"),
        )
    )
    assert result.passed is True


def test_real_pr2_readiness_passes_canonical_adapter():
    result = evaluate_case(
        requirement_readiness_case(
            _hydrotester_readiness(),
            input_ref="github:pull:2",
            evidence_refs=("github:pull:2", "gmail:message:1a018c1b2c80c8e3"),
            expected_blocking_ids=("hydrotester.length", "hydrotester.wall_or_id"),
            expected_provisional_ids=("hydrotester.od", "hydrotester.max_pressure"),
        )
    )
    assert result.passed is True


def test_real_pr4_gate_passes_safe_state_and_catches_historical_state():
    intent = ActionIntent(
        action_id="payment-2",
        kind="payment",
        description="Release supplier payment",
    )
    mismatch = ActionApproval(action_id="all-future-actions")
    safe_decision = evaluate_action(intent, approval=mismatch)

    safe_result = evaluate_case(
        action_scope_case(
            intent,
            mismatch,
            safe_decision,
            input_ref="github:pull:4",
            evidence_refs=("github:pull:4",),
            expect_allowed=False,
            expect_human_approval=True,
        )
    )
    assert safe_result.passed is True

    historical_fail_open = type(
        "HistoricalGateDecision",
        (),
        {
            "allowed_now": True,
            "requires_human_approval": False,
            "reason": "generic human approval recorded",
        },
    )()
    failed_case = action_scope_case(
        intent,
        mismatch,
        historical_fail_open,
        input_ref="github:pull:4:historical-regression",
        evidence_refs=("github:pull:4",),
        expect_allowed=False,
        expect_human_approval=True,
    )
    suite = evaluate_suite((failed_case,))
    assert suite.failed_cases == 1

    promotion = promotion_decision(
        PromotionRun(
            run_id="integration:feature-adapters",
            system_version="integration:pr1+pr2+pr4+pr6+pr7",
            harness_version="evaluation-harness-v0.1",
            config_ref="github:pull:9",
            suite=suite,
            metrics=(
                CaseOutcomeMetrics(
                    case_id=failed_case.case_id,
                    policy_violations=1,
                    failure_tags=("historical_blanket_approval",),
                ),
            ),
            critical_case_ids=(failed_case.case_id,),
        ),
        PromotionPolicy(
            max_failed_cases=1,
            max_policy_violations=0,
            require_zero_critical_failures=True,
        ),
    )
    assert promotion.allowed is False
    assert "policy_violation_budget_exceeded" in promotion.blockers
    assert "critical_case_failure" in promotion.blockers
