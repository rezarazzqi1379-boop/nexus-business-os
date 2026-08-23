from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ContradictionStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    SUPERSEDED = "superseded"


@dataclass(frozen=True)
class ContradictionRecord:
    contradiction_id: str
    subject: str
    claim_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    status: ContradictionStatus = ContradictionStatus.OPEN
    resolution_ref: str | None = None

    def __post_init__(self) -> None:
        for name, value in (("contradiction_id", self.contradiction_id), ("subject", self.subject)):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(f"{name} must be a normalized non-empty string")
        if not isinstance(self.status, ContradictionStatus):
            raise ValueError("status must be ContradictionStatus")
        if len(self.claim_refs) < 2:
            raise ValueError("contradiction requires at least two claim refs")
        for refs in (self.claim_refs, self.evidence_refs):
            if not isinstance(refs, tuple) or not refs:
                raise ValueError("claim/evidence refs must be non-empty tuples")
            if len(set(refs)) != len(refs):
                raise ValueError("claim/evidence refs must be unique")
            for ref in refs:
                if not isinstance(ref, str) or not ref.strip() or ref != ref.strip():
                    raise ValueError("refs must be normalized non-empty strings")
        if self.status is ContradictionStatus.RESOLVED:
            if not isinstance(self.resolution_ref, str) or not self.resolution_ref.strip() or self.resolution_ref != self.resolution_ref.strip():
                raise ValueError("resolved contradiction requires resolution_ref")
        elif self.resolution_ref is not None:
            raise ValueError("resolution_ref is allowed only for resolved contradictions")


@dataclass(frozen=True)
class ContradictionGate:
    open_count: int
    open_refs: tuple[str, ...]
    research_refresh_required: bool
    promotion_blocked: bool


def evaluate_contradictions(records: tuple[ContradictionRecord, ...]) -> ContradictionGate:
    """Gate unresolved contradictions without choosing which claim is true."""
    if not isinstance(records, tuple):
        raise ValueError("records must be a tuple")
    ids: set[str] = set()
    open_refs: list[str] = []
    for record in records:
        if not isinstance(record, ContradictionRecord):
            raise ValueError("records must contain ContradictionRecord")
        if record.contradiction_id in ids:
            raise ValueError("duplicate contradiction_id")
        ids.add(record.contradiction_id)
        if record.status is ContradictionStatus.OPEN:
            open_refs.append(record.contradiction_id)
    refs = tuple(open_refs)
    return ContradictionGate(len(refs), refs, bool(refs), bool(refs))
