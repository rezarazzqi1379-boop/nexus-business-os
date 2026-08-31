import pytest

from nexus_control_plane.workforce_orchestrator import (
    StepDisposition,
    WorkflowKind,
    WorkflowStep,
    compile_workflow,
    next_actionable_steps,
    validate_template,
)


def test_procurement_starts_with_only_discovery_runnable():
    plan = compile_workflow(WorkflowKind.PROCUREMENT, {"business_goal"})
    assert [item.step.step_id for item in plan.runnable] == ["discover"]
    assert plan.steps[1].disposition is StepDisposition.BLOCKED
    assert plan.steps[1].unmet_dependencies == ("discover",)


def test_procurement_advances_only_after_actual_completion():
    plan = compile_workflow(
        WorkflowKind.PROCUREMENT,
        {"business_goal", "target_entity"},
        completed_steps={"discover"},
    )
    assert plan.steps[0].disposition is StepDisposition.COMPLETED
    assert [item.step.step_id for item in plan.runnable] == ["company_research"]


def test_procurement_requires_exact_human_gate_only_after_all_predecessors_complete():
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
    completed = {
        "discover",
        "company_research",
        "verify_evidence",
        "engineering_review",
        "proposal",
        "duplicate_guard",
    }
    plan = compile_workflow(WorkflowKind.PROCUREMENT, inputs, completed)
    assert plan.steps[-1].step.step_id == "approve_send"
    assert plan.steps[-1].disposition is StepDisposition.HUMAN_GATE
    assert len(plan.human_gate) == 1
    assert not plan.runnable


def test_sales_workflow_cannot_skip_duplicate_guard():
    inputs = {
        "ideal_customer_profile",
        "target_entity",
        "evidence_refs",
        "verified_context",
        "exact_message",
        "exact_recipient",
    }
    completed = {"lead_sourcing", "prospect_research", "verify_evidence", "outbound_draft"}
    plan = compile_workflow(WorkflowKind.SALES, inputs, completed)
    duplicate = next(item for item in plan.steps if item.step.step_id == "duplicate_guard")
    approval = next(item for item in plan.steps if item.step.step_id == "approve_send")
    assert duplicate.disposition is StepDisposition.BLOCKED
    assert "counterparty_id" in duplicate.missing_inputs
    assert approval.disposition is StepDisposition.BLOCKED


def test_marketing_advances_one_frontier_at_a_time():
    inputs = {"audience", "topic", "evidence_refs", "verified_context", "brand_context", "draft_asset"}
    plan = compile_workflow(WorkflowKind.MARKETING, inputs)
    assert [item.step.step_id for item in next_actionable_steps(plan)] == ["trend_research"]

    plan = compile_workflow(WorkflowKind.MARKETING, inputs, {"trend_research"})
    assert [item.step.step_id for item in next_actionable_steps(plan)] == ["verify_evidence"]


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


def test_unknown_completed_step_fails_closed():
    with pytest.raises(ValueError, match="unknown step IDs"):
        compile_workflow(WorkflowKind.PROCUREMENT, {"business_goal"}, {"invented"})


def test_completed_step_cannot_claim_completion_without_required_inputs():
    with pytest.raises(ValueError, match="missing required inputs"):
        compile_workflow(WorkflowKind.PROCUREMENT, set(), {"discover"})


def test_malformed_input_metadata_fails_closed():
    with pytest.raises(ValueError, match="canonical"):
        compile_workflow(WorkflowKind.PROCUREMENT, {" business_goal"})
