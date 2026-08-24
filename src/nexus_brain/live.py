from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable
import unicodedata

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


def _compact_text(name: str, value, *, max_len: int = 512) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > max_len:
        raise ValueError(f"invalid {name}")
    if any(unicodedata.category(ch) in {"Cc", "Cf", "Zl", "Zp"} for ch in value):
        raise ValueError(f"invalid {name}")
    return value


def _validate_signal(graph: BrainGraph, signal) -> LiveEvidenceSignal:
    if not isinstance(signal, LiveEvidenceSignal):
        raise ValueError("live evidence signal must be LiveEvidenceSignal")
    _compact_text("id", signal.id, max_len=256)
    _compact_text("project_id", signal.project_id, max_len=128)
    _compact_text("source_ref", signal.source_ref, max_len=512)
    _compact_text("label", signal.label, max_len=512)
    _compact_text("topic", signal.topic, max_len=128)
    _compact_text("summary", signal.summary, max_len=2000)
    if type(signal.action_required) is not bool:
        raise ValueError("action_required must be boolean")
    try:
        observed = datetime.fromisoformat(signal.observed_at.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError("observed_at must be ISO-8601") from exc
    if observed.tzinfo is None or observed.utcoffset() is None:
        raise ValueError("observed_at must be timezone-aware")
    known_projects = {node.project_id for node in graph.nodes.values() if node.project_id}
    if signal.project_id not in known_projects:
        raise ValueError("live evidence references unknown project")
    if signal.id in graph.nodes:
        raise ValueError(f"duplicate live evidence id: {signal.id}")
    return signal


def apply_live_evidence_signals(graph: BrainGraph, signals: Iterable[LiveEvidenceSignal]) -> BrainGraph:
    """Add connector-retrieved live communication evidence without authority promotion.

    A live email is a fact that a communication occurred. Its embedded commercial or
    technical assertions remain evidence/claims unless separately verified. Governing
    requirements and blocking unknowns are left untouched.
    """
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable of LiveEvidenceSignal objects")
    try:
        iterator = iter(signals)
    except TypeError as exc:
        raise ValueError("signals must be iterable") from exc
    for raw in iterator:
        signal = _validate_signal(graph, raw)
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
