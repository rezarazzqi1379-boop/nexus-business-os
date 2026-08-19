from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class EpistemicState(str, Enum):
    FACT = "fact"
    CLAIM = "claim"
    ESTIMATE = "estimate"
    HYPOTHESIS = "hypothesis"
    UNKNOWN = "unknown"


class NodeKind(str, Enum):
    COMPANY = "company"
    PERSON = "person"
    PROJECT = "project"
    PAPER = "paper"
    RESEARCHER = "researcher"
    DATASET = "dataset"
    THEORY = "theory"
    TECHNOLOGY = "technology"
    TOOL = "tool"
    IDEA = "idea"
    EXPERIMENT = "experiment"
    FINDING = "finding"
    SIGNAL = "signal"
    OPPORTUNITY = "opportunity"
    OUTCOME = "outcome"


class PromotionTarget(str, Enum):
    EXPLORATION = "exploration"
    EXPERIMENT = "experiment"
    DECISION_SUPPORT = "decision_support"


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    kind: NodeKind
    label: str
    epistemic_state: EpistemicState
    source_refs: tuple[str, ...]
    project_refs: tuple[str, ...] = ()
    confidence: float | None = None


@dataclass(frozen=True)
class GraphEdge:
    edge_id: str
    source_node_id: str
    target_node_id: str
    relation: str
    source_refs: tuple[str, ...]
    epistemic_state: EpistemicState


@dataclass(frozen=True)
class PromotionDecision:
    target: PromotionTarget
    allowed: bool
    reasons: tuple[str, ...]


def _non_empty_unique(values: Iterable[str]) -> bool:
    items = tuple(values)
    return bool(items) and all(isinstance(v, str) and v.strip() for v in items) and len(items) == len(set(items))


def validate_node(node: GraphNode) -> tuple[str, ...]:
    """Validate raw graph data without requiring it to be production-grade.

    Exploration is intentionally permissive, but identity, provenance and numeric
    confidence must still be structurally valid so later promotion is auditable.
    """
    errors: list[str] = []
    if not isinstance(node.node_id, str) or not node.node_id.strip():
        errors.append("invalid_node_id")
    if not isinstance(node.label, str) or not node.label.strip():
        errors.append("invalid_label")
    if not _non_empty_unique(node.source_refs):
        errors.append("invalid_source_refs")
    if len(node.project_refs) != len(set(node.project_refs)):
        errors.append("duplicate_project_refs")
    if node.confidence is not None and not (0.0 <= node.confidence <= 1.0):
        errors.append("invalid_confidence")
    return tuple(errors)


def validate_edge(edge: GraphEdge, *, known_node_ids: set[str]) -> tuple[str, ...]:
    errors: list[str] = []
    if not edge.edge_id.strip():
        errors.append("invalid_edge_id")
    if edge.source_node_id not in known_node_ids or edge.target_node_id not in known_node_ids:
        errors.append("unknown_edge_endpoint")
    if edge.source_node_id == edge.target_node_id:
        errors.append("self_edge")
    if not edge.relation.strip():
        errors.append("invalid_relation")
    if not _non_empty_unique(edge.source_refs):
        errors.append("invalid_source_refs")
    return tuple(errors)


def decide_promotion(node: GraphNode, *, target: PromotionTarget) -> PromotionDecision:
    """Promote broad exploration only when evidence is strong enough for the target.

    The graph is allowed to be noisy. The decision layer is not. This keeps weak
    signals useful for ideation while preventing them from silently becoming facts.
    """
    reasons = list(validate_node(node))
    if reasons:
        return PromotionDecision(target=target, allowed=False, reasons=tuple(reasons))

    if target is PromotionTarget.EXPLORATION:
        return PromotionDecision(target=target, allowed=True, reasons=())

    if target is PromotionTarget.EXPERIMENT:
        if node.epistemic_state not in {
            EpistemicState.CLAIM,
            EpistemicState.ESTIMATE,
            EpistemicState.HYPOTHESIS,
            EpistemicState.FACT,
        }:
            reasons.append("insufficient_epistemic_state_for_experiment")
        if not node.project_refs:
            reasons.append("missing_project_linkage")
        return PromotionDecision(target=target, allowed=not reasons, reasons=tuple(reasons))

    if node.epistemic_state is not EpistemicState.FACT:
        reasons.append("decision_support_requires_fact")
    if not node.project_refs:
        reasons.append("missing_project_linkage")
    if node.confidence is None or node.confidence < 0.8:
        reasons.append("insufficient_confidence")
    if len(node.source_refs) < 1:
        reasons.append("missing_provenance")
    return PromotionDecision(target=target, allowed=not reasons, reasons=tuple(reasons))
