from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable

from .command import InternalActionRecommendation, recommend_internal_actions
from .graph import BrainGraph
from .model import AuthorityTier, EpistemicStatus, Node, NodeType


@dataclass(frozen=True)
class ShadowTaskIntent:
    task_id: str
    project_id: str
    source_node_id: str
    action: str
    priority_class: str
    action_digest: str
    external_effect: bool = False


@dataclass(frozen=True)
class ShadowTaskResult:
    task_id: str
    project_id: str
    source_node_id: str
    status: str
    summary: str
    evidence_refs: tuple[str, ...] = ()


def _digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_shadow_intents(graph: BrainGraph) -> tuple[ShadowTaskIntent, ...]:
    """Convert current Brain recommendations into immutable read-only shadow intents.

    The contract is deliberately execution-engine neutral so PLO can consume it after
    branch consolidation. It never grants external-effect authority.
    """
    intents: list[ShadowTaskIntent] = []
    for rec in recommend_internal_actions(graph):
        if rec.external_execution_allowed:
            raise ValueError("shadow loop cannot consume an externally executable recommendation")
        payload = {
            "project_id": rec.project_id,
            "source_node_id": rec.source_node_id,
            "action": rec.action,
            "priority_class": rec.priority_class,
            "external_effect": False,
        }
        digest = _digest(payload)
        intents.append(
            ShadowTaskIntent(
                task_id=f"shadow:{rec.project_id}:{rec.source_node_id}:{digest[:12]}",
                project_id=rec.project_id,
                source_node_id=rec.source_node_id,
                action=rec.action,
                priority_class=rec.priority_class,
                action_digest=digest,
            )
        )
    return tuple(intents)


def apply_shadow_results(graph: BrainGraph, results: Iterable[ShadowTaskResult]) -> BrainGraph:
    """Record execution outcomes as operational evidence without clearing blockers.

    A completed research/normalization task is proof that the task ran, not proof that
    its findings are canonical. Results therefore enter as Tier C OUTCOME nodes.
    """
    if isinstance(results, (str, bytes)):
        raise ValueError("results must be ShadowTaskResult objects")
    for result in results:
        if not isinstance(result, ShadowTaskResult):
            raise ValueError("result must be ShadowTaskResult")
        if result.status not in {"completed", "blocked", "failed"}:
            raise ValueError("unsupported shadow result status")
        if result.project_id not in {n.project_id for n in graph.nodes.values() if n.project_id}:
            raise ValueError("shadow result references unknown project")
        if result.source_node_id not in graph.nodes:
            raise ValueError("shadow result references unknown source node")
        node_id = f"OUTCOME-{_digest({'task_id': result.task_id, 'project_id': result.project_id})[:20]}"
        if node_id in graph.nodes:
            raise ValueError("duplicate shadow result")
        graph.add_node(
            Node(
                id=node_id,
                type=NodeType.OUTCOME,
                label=f"Shadow task {result.status}: {result.task_id}",
                project_id=result.project_id,
                authority_tier=AuthorityTier.C,
                epistemic_status=EpistemicStatus.FACT,
                source_refs=result.evidence_refs,
                attributes={
                    "task_id": result.task_id,
                    "source_node_id": result.source_node_id,
                    "status": result.status,
                    "summary": result.summary,
                    "shadow_only": True,
                    "external_effect": False,
                },
            )
        )
    return graph
