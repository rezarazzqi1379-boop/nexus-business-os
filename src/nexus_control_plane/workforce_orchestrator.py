from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .workforce import ActionClass, CapabilitySpec, catalog


class WorkflowKind(str, Enum):
    PROCUREMENT = "procurement"
    SALES = "sales"
    MARKETING = "marketing"
    SUPPORT = "support"


class StepDisposition(str, Enum):
    RUNNABLE = "runnable"
    HUMAN_GATE = "human_gate"
    BLOCKED = "blocked"
    COMPLETED = "completed"


@dataclass(frozen=True)
class WorkflowStep:
    step_id: str
    capability_id: str
    depends_on: tuple[str, ...] = ()
    required_inputs: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlannedStep:
    step: WorkflowStep
    capability: CapabilitySpec
    disposition: StepDisposition
    missing_inputs: tuple[str, ...]
    unmet_dependencies: tuple[str, ...]


@dataclass(frozen=True)
class WorkflowPlan:
    kind: WorkflowKind
    steps: tuple[PlannedStep, ...]

    @property
    def runnable(self) -> tuple[PlannedStep, ...]:
        return tuple(step for step in self.steps if step.disposition is StepDisposition.RUNNABLE)

    @property
    def human_gate(self) -> tuple[PlannedStep, ...]:
        return tuple(step for step in self.steps if step.disposition is StepDisposition.HUMAN_GATE)

    @property
    def blocked(self) -> tuple[PlannedStep, ...]:
        return tuple(step for step in self.steps if step.disposition is StepDisposition.BLOCKED)

    @property
    def completed(self) -> tuple[PlannedStep, ...]:
        return tuple(step for step in self.steps if step.disposition is StepDisposition.COMPLETED)


WORKFLOW_TEMPLATES: dict[WorkflowKind, tuple[WorkflowStep, ...]] = {
    WorkflowKind.PROCUREMENT: (
        WorkflowStep("discover", "nexus.opportunity_scout", required_inputs=("business_goal",)),
        WorkflowStep("company_research", "intelligence.company_research", ("discover",), ("target_entity",)),
        WorkflowStep("verify_evidence", "nexus.evidence_verifier", ("company_research",), ("evidence_refs",)),
        WorkflowStep("engineering_review", "nexus.engineering_reviewer", ("verify_evidence",), ("buyer_requirements",)),
        WorkflowStep("proposal", "deals.proposal_writer", ("engineering_review",), ("verified_requirements",)),
        WorkflowStep("duplicate_guard", "nexus.duplicate_guard", ("proposal",), ("counterparty_id", "action_fingerprint")),
        WorkflowStep("approve_send", "nexus.approval_gateway", ("duplicate_guard",), ("exact_message", "exact_recipient")),
    ),
    WorkflowKind.SALES: (
        WorkflowStep("lead_sourcing", "sales.lead_sourcing", required_inputs=("ideal_customer_profile",)),
        WorkflowStep("prospect_research", "intelligence.prospect_research", ("lead_sourcing",), ("target_entity",)),
        WorkflowStep("verify_evidence", "nexus.evidence_verifier", ("prospect_research",), ("evidence_refs",)),
        WorkflowStep("outbound_draft", "sales.outbound_writer", ("verify_evidence",), ("verified_context",)),
        WorkflowStep("duplicate_guard", "nexus.duplicate_guard", ("outbound_draft",), ("counterparty_id", "action_fingerprint")),
        WorkflowStep("approve_send", "nexus.approval_gateway", ("duplicate_guard",), ("exact_message", "exact_recipient")),
    ),
    WorkflowKind.MARKETING: (
        WorkflowStep("trend_research", "marketing.trend_analyst", required_inputs=("audience", "topic")),
        WorkflowStep("verify_evidence", "nexus.evidence_verifier", ("trend_research",), ("evidence_refs",)),
        WorkflowStep("hooks", "marketing.hook_writer", ("verify_evidence",), ("verified_context",)),
        WorkflowStep("content", "marketing.content_engine", ("hooks",), ("brand_context",)),
        WorkflowStep("qa", "nexus.qa_evaluator", ("content",), ("draft_asset",)),
    ),
    WorkflowKind.SUPPORT: (
        WorkflowStep("triage", "operations.support_triage", required_inputs=("inbound_message",)),
        WorkflowStep("verify_knowledge", "nexus.evidence_verifier", ("triage",), ("knowledge_refs",)),
        WorkflowStep("answer", "customer.support_answerer", ("verify_knowledge",), ("verified_context",)),
        WorkflowStep("qa", "nexus.qa_evaluator", ("answer",), ("draft_reply",)),
    ),
}


