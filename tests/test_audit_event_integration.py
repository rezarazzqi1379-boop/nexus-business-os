from nexus_core.audit_events import AuditEvent, validate_audit_trace
from nexus_core.policy import ActionApproval, ActionIntent, evaluate_action
from nexus_evals import evaluate_suite
from nexus_evals.adapters import action_scope_case, requirement_readiness_case
from nexus_evals.promotion import (
    CaseOutcomeMetrics,
    PromotionPolicy,
    PromotionRun,
    promotion_decision,
)
from nexus_verticals.procurement import Evidence
from nexus_verticals.readiness import RequirementInput, assess_requirement_readiness


def test_real_shadow_control_chain_can_be_reconstructed_from_metadata_only_events():
    evidence = Evidence(
        evidence_id="evidence:marley:requirements",
        source="gmail",
        source_ref="gmail:message:1a018c1b2c80c8e3",
        summary="Supplier requested pipe length and wall thickness ranges.",
        observed_at="2026-08-19",
        confidence=1.0,
        kind="fact",
    )

    readiness = assess_requirement_readiness(
        (
            RequirementInput(
                requirement_id="hydrotester.od",
                name="Pipe OD range",
                state="provisional",
                value="89-180 mm",
                source_ref=evidence.source_ref,
            ),
            RequirementInput(
                requirement_id="hydrotester.max_pressure",
                name="Maximum machine rating target",
                state="provisional",
                value="120 MPa",
                source_ref=evidence.source_ref,
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
        )
    )

    intent = ActionIntent(
        action_id="send:hydrotester-final-rfq:shadow",
        kind="send_external_message",
        description="Send final Hydrotester RFQ",
    )
    mismatched_approval = ActionApproval(action_id="approve:all-future-emails")
    gate = evaluate_action(intent, approval=mismatched_approval)

    suite = evaluate_suite(
        (
            requirement_readiness_case(
                readiness,
                input_ref="github:pr2",
                evidence_refs=(evidence.source_ref, "github:pr2"),
                expected_blocking_ids=(
                    "hydrotester.length",
                    "hydrotester.wall_or_id",
                ),
                expected_provisional_ids=(
                    "hydrotester.od",
                    "hydrotester.max_pressure",
                ),
                expect_discovery_ready=True,
                expect_final_ready=False,
            ),
            action_scope_case(
                intent,
                mismatched_approval,
                gate,
                input_ref="github:pr4",
                evidence_refs=("github:pr4",),
                expect_allowed=False,
                expect_human_approval=True,
            ),
        )
    )
    assert suite.passed is True

    run = PromotionRun(
        run_id="run:audit-shadow",
        system_version="integration:pr1+pr2+pr4+pr6+pr7+pr10",
        harness_version="evaluation-harness-v0.1",
        config_ref="github:pr10",
        suite=suite,
        metrics=tuple(
            CaseOutcomeMetrics(case_id=result.case_id) for result in suite.results
        ),
        critical_case_ids=tuple(result.case_id for result in suite.results),
    )
    promotion = promotion_decision(run, PromotionPolicy())
    assert promotion.allowed is True
    assert gate.allowed_now is False
    assert gate.requires_human_approval is True

    events = (
        AuditEvent(
            event_id="event:evidence",
            trace_id="trace:hydrotester-shadow",
            event_type="evidence_observed",
            occurred_at="2026-08-19T14:35:00+00:00",
            actor_type="external_source",
            subject_ref=evidence.source_ref,
            result_class="observed",
            evidence_refs=(evidence.source_ref,),
            correlation_refs=("github:pr1",),
        ),
        AuditEvent(
            event_id="event:readiness",
            trace_id="trace:hydrotester-shadow",
            event_type="decision_recorded",
            occurred_at="2026-08-19T14:35:01+00:00",
            actor_type="system",
            subject_ref="requirement-set:hydrotester",
            result_class="blocked",
            parent_event_id="event:evidence",
            evidence_refs=(evidence.source_ref,),
            correlation_refs=("github:pr2",),
            tags=("final_request_not_ready",),
        ),
        AuditEvent(
            event_id="event:eval",
            trace_id="trace:hydrotester-shadow",
            event_type="evaluation_completed",
            occurred_at="2026-08-19T14:35:02+00:00",
            actor_type="system",
            subject_ref="eval-suite:audit-shadow",
            result_class="passed",
            parent_event_id="event:readiness",
            evidence_refs=("github:pr2", "github:pr4"),
            correlation_refs=("github:pr6",),
        ),
        AuditEvent(
            event_id="event:promotion",
            trace_id="trace:hydrotester-shadow",
            event_type="promotion_decided",
            occurred_at="2026-08-19T14:35:03+00:00",
            actor_type="system",
            subject_ref="promotion-run:audit-shadow",
            result_class="accepted",
            parent_event_id="event:eval",
            correlation_refs=("github:pr6", "github:pr10"),
        ),
        AuditEvent(
            event_id="event:gate",
            trace_id="trace:hydrotester-shadow",
            event_type="human_gate_evaluated",
            occurred_at="2026-08-19T14:35:04+00:00",
            actor_type="system",
            subject_ref="action:send:hydrotester-final-rfq:shadow",
            result_class="blocked",
            privacy_mode="sensitive_omitted",
            parent_event_id="event:promotion",
            action_ref=intent.action_id,
            correlation_refs=("github:pr4",),
            tags=("mismatched_approval",),
        ),
    )

    validation = validate_audit_trace(events)
    assert validation.valid is True
    assert validation.errors == ()

    assert events[-2].result_class == "accepted"
    assert events[-1].result_class == "blocked"
    assert events[-1].action_ref == intent.action_id
    assert all(not hasattr(event, "payload") for event in events)


def test_integration_rejects_covert_payload_in_metadata_reference():
    event = AuditEvent(
        event_id="event:privacy-regression",
        trace_id="trace:hydrotester-shadow",
        event_type="evidence_observed",
        occurred_at="2026-08-19T14:35:00+00:00",
        actor_type="external_source",
        subject_ref="gmail:message:1a018c1b2c80c8e3",
        result_class="observed",
        evidence_refs=(
            "gmail:message:1a018c1b2c80c8e3\nthis must never become an embedded email body",
        ),
    )
    validation = validate_audit_trace((event,))
    assert validation.valid is False
    assert any(
        "evidence_refs cannot contain control or formatting characters" in error
        for error in validation.errors
    )
