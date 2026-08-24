"""Create a PR #19-compatible improvement proposal from real procurement friction.

The proposal is evidence-backed and evaluation-only. It does not block or send any
RFQ by itself; that behavior must be tested as a candidate against the current
baseline before any promotion is considered.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .procurement_friction import ProcurementFrictionPattern


@dataclass(frozen=True)
class PreRfqReadinessProposal:
    proposal_id: str
    component: str
    hypothesis: str
    change_summary: str
    source_observations: tuple[str, ...]
    expected_metric: str
    max_regression: float
    evidence_refs: tuple[str, ...]

    def as_pr19_payload(self) -> Mapping[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "component": self.component,
            "hypothesis": self.hypothesis,
            "change_summary": self.change_summary,
            "source_observations": self.source_observations,
            "expected_metric": self.expected_metric,
            "max_regression": self.max_regression,
        }


def proposal_from_friction_pattern(
    pattern: ProcurementFrictionPattern,
    *,
    proposal_id: str = "evolution:pre-rfq-readiness-gate:v0.1",
) -> PreRfqReadinessProposal:
    if not isinstance(pattern, ProcurementFrictionPattern):
        raise ValueError("pattern must be ProcurementFrictionPattern")
    if not pattern.eligible_for_improvement_proposal:
        raise ValueError("friction pattern is not eligible for an improvement proposal")
    if not pattern.event_ids or not pattern.source_refs:
        raise ValueError("eligible friction pattern must retain evidence")

    return PreRfqReadinessProposal(
        proposal_id=proposal_id,
        component="procurement_pre_rfq_gate",
        hypothesis=(
            "A bounded pre-RFQ readiness gate that checks decision-critical technical boundaries, "
            "requested equipment/supply scope, and regulatory/commercial prerequisites before outreach "
            "will reduce clarification loops without materially suppressing valid supplier outreach."
        ),
        change_summary=(
            "Evaluate a candidate pre-RFQ readiness gate. Before external RFQ outreach, classify unresolved "
            "items as technical-boundary, scope-boundary, or regulatory/commercial prerequisite. Decision-critical "
            "unknowns trigger RESEARCH/HOLD; non-critical unknowns remain explicitly disclosed. The candidate must "
            "be evaluated against the frozen current workflow and may not auto-send, auto-block production, or change permissions."
        ),
        source_observations=pattern.event_ids,
        expected_metric="post_outreach_clarification_rework_rate",
        max_regression=0.05,
        evidence_refs=pattern.source_refs,
    )
