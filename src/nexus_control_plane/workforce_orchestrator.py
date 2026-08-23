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


def compile_workflow(kind: WorkflowKind, available_inputs: Iterable[str]) -> WorkflowPlan:
    if not isinstance(kind, WorkflowKind):
        raise ValueError("kind must be WorkflowKind")
    available = {item for item in available_inputs if isinstance(item, str) and item.strip() == item and item}
    steps = validate_template(WORKFLOW_TEMPLATES[kind])
    capability_index = _capability_index()

    planned: list[PlannedStep] = []
    completed: set[str] = set()
    for step in steps:
        capability = capability_index[step.capability_id]
        missing_inputs = tuple(name for name in step.required_inputs if name not in available)
        dependency_blocked = any(dep not in completed for dep in step.depends_on)

        if missing_inputs or dependency_blocked:
            disposition = StepDisposition.BLOCKED
        elif capability.requires_human_approval or capability.action_class in {
            ActionClass.EXTERNAL_WRITE,
            ActionClass.FINANCIAL,
        }:
            disposition = StepDisposition.HUMAN_GATE
            completed.add(step.step_id)
        else:
            disposition = StepDisposition.RUNNABLE
            completed.add(step.step_id)

        planned.append(
            PlannedStep(
                step=step,
                capability=capability,
                disposition=disposition,
                missing_inputs=missing_inputs,
            )
        )

    return WorkflowPlan(kind=kind, steps=tuple(planned))


def next_actionable_steps(plan: WorkflowPlan) -> tuple[PlannedStep, ...]:
    """Return the first currently actionable frontier; never skip a blocked predecessor."""
    frontier: list[PlannedStep] = []
    for step in plan.steps:
        if step.disposition is StepDisposition.BLOCKED:
            break
        frontier.append(step)
        if step.disposition is StepDisposition.HUMAN_GATE:
            break
    return tuple(frontier)
