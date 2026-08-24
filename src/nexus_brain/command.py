from __future__ import annotations

from dataclasses import dataclass

from .graph import BrainGraph
from .live import action_required_signals


@dataclass(frozen=True)
class InternalActionRecommendation:
    project_id: str
    source_node_id: str
    action: str
    priority_class: str
    rationale: str
    external_execution_allowed: bool = False


def recommend_internal_actions(graph: BrainGraph) -> tuple[InternalActionRecommendation, ...]:
    """Derive conservative internal next actions from live evidence.

    This is intentionally deterministic and non-probabilistic. It recommends internal
    verification/normalization work only; it never authorizes sending or committing externally.
    """
    recommendations: list[InternalActionRecommendation] = []
    for signal in action_required_signals(graph):
        topic = signal.attributes.get("topic")
        if topic == "permit":
            action = "verify_permit_authority_and_current_buyer_status"
            priority = "P0_EVIDENCE_BLOCKER"
            rationale = "A live counterparty reply requests permit proof while current NEXUS state still marks permit applicability/status unresolved."
        elif topic == "supplier_reply":
            action = "normalize_supplier_reply_against_canonical_qualification_matrix"
            priority = "P0_NEW_PRIMARY_EVIDENCE"
            rationale = "New supplier evidence may close or expose decision-critical gaps, but must be tested against the governing project matrix before any selection or reply."
        else:
            action = "inspect_live_evidence_and_resolve_next_internal_step"
            priority = "P1_REVIEW"
            rationale = "Live evidence is marked action-required but has no specialized deterministic rule yet."
        recommendations.append(
            InternalActionRecommendation(
                project_id=signal.project_id or "UNSCOPED",
                source_node_id=signal.id,
                action=action,
                priority_class=priority,
                rationale=rationale,
            )
        )
    return tuple(recommendations)
