from dataclasses import dataclass
from typing import Callable, Literal

from nexus_autonomy.runner import ExecutionResult
from nexus_core.autonomy import PlannedWork

Confidence = Literal["strong", "partial", "weak", "unverified"]


@dataclass(frozen=True)
class ResearchArtifact:
    summary: str
    evidence_refs: tuple[str, ...]
    confidence: Confidence
    follow_up_objectives: tuple[str, ...] = ()


ResearchProvider = Callable[[PlannedWork], ResearchArtifact]


def _validate_artifact(artifact: object) -> ResearchArtifact:
    if not isinstance(artifact, ResearchArtifact):
        raise TypeError("research provider must return ResearchArtifact")
    if not isinstance(artifact.summary, str) or not artifact.summary.strip():
        raise ValueError("research summary is required")
    if artifact.confidence not in {"strong", "partial", "weak", "unverified"}:
        raise ValueError("unsupported research confidence")
    if not isinstance(artifact.evidence_refs, tuple):
        raise ValueError("evidence_refs must be a tuple")
    if any(not isinstance(ref, str) or not ref.strip() for ref in artifact.evidence_refs):
        raise ValueError("evidence_refs must contain nonblank strings")
    if artifact.confidence in {"strong", "partial"} and not artifact.evidence_refs:
        raise ValueError("strong or partial research requires retrievable evidence")
    if not isinstance(artifact.follow_up_objectives, tuple):
        raise ValueError("follow_up_objectives must be a tuple")
    if any(not isinstance(value, str) or not value.strip() for value in artifact.follow_up_objectives):
        raise ValueError("follow_up_objectives must contain nonblank strings")
    return artifact


def make_research_executor(provider: ResearchProvider):
    """Wrap a real connector/model research provider behind the runner contract.

    This adapter does not perform network access itself. It enforces evidence discipline
    at the execution boundary so a later web/Gmail/CRM provider cannot claim verified
    research without retrievable evidence.
    """
    if not callable(provider):
        raise TypeError("provider must be callable")

    def execute(work: PlannedWork) -> ExecutionResult:
        if work.task.domain not in {"research", "market_intelligence", "customer_network", "news_monitoring", "innovation"}:
            return ExecutionResult("failed", f"research executor cannot handle domain={work.task.domain}")
        artifact = _validate_artifact(provider(work))
        confidence_note = f"confidence={artifact.confidence}"
        follow_up_note = ""
        if artifact.follow_up_objectives:
            follow_up_note = f"; follow_ups={len(artifact.follow_up_objectives)}"
        return ExecutionResult(
            "succeeded",
            f"{artifact.summary.strip()} [{confidence_note}{follow_up_note}]",
            artifact.evidence_refs,
        )

    return execute
