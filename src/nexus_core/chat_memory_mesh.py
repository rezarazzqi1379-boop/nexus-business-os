from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import log
from typing import Iterable


@dataclass(frozen=True)
class ChatShard:
    shard_id: str
    chat_ref: str
    created_at: datetime
    source_version_ref: str
    project_refs: tuple[str, ...]
    goal_refs: tuple[str, ...]
    tags: tuple[str, ...]
    summary: str
    evidence_refs: tuple[str, ...]
    supersedes: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrievedShard:
    shard: ChatShard
    score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class MemoryBundle:
    query: str
    retrieved: tuple[RetrievedShard, ...]
    conflicts: tuple[tuple[str, str], ...]
    source_version_refs: tuple[str, ...]


def _norm(text: str) -> set[str]:
    return {token.strip('.,:;()[]{}<>"\'').casefold() for token in text.split() if token.strip()}


def validate_shard(shard: ChatShard) -> tuple[str, ...]:
    errors: list[str] = []
    for name, value in (("shard_id", shard.shard_id), ("chat_ref", shard.chat_ref), ("source_version_ref", shard.source_version_ref), ("summary", shard.summary)):
        if not isinstance(value, str) or not value.strip():
            errors.append(f"invalid_{name}")
    if shard.created_at.tzinfo is None:
        errors.append("timezone_naive_created_at")
    for name, refs in (("project_refs", shard.project_refs), ("goal_refs", shard.goal_refs), ("tags", shard.tags), ("evidence_refs", shard.evidence_refs), ("supersedes", shard.supersedes)):
        if not isinstance(refs, tuple):
            errors.append(f"invalid_{name}_type")
            continue
        if any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            errors.append(f"invalid_{name}")
        if len(refs) != len(set(refs)):
            errors.append(f"duplicate_{name}")
    if not shard.evidence_refs:
        errors.append("missing_evidence_refs")
    return tuple(errors)


def retrieve_chat_context(
    shards: Iterable[ChatShard],
    *,
    query: str,
    project_refs: tuple[str, ...] = (),
    goal_refs: tuple[str, ...] = (),
    limit: int = 10,
) -> MemoryBundle:
    """Retrieve relevant cross-chat state without pretending the chat UI is a database.

    Scores are deterministic bookkeeping signals, not semantic truth. Live/canonical
    sources still outrank chat memory for mutable state. Superseded shards remain
    retrievable for provenance but are discounted.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("invalid_query")
    if limit < 1 or limit > 50:
        raise ValueError("invalid_limit")

    items = tuple(shards)
    seen_ids: set[str] = set()
    superseded_ids: set[str] = set()
    for shard in items:
        errors = validate_shard(shard)
        if errors:
            raise ValueError(",".join(errors))
        if shard.shard_id in seen_ids:
            raise ValueError("duplicate_shard_id")
        seen_ids.add(shard.shard_id)
        superseded_ids.update(shard.supersedes)

    q = _norm(query)
    ranked: list[RetrievedShard] = []
    for shard in items:
        searchable = _norm(" ".join((shard.summary, *shard.tags, *shard.project_refs, *shard.goal_refs)))
        overlap = len(q & searchable)
        lexical = overlap / max(len(q), 1)
        project_boost = 0.35 if set(project_refs) & set(shard.project_refs) else 0.0
        goal_boost = 0.35 if set(goal_refs) & set(shard.goal_refs) else 0.0
        evidence_bonus = min(log(len(shard.evidence_refs) + 1, 10), 0.25)
        superseded_penalty = 0.35 if shard.shard_id in superseded_ids else 0.0
        score = max(0.0, lexical + project_boost + goal_boost + evidence_bonus - superseded_penalty)
        if score <= 0:
            continue
        reasons: list[str] = []
        if overlap:
            reasons.append("query_overlap")
        if project_boost:
            reasons.append("project_match")
        if goal_boost:
            reasons.append("goal_match")
        if shard.shard_id in superseded_ids:
            reasons.append("superseded_history")
        ranked.append(RetrievedShard(shard, round(score, 6), tuple(reasons)))

    ranked.sort(key=lambda item: (-item.score, item.shard.created_at, item.shard.shard_id), reverse=False)
    selected = tuple(ranked[:limit])

    conflicts: list[tuple[str, str]] = []
    for i, left in enumerate(selected):
        for right in selected[i + 1:]:
            shared_scope = (set(left.shard.project_refs) & set(right.shard.project_refs)) or (set(left.shard.goal_refs) & set(right.shard.goal_refs))
            if not shared_scope:
                continue
            if left.shard.summary != right.shard.summary and left.shard.source_version_ref != right.shard.source_version_ref:
                conflicts.append((left.shard.shard_id, right.shard.shard_id))

    versions = tuple(dict.fromkeys(item.shard.source_version_ref for item in selected))
    return MemoryBundle(query=query, retrieved=selected, conflicts=tuple(conflicts), source_version_refs=versions)


def build_cross_chat_bootstrap(bundle: MemoryBundle) -> str:
    if not bundle.retrieved:
        return "No relevant chat shards found. Recover from canonical live sources and the Universal Resume Pack before continuing."
    shard_refs = ", ".join(item.shard.shard_id for item in bundle.retrieved)
    conflict_note = " Preserve and resolve shard conflicts against live/canonical evidence." if bundle.conflicts else ""
    return (
        f"Resume NEXUS using cross-chat shards [{shard_refs}] as continuity evidence only."
        " Recover project/goal scope, blockers, decisions, experiments, code refs and Human Gates; then live-verify mutable systems before acting."
        + conflict_note
        + " Continue the highest-value safe reversible work without asking for context already present in the retrieved shards or canonical sources."
    )
