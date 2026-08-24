from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .command import recommend_internal_actions
from .fixtures import canonical_portfolio_graph
from .live import LiveEvidenceSignal, apply_live_evidence_signals
from .projection import portfolio_projection


def load_manual_snapshot(path: str | Path) -> list[LiveEvidenceSignal]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("snapshot_mode") != "MANUAL_CONNECTOR_READ_ONLY":
        raise ValueError("unsupported snapshot mode")
    if payload.get("continuous_sync") is not False:
        raise ValueError("manual snapshot must not claim continuous sync")
    signals = payload.get("signals")
    if not isinstance(signals, list):
        raise ValueError("snapshot signals must be a list")
    return [LiveEvidenceSignal(**item) for item in signals]


def live_command_projection(path: str | Path) -> dict[str, Any]:
    """Build the current read-only command projection from canonical fixtures + live evidence.

    This remains an internal projection. It grants no external action authority.
    """
    graph = canonical_portfolio_graph()
    apply_live_evidence_signals(graph, load_manual_snapshot(path))
    portfolio = portfolio_projection(graph)
    actions = recommend_internal_actions(graph)

    by_project: dict[str, list[dict[str, Any]]] = {}
    for action in actions:
        by_project.setdefault(action.project_id, []).append({
            "source_node_id": action.source_node_id,
            "action": action.action,
            "priority_class": action.priority_class,
            "rationale": action.rationale,
            "external_execution_allowed": action.external_execution_allowed,
        })

    for project in portfolio["projects"]:
        pid = project["project_id"]
        communications = [
            {
                "id": n.id,
                "label": n.label,
                "observed_at": n.observed_at,
                "source_refs": list(n.source_refs),
                "topic": n.attributes.get("topic"),
                "summary": n.attributes.get("summary"),
                "action_required": n.attributes.get("action_required") is True,
            }
            for n in graph.project_nodes(pid)
            if n.type.value == "communication" and n.attributes.get("live_evidence") is True
        ]
        project["live_communications"] = sorted(communications, key=lambda x: x["observed_at"] or "", reverse=True)
        project["recommended_internal_actions"] = by_project.get(pid, [])
        project["counts"]["live_communications"] = len(communications)
        project["counts"]["recommended_internal_actions"] = len(by_project.get(pid, []))

    portfolio["action_required_count"] = sum(len(v) for v in by_project.values())
    portfolio["external_execution_allowed"] = False
    return portfolio
