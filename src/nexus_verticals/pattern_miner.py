"""Evidence-bounded pattern mining for NEXUS outcome and failure observations.

The miner only surfaces repeated patterns. It does not tune weights, mutate agents,
open PRs, send messages, or deploy changes. Single observations remain anecdotal.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Literal

from .business_genome_learning import NegativeKnowledgeEvent, OutcomeKind, OutcomeLedgerEntry

PatternKind = Literal["failure", "success"]


@dataclass(frozen=True)
class PatternCandidate:
    pattern_id: str
    kind: PatternKind
    key: str
    occurrences: int
    distinct_projects: int
    observation_ids: tuple[str, ...]
    source_refs: tuple[str, ...]
    eligible_for_improvement_proposal: bool
    reason: str


def _norm(value: str) -> str:
    return " ".join(value.strip().lower().split())


def mine_failure_patterns(
    events: Iterable[NegativeKnowledgeEvent],
    *,
    min_occurrences: int = 2,
    min_distinct_projects: int = 2,
) -> tuple[PatternCandidate, ...]:
    if min_occurrences < 2:
        raise ValueError("min_occurrences must be >= 2")
    if min_distinct_projects < 1:
        raise ValueError("min_distinct_projects must be >= 1")

    groups: dict[str, list[NegativeKnowledgeEvent]] = defaultdict(list)
    seen_ids: dict[str, NegativeKnowledgeEvent] = {}
    for event in events:
        if not isinstance(event, NegativeKnowledgeEvent):
            raise ValueError("events must contain NegativeKnowledgeEvent objects")
        existing = seen_ids.get(event.event_id)
        if existing is not None and existing != event:
            raise ValueError(f"conflicting duplicate event_id: {event.event_id}")
        seen_ids[event.event_id] = event

    for event in seen_ids.values():
        groups[_norm(event.category)].append(event)

    patterns: list[PatternCandidate] = []
    for key, rows in sorted(groups.items()):
        projects = {_norm(row.project_id) for row in rows}
        eligible = len(rows) >= min_occurrences and len(projects) >= min_distinct_projects
        reason = (
            "repeated failure pattern meets occurrence and project-diversity thresholds"
            if eligible
            else "insufficient repeated evidence; keep as negative knowledge only"
        )
        patterns.append(
            PatternCandidate(
                pattern_id=f"failure:{key}",
                kind="failure",
                key=key,
                occurrences=len(rows),
                distinct_projects=len(projects),
                observation_ids=tuple(sorted(row.observation_id for row in rows)),
                source_refs=tuple(sorted({row.source_ref for row in rows})),
                eligible_for_improvement_proposal=eligible,
                reason=reason,
            )
        )
    return tuple(patterns)


def mine_success_patterns(
    entries: Iterable[OutcomeLedgerEntry],
    *,
    min_occurrences: int = 2,
    min_distinct_projects: int = 2,
) -> tuple[PatternCandidate, ...]:
    if min_occurrences < 2:
        raise ValueError("min_occurrences must be >= 2")
    if min_distinct_projects < 1:
        raise ValueError("min_distinct_projects must be >= 1")

    seen_ids: dict[str, OutcomeLedgerEntry] = {}
    for entry in entries:
        if not isinstance(entry, OutcomeLedgerEntry):
            raise ValueError("entries must contain OutcomeLedgerEntry objects")
        existing = seen_ids.get(entry.ledger_id)
        if existing is not None and existing != entry:
            raise ValueError(f"conflicting duplicate ledger_id: {entry.ledger_id}")
        seen_ids[entry.ledger_id] = entry

    groups: dict[str, list[OutcomeLedgerEntry]] = defaultdict(list)
    for entry in seen_ids.values():
        if entry.outcome_kind not in {OutcomeKind.STAGE_SUCCESS, OutcomeKind.FINAL_SUCCESS}:
            continue
        stage = entry.outcome_stage or entry.outcome_kind.value
        groups[_norm(stage)].append(entry)

    patterns: list[PatternCandidate] = []
    for key, rows in sorted(groups.items()):
        projects = {_norm(row.project_id) for row in rows}
        eligible = len(rows) >= min_occurrences and len(projects) >= min_distinct_projects
        reason = (
            "repeated success pattern meets occurrence and project-diversity thresholds"
            if eligible
            else "insufficient repeated evidence; do not generalize from anecdote"
        )
        patterns.append(
            PatternCandidate(
                pattern_id=f"success:{key}",
                kind="success",
                key=key,
                occurrences=len(rows),
                distinct_projects=len(projects),
                observation_ids=tuple(sorted(row.observation_id for row in rows)),
                source_refs=tuple(sorted({row.source_ref for row in rows})),
                eligible_for_improvement_proposal=eligible,
                reason=reason,
            )
        )
    return tuple(patterns)
