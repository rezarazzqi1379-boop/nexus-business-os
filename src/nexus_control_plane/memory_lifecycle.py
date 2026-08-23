from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MemoryStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    INVALIDATED = "invalidated"
    HISTORICAL = "historical"


class MemoryUse(str, Enum):
    DECISION_CONTEXT = "decision_context"
    CONTRADICTION_REVIEW = "contradiction_review"
    HISTORY_AUDIT = "history_audit"


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    project_id: str
    source_ref: str
    status: MemoryStatus
    valid_from: str
    valid_until: str | None = None
    superseded_by: str | None = None
    confidence: float | None = None


@dataclass(frozen=True)
class MemoryRetrievalDecision:
    include: bool
    reasons: tuple[str, ...]


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def evaluate_memory_for_use(record: MemoryRecord, *, project_id: str, use: MemoryUse) -> MemoryRetrievalDecision:
    """Prevent obsolete or cross-project memory from silently entering decision context."""
    if not isinstance(record, MemoryRecord):
        return MemoryRetrievalDecision(False, ("invalid memory record",))
    if not _text(project_id):
        return MemoryRetrievalDecision(False, ("invalid project_id",))
    if not isinstance(use, MemoryUse):
        return MemoryRetrievalDecision(False, ("invalid memory use",))
    for field in ("memory_id", "project_id", "source_ref", "valid_from"):
        if not _text(getattr(record, field)):
            return MemoryRetrievalDecision(False, (f"invalid {field}",))
    if record.valid_until is not None and not _text(record.valid_until):
        return MemoryRetrievalDecision(False, ("invalid valid_until",))
    if record.superseded_by is not None and not _text(record.superseded_by):
        return MemoryRetrievalDecision(False, ("invalid superseded_by",))
    if record.confidence is not None:
        if not isinstance(record.confidence, (int, float)) or isinstance(record.confidence, bool) or not 0 <= float(record.confidence) <= 1:
            return MemoryRetrievalDecision(False, ("invalid confidence",))

    if record.project_id != project_id:
        return MemoryRetrievalDecision(False, ("cross-project memory excluded",))

    if use is MemoryUse.DECISION_CONTEXT:
        if record.status is not MemoryStatus.ACTIVE:
            return MemoryRetrievalDecision(False, (f"{record.status.value} memory excluded from current decision context",))
        if record.valid_until is not None:
            return MemoryRetrievalDecision(False, ("time-bounded memory requires live freshness resolution before decision use",))
        return MemoryRetrievalDecision(True, ("active project-scoped memory",))

    if use is MemoryUse.CONTRADICTION_REVIEW:
        return MemoryRetrievalDecision(True, ("historical/superseded records may be needed to explain contradiction lineage",))

    return MemoryRetrievalDecision(True, ("history audit preserves retrievable evidence regardless of current validity",))
