import pytest

from nexus_control_plane.workforce_orchestrator import (
    StepDisposition,
    WorkflowKind,
    WorkflowStep,
    compile_workflow,
    next_actionable_steps,
    validate_template,
)


def test_procurement_workflow_fails_closed_when_inputs_are_missing():
    plan = compile_workflow(WorkflowKind.PROCUREMENT, {"business_goal"})
    assert plan.steps[0].disposition is StepDisposition.RUNNABLE
    assert plan.steps[1].disposition is StepDisposition.BLOCKED
    assert plan.steps[1].missing_inputs == ("target_entity",)
    assert plan.steps[-1].disposition is StepDisposition.BLOCKED


def test_procurement_workflow_requires_exact_human_gate_before_send():
    inputs = {
        "business_goal",
        "target_entity",
        "evidence_refs",
        "buyer_requirements",
        "verified_requirements",
        "counterparty_id",
        "action_fingerprint",
        "exact_message",
        "exact_recipient",
    }
    plan = compile_workflow(WorkflowKind.PROCUREMENT, inputs)
    assert not plan.blocked
    assert plan.steps[-1].step.step_id == "approve_send"
    assert plan.steps[-1].disposition is StepDisposition.HUMAN_GATE
    assert len(plan.human_gate) == 1


def test_sales_workflow_cannot_skip_duplicate_guard():
    inputs = {
        "ideal_customer_profile",
        "target_entity",
        "evidence_refs",
        "verified_context",
        "exact_message",
        "exact_recipient",
    }
    plan = compile_workflow(WorkflowKind.SALES, inputs)
    duplicate = next(item for item in plan.steps if item.step.step_id == "duplicate_guard")
    approval = next(item for item in plan.steps if item.step.step_id == "approve_send")
    assert duplicate.disposition is StepDisposition.BLOCKED
    assert approval.disposition is StepDisposition.BLOCKED


def test_marketing_research_to_qa_is_runnable_without_external_publish_authority():
    inputs = {"audience", "topic", "evidence_refs", "verified_context", "brand_context", "draft_asset"}
    plan = compile_workflow(WorkflowKind.MARKETING, inputs)
    assert not plan.blocked
    assert not plan.human_gate
    assert [item.step.step_id for item in plan.runnable] == [
        "trend_research",
        "verify_evidence",
        "hooks",
        "content",
        "qa",
    ]


def test_validate_template_rejects_unknown_capability():
    with pytest.raises(ValueError, match="unknown capability_id"):
        validate_template((WorkflowStep("x", "nonexistent.capability"),))


def test_validate_template_rejects_forward_dependency():
    with pytest.raises(ValueError, match="forward or unknown dependencies"):
        validate_template(
            (
                WorkflowStep("second", "nexus.qa_evaluator", ("first",)),
                WorkflowStep("first", "nexus.evidence_verifier"),
            )
        )


def test_next_actionable_steps_stops_at_first_blocker():
    plan = compile_workflow(WorkflowKind.PROCUREMENT, {"business_goal"})
    frontier = next_actionable_steps(plan)
    assert [item.step.step_id for item in frontier] == ["discover"]
