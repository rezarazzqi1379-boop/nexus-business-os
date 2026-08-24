from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .graph import BrainGraph
from .model import AuthorityTier, EpistemicStatus, NodeType


def project_projection(graph: BrainGraph, project_id: str) -> dict[str, Any]:
    """Return a read-only, JSON-serializable decision projection for one project.

    The projection intentionally exposes blockers, authority and epistemic state.
    It is not an action endpoint and grants no external-write authority.
    """
    context = graph.decision_context(project_id)
    nodes = [node for node in graph.project_nodes(project_id)]

    def encode_node(node):
        return {
            "id": node.id,
            "type": node.type.value,
            "label": node.label,
            "authority_tier": node.authority_tier.value,
            "epistemic_status": node.epistemic_status.value,
            "source_refs": list(node.source_refs),
            "observed_at": node.observed_at,
            "verified_at": node.verified_at,
            "review_at": node.review_at,
            "valid_from": node.valid_from,
            "valid_to": node.valid_to,
            "superseded_by": node.superseded_by,
            "attributes": dict(node.attributes),
            "provenance": list(graph.trace_provenance(node.id)),
        }

    requirements = [
        encode_node(n)
        for n in nodes
        if n.type is NodeType.REQUIREMENT and n.epistemic_status is not EpistemicStatus.SUPERSEDED
    ]
    claims = [encode_node(n) for n in context.claims]
    unknowns = [encode_node(n) for n in context.unknowns]
    facts = [encode_node(n) for n in context.facts]

    return {
        "project_id": project_id,
        "consequential_use_allowed": context.consequential_use_allowed,
        "blockers": list(context.blockers),
        "counts": {
            "nodes": len(nodes),
            "facts": len(facts),
            "claims": len(claims),
            "unknowns": len(unknowns),
            "contradictions": len(context.contradictions),
        },
        "requirements": requirements,
        "facts": facts,
        "claims": claims,
        "unknowns": unknowns,
        "contradictions": [asdict(item) for item in context.contradictions],
    }


def portfolio_projection(graph: BrainGraph) -> dict[str, Any]:
    """Summarize all project IDs currently represented in the graph."""
    project_ids = sorted({node.project_id for node in graph.nodes.values() if node.project_id})
    projects = [project_projection(graph, project_id) for project_id in project_ids]
    return {
        "project_count": len(projects),
        "blocked_project_count": sum(not item["consequential_use_allowed"] for item in projects),
        "projects": projects,
    }
