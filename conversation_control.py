"""Conversation intelligence for the NEXUS control plane.

The module consumes metadata/summaries exported by an authorized Codex/ChatGPT
connector.  It never reads, messages, archives, or mutates a conversation by
itself; those remain adapter operations behind exact-scope authorization.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable, Literal, Mapping

ThreadState = Literal["active", "idle", "blocked", "complete", "unknown"]
NeedKind = Literal["blocker", "evidence_gap", "duplication", "stale_context", "opportunity"]


@dataclass(frozen=True)
class ConversationSnapshot:
    thread_id: str
    title: str
    summary: str
    project_id: str | None
    state: ThreadState
    updated_at: int
    source_ref: str

    def validate(self) -> None:
        if not self.thread_id.strip() or not self.title.strip() or not self.source_ref.strip():
            raise ValueError("invalid_conversation_identity")
        if self.state not in {"active", "idle", "blocked", "complete", "unknown"}:
            raise ValueError("invalid_conversation_state")
        if isinstance(self.updated_at, bool) or not isinstance(self.updated_at, int) or self.updated_at < 0:
            raise ValueError("invalid_updated_at")


@dataclass(frozen=True)
class TokenPolicy:
    max_context_tokens: int = 24_000
    reserve_output_tokens: int = 4_000
    max_history_share: float = 0.45
    max_evidence_share: float = 0.35

    def validate(self) -> None:
        if self.max_context_tokens < 1000 or self.reserve_output_tokens < 1:
            raise ValueError("invalid_token_budget")
        if self.reserve_output_tokens >= self.max_context_tokens:
            raise ValueError("output_reserve_exceeds_context")
        if not 0 < self.max_history_share <= 1 or not 0 < self.max_evidence_share <= 1:
            raise ValueError("invalid_token_share")
        if self.max_history_share + self.max_evidence_share > 0.9:
            raise ValueError("insufficient_working_token_share")


@dataclass(frozen=True)
class TokenAllocation:
    history: int
    evidence: int
    working: int
    output: int


def allocate_tokens(policy: TokenPolicy, *, estimated_history: int, estimated_evidence: int) -> TokenAllocation:
    """Allocate context deterministically, preserving reasoning and output room."""
    policy.validate()
    if min(estimated_history, estimated_evidence) < 0:
        raise ValueError("negative_token_estimate")
    usable = policy.max_context_tokens - policy.reserve_output_tokens
    history = min(estimated_history, int(usable * policy.max_history_share))
    evidence = min(estimated_evidence, int(usable * policy.max_evidence_share))
    return TokenAllocation(history, evidence, usable - history - evidence, policy.reserve_output_tokens)


_FILLER = re.compile(r"\b(please|kindly|just|basically|actually)\b", re.IGNORECASE)


def normalize_question(text: str, *, project_id: str, desired_output: str = "evidence-backed answer") -> str:
    """Produce a compact task contract without silently changing user intent."""
    cleaned = " ".join(_FILLER.sub("", text).split())
    if not cleaned or not project_id.strip() or not desired_output.strip():
        raise ValueError("invalid_question_contract")
    return f"project={project_id}; objective={cleaned}; output={desired_output}; preserve_unknowns=true"


@dataclass(frozen=True)
class ProjectNeed:
    need_id: str
    project_id: str
    kind: NeedKind
    description: str
    evidence_refs: tuple[str, ...]
    urgency: int
    leverage: int
    confidence: float

    @property
    def score(self) -> float:
        return round((self.urgency * 0.4 + self.leverage * 0.4 + self.confidence * 5 * 0.2), 4)


def discover_needs(snapshots: Iterable[ConversationSnapshot], *, now: int, stale_after: int = 2_592_000) -> tuple[ProjectNeed, ...]:
    """Find coordination needs from metadata only; summaries are untrusted claims."""
    items = tuple(snapshots)
    seen: set[str] = set()
    needs: list[ProjectNeed] = []
    title_groups: dict[tuple[str, str], list[ConversationSnapshot]] = {}
    for item in items:
        item.validate()
        if item.thread_id in seen:
            raise ValueError("duplicate_thread_id")
        seen.add(item.thread_id)
        project = item.project_id or "UNASSIGNED"
        key = (project, " ".join(item.title.casefold().split()))
        title_groups.setdefault(key, []).append(item)
        age = max(0, now - item.updated_at)
        if item.state == "blocked":
            needs.append(_need(project, "blocker", f"Resolve blocked task: {item.title}", (item.source_ref,), 5, 4, .9))
        elif age > stale_after and item.state in {"active", "idle"}:
            needs.append(_need(project, "stale_context", f"Refresh or close stale task: {item.title}",
                               (item.source_ref,), 2, 2, .8))
        if not item.summary.strip():
            needs.append(_need(project, "evidence_gap", f"Create evidence-linked summary: {item.title}",
                               (item.source_ref,), 2, 3, .7))
    for (project, title), group in title_groups.items():
        if len(group) > 1:
            needs.append(_need(project, "duplication", f"Reconcile {len(group)} tasks titled {title}",
                               tuple(sorted(x.source_ref for x in group)), 3, 4, .95))
    return tuple(sorted(needs, key=lambda n: (-n.score, n.project_id, n.need_id)))


def _need(project: str, kind: NeedKind, description: str, refs: tuple[str, ...],
          urgency: int, leverage: int, confidence: float) -> ProjectNeed:
    digest = sha256(f"{project}|{kind}|{description}|{refs}".encode()).hexdigest()[:16]
    return ProjectNeed(f"need_{digest}", project, kind, description, refs, urgency, leverage, confidence)


@dataclass(frozen=True)
class IdeaProposal:
    idea_id: str
    need_id: str
    hypothesis: str
    smallest_experiment: str
    acceptance_test: str
    expected_leverage: int
    risk: int
    auto_runnable: bool


def propose_ideas(needs: Iterable[ProjectNeed], *, max_ideas: int = 10) -> tuple[IdeaProposal, ...]:
    """Turn observed needs into bounded experiments, never self-authorizing actions."""
    if not 1 <= max_ideas <= 100:
        raise ValueError("invalid_idea_limit")
    templates: Mapping[NeedKind, tuple[str, str, str, int, int]] = {
        "blocker": ("A focused blocker brief will expose the minimum owner decision.", "Draft one decision brief.", "Brief names evidence, options and exact decision.", 4, 1),
        "evidence_gap": ("A structured summary will reduce repeated context loading.", "Create a source-linked compact summary.", "Another task can resume from summary without raw history.", 5, 1),
        "duplication": ("A canonical task plus references can replace duplicate active context.", "Propose a primary task and merge map.", "No unique evidence or unresolved action is lost.", 5, 2),
        "stale_context": ("A freshness check can distinguish live work from historical context.", "Run a read-only state refresh.", "Every retained claim has a current source or stale label.", 4, 1),
        "opportunity": ("A small reversible experiment can validate value before expansion.", "Run a sandboxed comparison.", "Measured lift exceeds baseline without policy regression.", 4, 2),
    }
    ideas = []
    for need in sorted(needs, key=lambda n: (-n.score, n.need_id))[:max_ideas]:
        hypothesis, experiment, acceptance, leverage, risk = templates[need.kind]
        idea_id = "idea_" + sha256(f"{need.need_id}|{experiment}".encode()).hexdigest()[:16]
        ideas.append(IdeaProposal(idea_id, need.need_id, hypothesis, experiment, acceptance,
                                  leverage, risk, risk <= 2))
    return tuple(ideas)

