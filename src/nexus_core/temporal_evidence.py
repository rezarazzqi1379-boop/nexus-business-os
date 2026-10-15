from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal, Sequence

EpistemicClass = Literal["FACT", "MEASUREMENT", "CLAIM", "ESTIMATE", "ASSUMPTION", "HYPOTHESIS", "UNKNOWN"]
EvidenceState = Literal["CURRENT", "HISTORICAL", "SUPERSEDED", "CONFLICT", "INVALID"]


@dataclass(frozen=True)
class EvidenceNode:
    evidence_id: str
    project_id: str
    subject_id: str
    field: str
    value: str
    epistemic_class: EpistemicClass
    source_ref: str
    observed_at: str
    valid_from: str
    valid_to: str | None = None
    supersedes: tuple[str, ...] = ()

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        for name in ("evidence_id", "project_id", "subject_id", "field", "value", "source_ref", "observed_at", "valid_from"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{name} required")
        for name in ("observed_at", "valid_from"):
            try:
                datetime.fromisoformat(getattr(self, name).replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{name} must be ISO-8601")
        if self.valid_to is not None:
            try:
                datetime.fromisoformat(self.valid_to.replace("Z", "+00:00"))
            except ValueError:
                errors.append("valid_to must be ISO-8601")
        if self.evidence_id in self.supersedes:
            errors.append("evidence cannot supersede itself")
        return tuple(errors)


def _dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def resolve_subject_field(nodes: Sequence[EvidenceNode], project_id: str, subject_id: str, field: str, at: str) -> tuple[EvidenceState, tuple[EvidenceNode, ...]]:
    relevant = [n for n in nodes if n.project_id == project_id and n.subject_id == subject_id and n.field == field]
    if any(n.validate() for n in relevant):
        return "INVALID", tuple()
    point = _dt(at)
    active = [n for n in relevant if _dt(n.valid_from) <= point and (n.valid_to is None or point < _dt(n.valid_to))]
    superseded_ids = {sid for n in active for sid in n.supersedes}
    active = [n for n in active if n.evidence_id not in superseded_ids]
    if not active:
        historical = tuple(sorted(relevant, key=lambda n: _dt(n.valid_from)))
        return ("HISTORICAL" if historical else "CURRENT"), historical
    values = {n.value for n in active}
    if len(values) > 1:
        return "CONFLICT", tuple(sorted(active, key=lambda n: _dt(n.observed_at)))
    return "CURRENT", tuple(sorted(active, key=lambda n: _dt(n.observed_at)))


def cross_project_safe(nodes: Sequence[EvidenceNode], project_id: str) -> tuple[EvidenceNode, ...]:
    return tuple(n for n in nodes if n.project_id == project_id and not n.validate())
