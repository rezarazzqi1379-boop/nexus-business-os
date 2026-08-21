from __future__ import annotations

from dataclasses import dataclass
from typing import Any


BLOCKING_FIELD_STATUSES = {
    "missing_blocker",
    "not_verified_for_requirement",
    "budgetary_not_engineering_verified",
    "supplier_stated_not_fat_verified",
}

POSITIVE_FIELD_STATUSES = {
    "supplier_stated_match",
    "supplier_stated",
    "quoted",
    "budgetary",
    "supplier_stated_budgetary",
}


@dataclass(frozen=True)
class CandidateReadiness:
    supplier_id: str
    readiness_percent: int
    blocking_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]
    inconsistent_fields: tuple[str, ...]
    selection_allowed: bool
    rationale: tuple[str, ...]


def _field_status(field: dict[str, Any]) -> str:
    return str(field.get("status", "")).strip()


def evaluate_candidate(candidate: dict[str, Any], buyer_baseline: dict[str, Any]) -> CandidateReadiness:
    fields = candidate["fields"]
    total = len(fields)
    if total == 0:
        raise ValueError("candidate must contain qualification fields")

    buyer_blockers = tuple(
        key for key, value in buyer_baseline.items()
        if isinstance(value, dict) and value.get("blocking") is True
    )

    blocking = []
    missing = []
    inconsistent = []
    usable = 0

    for name, field in fields.items():
        status = _field_status(field)
        value = field.get("value")

        if "inconsistency" in status:
            inconsistent.append(name)
        if status in BLOCKING_FIELD_STATUSES:
            blocking.append(name)
        if value is None or status.startswith("missing") or status.endswith("_missing") or status == "pending":
            missing.append(name)
        if value is not None and status not in BLOCKING_FIELD_STATUSES and "inconsistency" not in status:
            usable += 1

    readiness = round((usable / total) * 100)
    selection_allowed = not buyer_blockers and not blocking and not inconsistent

    rationale = []
    if buyer_blockers:
        rationale.append("buyer_baseline_has_unresolved_blockers")
    if blocking:
        rationale.append("candidate_has_blocking_technical_gaps")
    if inconsistent:
        rationale.append("candidate_has_internal_document_inconsistencies")
    if not rationale:
        rationale.append("no_current_selection_blocker_detected")

    return CandidateReadiness(
        supplier_id=candidate["supplier_id"],
        readiness_percent=readiness,
        blocking_fields=tuple(blocking),
        missing_fields=tuple(missing),
        inconsistent_fields=tuple(inconsistent),
        selection_allowed=selection_allowed,
        rationale=tuple(rationale),
    )


def evaluate_matrix(matrix: dict[str, Any]) -> tuple[CandidateReadiness, ...]:
    baseline = matrix["buyer_baseline"]
    return tuple(evaluate_candidate(candidate, baseline) for candidate in matrix["candidates"])


def highest_readiness_without_selection(matrix: dict[str, Any]) -> CandidateReadiness:
    results = evaluate_matrix(matrix)
    if not results:
        raise ValueError("matrix must contain candidates")
    return max(results, key=lambda item: item.readiness_percent)