def _capability_index() -> dict[str, CapabilitySpec]:
    return {item.capability_id: item for item in catalog()}


def _canonical_string_set(values: Iterable[str], *, field_name: str) -> set[str]:
    normalized: set[str] = set()
    for value in values:
        if not isinstance(value, str) or not value or value.strip() != value:
            raise ValueError(f"{field_name} must contain canonical non-empty strings")
        normalized.add(value)
    return normalized


def validate_template(steps: Iterable[WorkflowStep]) -> tuple[WorkflowStep, ...]:
    normalized = tuple(steps)
    if not normalized:
        raise ValueError("workflow template must contain at least one step")
    ids = [step.step_id for step in normalized]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate workflow step_id")
    if any(not step.step_id or step.step_id.strip() != step.step_id for step in normalized):
        raise ValueError("workflow step_id must be canonical")

    known_steps: set[str] = set()
    capability_index = _capability_index()
    for step in normalized:
        if step.capability_id not in capability_index:
            raise ValueError(f"unknown capability_id: {step.capability_id}")
        unknown_dependencies = set(step.depends_on) - known_steps
        if unknown_dependencies:
            raise ValueError(f"forward or unknown dependencies: {sorted(unknown_dependencies)}")
        known_steps.add(step.step_id)
    return normalized


def compile_workflow(
    kind: WorkflowKind,
    available_inputs: Iterable[str],
    completed_steps: Iterable[str] = (),
) -> WorkflowPlan:
    """Compile current workflow state without pretending planned predecessors already ran."""
    if not isinstance(kind, WorkflowKind):
        raise ValueError("kind must be WorkflowKind")
    available = _canonical_string_set(available_inputs, field_name="available_inputs")
    completed = _canonical_string_set(completed_steps, field_name="completed_steps")
    steps = validate_template(WORKFLOW_TEMPLATES[kind])
    known_step_ids = {step.step_id for step in steps}
    unknown_completed = completed - known_step_ids
    if unknown_completed:
        raise ValueError(f"completed_steps contains unknown step IDs: {sorted(unknown_completed)}")

    capability_index = _capability_index()
    planned: list[PlannedStep] = []
    for step in steps:
        capability = capability_index[step.capability_id]
        missing_inputs = tuple(name for name in step.required_inputs if name not in available)
        unmet_dependencies = tuple(dep for dep in step.depends_on if dep not in completed)

        if step.step_id in completed:
            if missing_inputs:
                raise ValueError(f"completed step {step.step_id} is missing required inputs")
            if unmet_dependencies:
                raise ValueError(f"completed step {step.step_id} has unmet dependencies")
            disposition = StepDisposition.COMPLETED
        elif missing_inputs or unmet_dependencies:
            disposition = StepDisposition.BLOCKED
        elif capability.requires_human_approval or capability.action_class in {
            ActionClass.EXTERNAL_WRITE,
            ActionClass.FINANCIAL,
        }:
            disposition = StepDisposition.HUMAN_GATE
        else:
            disposition = StepDisposition.RUNNABLE

        planned.append(
            PlannedStep(
                step=step,
                capability=capability,
                disposition=disposition,
                missing_inputs=missing_inputs,
                unmet_dependencies=unmet_dependencies,
            )
        )

    return WorkflowPlan(kind=kind, steps=tuple(planned))


def next_actionable_steps(plan: WorkflowPlan) -> tuple[PlannedStep, ...]:
    """Return only the current runnable/human-gated frontier, never future blocked work."""
    return tuple(
        step
        for step in plan.steps
        if step.disposition in {StepDisposition.RUNNABLE, StepDisposition.HUMAN_GATE}
    )
