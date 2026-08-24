from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .graph import BrainGraph
from .model import AuthorityTier, EpistemicStatus, Node, NodeType


@dataclass(frozen=True)
class LiveEvidenceSignal:
    id: str
    project_id: str
    observed_at: str
    source_ref: str
    label: str
    topic: str
    summary: str
    action_required: bool = False


def apply_live_evidence_signals(graph: BrainGraph, signals: Iterable[LiveEvidenceSignal]) -> BrainGraph:
    """Add connector-retrieved live communication evidence to a graph, read-only in effect.

    A live email is a fact that a communication occurred. Its underlying commercial or
    technical assertions are not silently promoted to facts. This adapter therefore adds
    Communication nodes at Tier B and leaves governing requirements untouched.
    """
    for signal in signals:
        if not signal.source_ref:
            raise ValueError("live evidence requires a retrievable source_ref")
        if signal.id in graph.nodes:
            raise ValueError(f"duplicate live evidence id: {signal.id}")
        graph.add_node(
            Node(
                id=signal.id,
                type=NodeType.COMMUNICATION,
                label=signal.label,
                project_id=signal.project_id,
                authority_tier=AuthorityTier.B,
                epistemic_status=EpistemicStatus.FACT,
                source_refs=(signal.source_ref,),
                observed_at=signal.observed_at,
                attributes={
                    "topic": signal.topic,
                    "summary": signal.summary,
                    "action_required": signal.action_required,
                    "live_evidence": True,
                },
            )
        )
    return graph


def action_required_signals(graph: BrainGraph, project_id: str | None = None) -> tuple[Node, ...]:
    result = []
    for node in graph.nodes.values():
        if node.type is not NodeType.COMMUNICATION:
            continue
        if project_id is not None and node.project_id != project_id:
            continue
        if node.attributes.get("action_required") is True:
            result.append(node)
    return tuple(result)
