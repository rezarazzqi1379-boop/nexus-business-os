"""Evidence-bound collaboration coaching for the NEXUS owner and agent.

The system observes workflow friction, never personality or health. It stores
derived counters and evidence references, not raw conversation text, and keeps
owner coaching optional while agent adaptations remain testable/reversible.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Literal

from owner_decision_runtime import DecisionOption
from unified_data_environment import EvidenceObservation, UnifiedDataHub

FrictionKind = Literal[
    "REPEATED_INSTRUCTION", "AMBIGUOUS_SCOPE", "MISSING_ACCEPTANCE_TEST",
    "CORRECTION_LOOP", "CONTEXT_OVERLOAD", "DECISION_BOTTLENECK",
]
ObservedSide = Literal["AGENT", "OWNER_WORKFLOW", "SHARED_PROCESS"]

_ALLOWED_KINDS = {
    "REPEATED_INSTRUCTION", "AMBIGUOUS_SCOPE", "MISSING_ACCEPTANCE_TEST",
    "CORRECTION_LOOP", "CONTEXT_OVERLOAD", "DECISION_BOTTLENECK",
}


def _digest(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


@dataclass(frozen=True)
class CollaborationSignal:
    signal_id: str
    project_id: str
    kind: FrictionKind
    observed_side: ObservedSide
    occurrence_count: int
    impact: int
    confidence: float
    evidence_refs: tuple[str, ...]
    observed_at: str

    def validate(self) -> None:
        if not self.signal_id.strip() or not self.project_id.strip():
            raise ValueError("invalid_collaboration_signal")
        if self.kind not in _ALLOWED_KINDS:
            raise ValueError("unsupported_workflow_friction")
        if self.observed_side not in {"AGENT", "OWNER_WORKFLOW", "SHARED_PROCESS"}:
            raise ValueError("invalid_observed_side")
        if self.occurrence_count < 1 or not 1 <= self.impact <= 5:
            raise ValueError("invalid_signal_measurement")
        if not 0 <= self.confidence <= 1:
            raise ValueError("invalid_signal_confidence")
        if not self.evidence_refs or any(not x.strip() for x in self.evidence_refs):
            raise ValueError("signal_evidence_required")


@dataclass(frozen=True)
class GrowthRecommendation:
    recommendation_id: str
    kind: FrictionKind
    agent_adaptation: str
    owner_support: str
    shared_experiment: str
    acceptance_test: str
    evidence_refs: tuple[str, ...]
    priority: float
    owner_action_optional: bool = True
    diagnosis_made: bool = False


@dataclass(frozen=True)
class CollaborationGrowthReport:
    project_id: str
    recommendations: tuple[GrowthRecommendation, ...]
    raw_conversation_stored: bool = False
    sensitive_profile_created: bool = False


_PLAYBOOK = {
    "REPEATED_INSTRUCTION": (
        "Load the project contract and prior evidence summary before acting.",
        "State a standing rule once; the system will carry it forward.",
        "Run three tasks without asking the owner to repeat an existing rule.",
        "No standing constraint is requested again and all are preserved.",
    ),
    "AMBIGUOUS_SCOPE": (
        "Translate the request into a bounded internal contract and preserve unknowns.",
        "Confirm only choices that would materially alter scope or create consequences.",
        "Compare task completion with and without the compact contract.",
        "The delivered result matches the requested outcome without scope expansion.",
    ),
    "MISSING_ACCEPTANCE_TEST": (
        "Infer reversible acceptance checks from project evidence before implementation.",
        "Review the result against outcome-focused checks instead of implementation detail.",
        "Attach at least one measurable check to the next three work requests.",
        "Every completed request has reproducible evidence of completion.",
    ),
    "CORRECTION_LOOP": (
        "Classify each correction and update the smallest relevant contract or test.",
        "Correct the outcome once; the system will retain the generalized lesson.",
        "Replay the corrected workflow on three independent tasks.",
        "Correction rate falls without hiding failures or weakening checks.",
    ),
    "CONTEXT_OVERLOAD": (
        "Load metadata and evidence-linked summaries before raw history.",
        "Keep decisions and constraints explicit; omit repeated narrative where practical.",
        "Measure context used and constraint retention across three tasks.",
        "Context use falls while all constraints and evidence links remain intact.",
    ),
    "DECISION_BOTTLENECK": (
        "Use bounded owner delegation for zero-cost reversible local choices.",
        "Reserve attention for consequential or preference-sensitive decisions.",
        "Auto-select safe local work and queue consequential choices separately.",
        "Safe work advances while every consequential action remains approval-bound.",
    ),
}


def analyze_collaboration(signals: tuple[CollaborationSignal, ...], *, project_id: str,
                          minimum_occurrences: int = 2) -> CollaborationGrowthReport:
    if not project_id.strip() or minimum_occurrences < 2:
        raise ValueError("invalid_growth_scope")
    seen: set[str] = set()
    grouped: dict[str, list[CollaborationSignal]] = {}
    for signal in signals:
        signal.validate()
        if signal.project_id != project_id:
            raise ValueError("cross_project_signal_denied")
        if signal.signal_id in seen:
            raise ValueError("duplicate_signal_id")
        seen.add(signal.signal_id)
        grouped.setdefault(signal.kind, []).append(signal)
    recommendations = []
    for kind, items in grouped.items():
        occurrences = sum(x.occurrence_count for x in items)
        if occurrences < minimum_occurrences:
            continue
        refs = tuple(dict.fromkeys(ref for x in items for ref in x.evidence_refs))
        agent, owner, experiment, acceptance = _PLAYBOOK[kind]
        priority = round(sum(x.impact * x.confidence * x.occurrence_count for x in items) / occurrences, 3)
        recommendations.append(GrowthRecommendation(
            "growth-" + _digest((project_id, kind, refs))[:16], kind, agent, owner,
            experiment, acceptance, refs, priority))
    recommendations.sort(key=lambda x: (-x.priority, x.kind))
    return CollaborationGrowthReport(project_id, tuple(recommendations))


def agent_adaptation_options(report: CollaborationGrowthReport) -> tuple[DecisionOption, ...]:
    """Create only agent-side, reversible experiments; never actions imposed on the owner."""
    return tuple(DecisionOption(
        f"adapt-{item.recommendation_id}", report.project_id, "sandbox_experiment",
        item.agent_adaptation, item.evidence_refs, min(5, max(1, round(item.priority))),
        min(5, max(1, round(item.priority))), 3, 1, True, 0)
        for item in report.recommendations)


def record_growth_report(hub: UnifiedDataHub, report: CollaborationGrowthReport,
                         *, observed_at: str) -> bool:
    digest = _digest(asdict(report))
    refs = tuple(dict.fromkeys(ref for item in report.recommendations for ref in item.evidence_refs))
    refs = refs or ("collaboration:no-repeated-signal",)
    return hub.record_observation(EvidenceObservation(
        f"collaboration-growth-{digest[:20]}", report.project_id, "COLLABORATION_GROWTH",
        f"{len(report.recommendations)} evidence-bound workflow recommendations; no sensitive profile or raw chat stored",
        refs, observed_at, 1.0))
