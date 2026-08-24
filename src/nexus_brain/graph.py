from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .model import AuthorityTier, Edge, EpistemicStatus, Node, NodeType


AUTHORITY_RANK = {
    AuthorityTier.A: 4,
    AuthorityTier.B: 3,
    AuthorityTier.C: 2,
    AuthorityTier.D: 1,
}

CONSEQUENTIAL_RELATIONS = {
    "qualifies",
    "authorizes",
    "governs",
    "selects",
    "commits",
}


@dataclass(frozen=True)
class Contradiction:
    subject_id: str
    predicate: str
    node_ids: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class DecisionContext:
    project_id: str
    facts: tuple[Node, ...]
    claims: tuple[Node, ...]
    unknowns: tuple[Node, ...]
    contradictions: tuple[Contradiction, ...]
    consequential_use_allowed: bool
    blockers: tuple[str, ...]


class BrainGraph:
    """Small, fail-closed governed graph for NEXUS vertical slices.

    This is deliberately not a generic graph database. It enforces the NEXUS
    authority and provenance rules before graph records may support a decision.
    """

    def __init__(self, nodes: Iterable[Node] = (), edges: Iterable[Edge] = ()):
        self.nodes: dict[str, Node] = {}
        self.edges: dict[str, Edge] = {}
        for node in nodes:
            self.add_node(node)
        for edge in edges:
            self.add_edge(edge)

    def add_node(self, node: Node) -> None:
        if node.id in self.nodes:
            raise ValueError(f"duplicate node id: {node.id}")
        if node.authority_tier in {AuthorityTier.A, AuthorityTier.B} and not node.source_refs:
            raise ValueError(f"authoritative/evidence node requires source_refs: {node.id}")
        if node.epistemic_status is EpistemicStatus.FACT and not node.source_refs:
            raise ValueError(f"fact requires provenance: {node.id}")
        if node.superseded_by == node.id:
            raise ValueError("node cannot supersede itself")
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        if edge.id in self.edges:
            raise ValueError(f"duplicate edge id: {edge.id}")
        if edge.from_id not in self.nodes or edge.to_id not in self.nodes:
            raise ValueError(f"edge references missing node: {edge.id}")
        if edge.relation in CONSEQUENTIAL_RELATIONS and not edge.source_refs:
            raise ValueError(f"consequential edge requires provenance: {edge.id}")
        self.edges[edge.id] = edge

    def project_nodes(self, project_id: str) -> tuple[Node, ...]:
        return tuple(node for node in self.nodes.values() if node.project_id == project_id)

    def neighbors(self, node_id: str, relation: str | None = None) -> tuple[Node, ...]:
        result: list[Node] = []
        for edge in self.edges.values():
            if relation is not None and edge.relation != relation:
                continue
            if edge.from_id == node_id:
                result.append(self.nodes[edge.to_id])
            elif edge.to_id == node_id:
                result.append(self.nodes[edge.from_id])
        return tuple(result)

    def _active(self, node: Node) -> bool:
        return (
            node.epistemic_status not in {EpistemicStatus.STALE, EpistemicStatus.SUPERSEDED}
            and node.superseded_by is None
        )

    def detect_value_contradictions(self, project_id: str) -> tuple[Contradiction, ...]:
        """Detect conflicting active values sharing a normalized subject/predicate.

        Nodes opt in using attributes: subject, predicate, value. This avoids
        pretending arbitrary natural language equality can be resolved safely.
        """
        buckets: dict[tuple[str, str], list[Node]] = {}
        for node in self.project_nodes(project_id):
            if not self._active(node):
                continue
            subject = node.attributes.get("subject")
            predicate = node.attributes.get("predicate")
            if subject is None or predicate is None or "value" not in node.attributes:
                continue
            buckets.setdefault((str(subject), str(predicate)), []).append(node)

        contradictions: list[Contradiction] = []
        for (subject, predicate), nodes in buckets.items():
            values = {repr(node.attributes.get("value")) for node in nodes}
            if len(values) <= 1:
                continue
            highest = max(AUTHORITY_RANK[node.authority_tier] for node in nodes)
            highest_nodes = [node for node in nodes if AUTHORITY_RANK[node.authority_tier] == highest]
            highest_values = {repr(node.attributes.get("value")) for node in highest_nodes}
            reason = (
                "same-authority conflict requires explicit resolution"
                if len(highest_values) > 1
                else "lower-authority evidence conflicts with governing value"
            )
            contradictions.append(
                Contradiction(
                    subject_id=subject,
                    predicate=predicate,
                    node_ids=tuple(node.id for node in nodes),
                    reason=reason,
                )
            )
        return tuple(contradictions)

    def decision_context(self, project_id: str) -> DecisionContext:
        project_nodes = tuple(node for node in self.project_nodes(project_id) if self._active(node))
        facts = tuple(node for node in project_nodes if node.epistemic_status is EpistemicStatus.FACT)
        claims = tuple(
            node
            for node in project_nodes
            if node.epistemic_status
            in {
                EpistemicStatus.CLAIM,
                EpistemicStatus.ESTIMATE,
                EpistemicStatus.INFERENCE,
                EpistemicStatus.HYPOTHESIS,
                EpistemicStatus.ASSUMPTION,
            }
        )
        unknowns = tuple(node for node in project_nodes if node.epistemic_status is EpistemicStatus.UNKNOWN)
        contradictions = self.detect_value_contradictions(project_id)

        blockers: list[str] = []
        if contradictions:
            blockers.append("unresolved_contradiction")
        if any(node.attributes.get("blocking") is True for node in unknowns):
            blockers.append("blocking_unknown")
        if any(
            node.type is NodeType.REQUIREMENT
            and node.authority_tier is not AuthorityTier.A
            and node.attributes.get("governing") is True
            for node in project_nodes
        ):
            blockers.append("governing_requirement_without_tier_a_authority")

        return DecisionContext(
            project_id=project_id,
            facts=facts,
            claims=claims,
            unknowns=unknowns,
            contradictions=contradictions,
            consequential_use_allowed=not blockers,
            blockers=tuple(blockers),
        )

    def trace_provenance(self, node_id: str) -> tuple[str, ...]:
        """Return direct provenance references plus evidence nodes linked to a node."""
        if node_id not in self.nodes:
            raise KeyError(node_id)
        refs = set(self.nodes[node_id].source_refs)
        for edge in self.edges.values():
            if edge.from_id == node_id and edge.relation in {"supported_by", "derived_from"}:
                evidence = self.nodes[edge.to_id]
                refs.update(evidence.source_refs)
            if edge.to_id == node_id and edge.relation == "supports":
                evidence = self.nodes[edge.from_id]
                refs.update(evidence.source_refs)
        return tuple(sorted(refs))
