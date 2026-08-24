from __future__ import annotations

from dataclasses import dataclass

from meta_agent import Capability, Evidence, EvidenceKind, MetaAgent, Objective, Risk
from need_radar import NeedAssessment, NeedSignal, assess_need


@dataclass(frozen=True)
class MetaLeadResult:
    assessment: NeedAssessment
    selected_tools: tuple[str, ...]
    blocked_capabilities: tuple[str, ...]
    evidence_digest: str
    outreach_authorized: bool


def _required_capabilities(assessment: NeedAssessment) -> tuple[Capability, ...]:
    if assessment.disposition == "manual_review":
        return (Capability.RETRIEVAL, Capability.VERIFICATION)
    if assessment.disposition == "verify":
        return (Capability.RESEARCH, Capability.VERIFICATION)
    if assessment.disposition in {"priority_research", "research", "supply_research"}:
        return (Capability.RESEARCH, Capability.VERIFICATION, Capability.PLANNING)
    return (Capability.RETRIEVAL,)


def evaluate_lead_with_meta_agent(signal: NeedSignal, agent: MetaAgent) -> MetaLeadResult:
    """Preserve v1 classification, then add a read-only capability plan.

    This adapter cannot upgrade a lead disposition and cannot authorize outreach.
    """
    assessment = assess_need(signal)
    evidence = []
    for item in signal.evidence:
        kind = EvidenceKind.FACT if item.classification == "FACT" else EvidenceKind.CLAIM
        evidence.append(
            Evidence(
                evidence_id=f"{signal.signal_id}:{item.evidence_id}",
                project_id=signal.project_id,
                statement=item.statement,
                kind=kind,
                source=item.source_ref if kind is EvidenceKind.FACT else None,
                confidence=0.95 if kind is EvidenceKind.FACT else 0.50,
            )
        )
    agent.remember(evidence)
    required = _required_capabilities(assessment) + (Capability.EXTERNAL_ACTION,)
    plan = agent.plan(
        Objective(
            objective_id=f"lead-eval:{signal.signal_id}",
            project_id=signal.project_id,
            description=f"Evaluate {signal.company_name} without outreach",
            required=required,
            max_risk=Risk.READ,
            acceptance_criteria=("classification parity", "primary evidence", "no outreach"),
        )
    )
    return MetaLeadResult(
        assessment=assessment,
        selected_tools=tuple(step.tool_id for step in plan.steps),
        blocked_capabilities=tuple(item.value for item in plan.blocked),
        evidence_digest=plan.evidence_digest,
        outreach_authorized=False,
    )
