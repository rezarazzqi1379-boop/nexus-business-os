"""Evidence-bounded procurement process-friction modeling.

This module captures repeated rework caused by decision-critical information or
commercial prerequisites becoming clear only after supplier outreach. These are
not automatically treated as commercial failures. The purpose is to identify
repeatable process friction that may justify a pre-RFQ readiness improvement.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ProcurementFrictionEvent:
    event_id: str
    project_id: str
    category: str
    missing_or_misaligned_item: str
    consequence: str
    source_ref: str

    def __post_init__(self) -> None:
        fields = (
            self.event_id,
            self.project_id,
            self.category,
            self.missing_or_misaligned_item,
            self.consequence,
            self.source_ref,
        )
        if any(not isinstance(v, str) or not v.strip() for v in fields):
            raise ValueError("all friction-event fields must be non-empty strings")


@dataclass(frozen=True)
class ProcurementFrictionPattern:
    pattern_id: str
    category: str
    occurrences: int
    distinct_projects: int
    event_ids: tuple[str, ...]
    source_refs: tuple[str, ...]
    missing_or_misaligned_items: tuple[str, ...]
    eligible_for_improvement_proposal: bool
    reason: str


def _norm(value: str) -> str:
    return " ".join(value.strip().lower().split())


def mine_procurement_friction_patterns(
    events: Iterable[ProcurementFrictionEvent],
    *,
    min_occurrences: int = 3,
    min_distinct_projects: int = 3,
) -> tuple[ProcurementFrictionPattern, ...]:
    if min_occurrences < 2:
        raise ValueError("min_occurrences must be >= 2")
    if min_distinct_projects < 2:
        raise ValueError("min_distinct_projects must be >= 2")

    seen: dict[str, ProcurementFrictionEvent] = {}
    for event in events:
        if not isinstance(event, ProcurementFrictionEvent):
            raise ValueError("events must contain ProcurementFrictionEvent objects")
        existing = seen.get(event.event_id)
        if existing is not None and existing != event:
            raise ValueError(f"conflicting duplicate event_id: {event.event_id}")
        seen[event.event_id] = event

    grouped: dict[str, list[ProcurementFrictionEvent]] = {}
    for event in seen.values():
        grouped.setdefault(_norm(event.category), []).append(event)

    output: list[ProcurementFrictionPattern] = []
    for category, rows in sorted(grouped.items()):
        projects = {_norm(r.project_id) for r in rows}
        eligible = len(rows) >= min_occurrences and len(projects) >= min_distinct_projects
        output.append(
            ProcurementFrictionPattern(
                pattern_id=f"procurement-friction:{category}",
                category=category,
                occurrences=len(rows),
                distinct_projects=len(projects),
                event_ids=tuple(sorted(r.event_id for r in rows)),
                source_refs=tuple(sorted({r.source_ref for r in rows})),
                missing_or_misaligned_items=tuple(sorted({r.missing_or_misaligned_item for r in rows})),
                eligible_for_improvement_proposal=eligible,
                reason=(
                    "repeated cross-project procurement friction meets evidence thresholds"
                    if eligible
                    else "insufficient cross-project evidence; keep as process observation only"
                ),
            )
        )
    return tuple(output)
