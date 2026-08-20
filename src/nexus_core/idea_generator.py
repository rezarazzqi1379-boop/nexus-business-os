from __future__ import annotations

from dataclasses import dataclass

from .contradictions import Contradiction
from .knowledge_graph import EpistemicState, GraphNode, NodeKind


@dataclass(frozen=True)
class IdeaCandidate:
    idea_id: str
    title: str
    hypothesis: str
    source_refs: tuple[str, ...]
    project_refs: tuple[str, ...]
    reason: str


def generate_gap_ideas(
    *,
    nodes: tuple[GraphNode, ...],
    contradictions: tuple[Contradiction, ...],
) -> tuple[IdeaCandidate, ...]:
    """Generate auditable hypotheses from graph gaps, not free-form inspiration.

    This is intentionally deterministic. LLM ideation can later enrich candidates,
    but the base system should always be able to explain which graph condition
    produced an idea and which evidence must be revisited to test it.
    """
    ideas: list[IdeaCandidate] = []

    for contradiction in contradictions:
        source_refs: set[str] = set()
        project_refs: set[str] = set()
        for node in nodes:
            if node.node_id == contradiction.subject_ref:
                source_refs.update(node.source_refs)
                project_refs.update(node.project_refs)
        ideas.append(
            IdeaCandidate(
                idea_id=f"idea:resolve:{contradiction.subject_ref}:{contradiction.predicate}",
                title=f"Resolve conflicting evidence for {contradiction.predicate}",
                hypothesis=(
                    f"One or more sources for {contradiction.subject_ref} may be stale, "
                    f"scoped differently, or incorrect for {contradiction.predicate}."
                ),
                source_refs=tuple(sorted(source_refs)),
                project_refs=tuple(sorted(project_refs)),
                reason="direct_contradiction",
            )
        )

    for node in sorted(nodes, key=lambda item: item.node_id):
        if node.kind not in {NodeKind.SIGNAL, NodeKind.OPPORTUNITY, NodeKind.IDEA}:
            continue
        if node.epistemic_state not in {EpistemicState.HYPOTHESIS, EpistemicState.UNKNOWN, EpistemicState.CLAIM}:
            continue
        if not node.project_refs:
            continue
        if node.confidence is not None and node.confidence >= 0.8:
            continue
        ideas.append(
            IdeaCandidate(
                idea_id=f"idea:verify:{node.node_id}",
                title=f"Test low-confidence {node.kind.value}: {node.label}",
                hypothesis=f"Additional evidence could promote or falsify {node.node_id}.",
                source_refs=node.source_refs,
                project_refs=node.project_refs,
                reason="low_confidence_project_linked_node",
            )
        )

    deduped: dict[str, IdeaCandidate] = {}
    for idea in ideas:
        deduped.setdefault(idea.idea_id, idea)
    return tuple(deduped[key] for key in sorted(deduped))
