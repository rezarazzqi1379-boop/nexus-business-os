from nexus_core.policy import ActionIntent, evaluate_action
from nexus_evals import Assertion, EvaluationCase, evaluate_suite
from nexus_evals.promotion import (
    CaseOutcomeMetrics,
    PromotionPolicy,
    PromotionRun,
    promotion_decision,
)
from nexus_observability import TraceEvent, validate_trace
from nexus_verticals.readiness import RequirementInput, assess_requirement_readiness


def test_hydrotester_shadow_chain_is_reconstructable_without_sensitive_payloads():
    assessment = assess_requirement_readiness(
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
    assert assessment.ready_for_discovery is True
    assert assessment.ready_for_final_request is False

    suite = evaluate_suite(
        (
            EvaluationCase(
                case_id="case:hydrotester-readiness-shadow",
                name="Unknown/provisional engineering inputs remain explicit",
                input_ref="gmail:message:1a018c1b2c80c8e3",
                observations={
                    "decision": {
                        "ready_for_discovery": assessment.ready_for_discovery,
                        "ready_for_final_request": assessment.ready_for_final_request,
                    },
                    "requirements": {
                        "blocking_ids": assessment.blocking_ids,
                        "provisional_ids": assessment.provisional_ids,
                    },
                },
                assertions=(
                    Assertion(
                        assertion_id="discovery-open",
                        path="decision.ready_for_discovery",
                        operator="equals",
                        expected=True,
                    ),
                    Assertion(
                        assertion_id="final-request-blocked",
                        path="decision.ready_for_final_request",
                        operator="equals",
                        expected=False,
                    ),
                    Assertion(
                        assertion_id="length-stays-blocking",
                        path="requirements.blocking_ids",
                        operator="contains",
                        expected="hydrotester.length",
                    ),
                    Assertion(
                        assertion_id="wall-stays-blocking",
                        path="requirements.blocking_ids",
                        operator="contains",
                        expected="hydrotester.wall_or_id",
                    ),
                ),
                evidence_refs=(
                    "gmail:message:1a018c1b2c80c8e3",
                    "github:pr:2",
                ),
            ),
        )
    )
    assert suite.passed is True

    promotion = promotion_decision(
        PromotionRun(
            run_id="promotion:hydrotester-shadow:1",
            system_version="integration:pr1+pr2+pr4+pr6+pr7+pr11",
            harness_version="evaluation-harness-v0.1",
            config_ref="github:pr:11",
            suite=suite,
            metrics=(
                CaseOutcomeMetrics(case_id="case:hydrotester-readiness-shadow"),
            ),
            critical_case_ids=("case:hydrotester-readiness-shadow",),
        ),
        PromotionPolicy(),
    )
    assert promotion.allowed is True

    intent = ActionIntent(
        action_id="send:hydrotester-final-rfq:trace-test",
        kind="send_external_message",
        description="Send final Hydrotester RFQ while engineering blockers remain.",
    )
    gate = evaluate_action(intent)
    assert gate.allowed_now is False
    assert gate.requires_human_approval is True

    trace = (
        TraceEvent(
            event_id="event:evidence:marley-readiness",
            trace_id="trace:hydrotester:shadow:1",
            occurred_at="2026-08-19T14:40:00Z",
            event_type="evidence_read",
            actor="nexus:research",
            result="success",
            correlation_ref="hydrotester:rfq:shadow",
            evidence_refs=("gmail:message:1a018c1b2c80c8e3",),
            payload_ref="gmail:message:1a018c1b2c80c8e3",
            attributes={"domain": "procurement", "status": "shadow"},
        ),
        TraceEvent(
            event_id="event:decision:readiness",
            trace_id="trace:hydrotester:shadow:1",
            occurred_at="2026-08-19T14:41:00Z",
            event_type="decision_recorded",
            actor="nexus:readiness",
            result="blocked",
            parent_event_id="event:evidence:marley-readiness",
            correlation_ref="hydrotester:rfq:shadow",
            decision_ref="decision:hydrotester-final-request-readiness",
            evidence_refs=("github:pr:2",),
            attributes={"reason_code": "unknown_blocking_requirements"},
        ),
        TraceEvent(
            event_id="event:eval:readiness",
            trace_id="trace:hydrotester:shadow:1",
            occurred_at="2026-08-19T14:42:00Z",
            event_type="evaluation_completed",
            actor="nexus:eval",
            result="success",
            parent_event_id="event:decision:readiness",
            correlation_ref="hydrotester:rfq:shadow",
            eval_ref="case:hydrotester-readiness-shadow",
            evidence_refs=("github:pr:6",),
            attributes={"harness_version": "evaluation-harness-v0.1"},
        ),
        TraceEvent(
            event_id="event:promotion:readiness",
            trace_id="trace:hydrotester:shadow:1",
            occurred_at="2026-08-19T14:43:00Z",
            event_type="promotion_decided",
            actor="nexus:promotion",
            result="success",
            parent_event_id="event:eval:readiness",
            correlation_ref="hydrotester:rfq:shadow",
            eval_ref="promotion:hydrotester-shadow:1",
            evidence_refs=("github:pr:6",),
            attributes={"status": "regression-safe"},
        ),
        TraceEvent(
            event_id="event:approval:final-rfq",
            trace_id="trace:hydrotester:shadow:1",
            occurred_at="2026-08-19T14:44:00Z",
            event_type="approval_decided",
            actor="nexus:human-gate",
            result="blocked",
            parent_event_id="event:promotion:readiness",
            correlation_ref="hydrotester:rfq:shadow",
            action_ref=intent.action_id,
            evidence_refs=("github:pr:4",),
            attributes={"reason_code": "human_approval_required", "reversible": False},
        ),
    )

    validation = validate_trace(trace)
    assert validation.valid is True
    assert validation.errors == ()
    assert validation.root_event_ids == ("event:evidence:marley-readiness",)
    assert validation.terminal_event_ids == ("event:approval:final-rfq",)

    serialized = [event.to_dict() for event in trace]
    assert all("email_body" not in event["attributes"] for event in serialized)
    assert serialized[0]["payload_ref"] == "gmail:message:1a018c1b2c80c8e3"
