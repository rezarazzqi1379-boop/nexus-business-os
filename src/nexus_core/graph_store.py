from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .knowledge_graph import GraphEdge, GraphNode, validate_edge, validate_node


class GraphRepository(Protocol):
    """Storage boundary for the exploration graph.

    The core graph logic must not depend on Supabase/Postgres directly. Keeping a
    narrow repository contract lets NEXUS test graph behaviour in memory now and
    attach a durable backend later without changing promotion/decision logic.
    """

    def put_node(self, node: GraphNode) -> None: ...
    def put_edge(self, edge: GraphEdge) -> None: ...
    def get_node(self, node_id: str) -> GraphNode | None: ...
    def list_nodes(self) -> tuple[GraphNode, ...]: ...
    def list_edges(self) -> tuple[GraphEdge, ...]: ...


@dataclass
class InMemoryGraphRepository:
    """Deterministic reference implementation used for tests and dry-runs."""

    _nodes: dict[str, GraphNode] = field(default_factory=dict)
    _edges: dict[str, GraphEdge] = field(default_factory=dict)

    def put_node(self, node: GraphNode) -> None:
        errors = validate_node(node)
        if errors:
            raise ValueError(f"invalid_graph_node:{','.join(errors)}")
        existing = self._nodes.get(node.node_id)
        if existing is not None and existing != node:
            # Reusing a stable ID for different content corrupts lineage. Updates
            # should be explicit versioned writes in a durable backend, not silent
            # replacement of an identity key.
            raise ValueError("node_identity_collision")
        self._nodes[node.node_id] = node

    def put_edge(self, edge: GraphEdge) -> None:
        errors = validate_edge(edge, known_node_ids=set(self._nodes))
        if errors:
            raise ValueError(f"invalid_graph_edge:{','.join(errors)}")
        existing = self._edges.get(edge.edge_id)
        if existing is not None and existing != edge:
            raise ValueError("edge_identity_collision")
        self._edges[edge.edge_id] = edge

    def get_node(self, node_id: str) -> GraphNode | None:
        return self._nodes.get(node_id)

    def list_nodes(self) -> tuple[GraphNode, ...]:
        return tuple(self._nodes[key] for key in sorted(self._nodes))

    def list_edges(self) -> tuple[GraphEdge, ...]:
        return tuple(self._edges[key] for key in sorted(self._edges))
