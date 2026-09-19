from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

EvidenceClass = Literal["FACT", "MEASUREMENT", "CLAIM", "ESTIMATE", "ASSUMPTION", "HYPOTHESIS", "UNKNOWN"]
Disposition = Literal["MATCH", "DEVIATION", "MISSING", "UNVERIFIED", "BLOCKED"]


@dataclass(frozen=True)
class Requirement:
    requirement_id: str
    project_id: str
    canonical_version: str
    field: str
    expected: str
    mandatory: bool = True


@dataclass(frozen=True)
class ProposalItem:
    requirement_id: str
    project_id: str
    offered: str
    evidence_class: EvidenceClass = "CLAIM"
    source_locator: str = ""


@dataclass(frozen=True)
class Delta:
    requirement_id: str
    disposition: Disposition
    expected: str
    offered: str | None
    evidence_class: EvidenceClass
    source_locator: str
    reason: str


_ALLOWED_EVIDENCE = {"FACT", "MEASUREMENT", "CLAIM", "ESTIMATE", "ASSUMPTION", "HYPOTHESIS", "UNKNOWN"}


def compare_proposal(requirements: Sequence[Requirement], items: Sequence[ProposalItem]) -> tuple[Delta, ...]:
    """Compare supplier proposal evidence against one canonical project requirement set.

    Supplier content is evidence, never authority. Cross-project matching fails closed.
    Only FACT/MEASUREMENT can produce MATCH; vendor CLAIM remains UNVERIFIED even when text matches.
    """
    if not requirements:
        return ()
    project_ids = {r.project_id for r in requirements}
    if len(project_ids) != 1:
        raise ValueError("requirements must belong to exactly one project")
    versions = {r.canonical_version for r in requirements}
    if len(versions) != 1:
        raise ValueError("requirements must use exactly one canonical version")
    if len({r.requirement_id for r in requirements}) != len(requirements):
        raise ValueError("duplicate requirement_id")

    project_id = next(iter(project_ids))
    by_req: dict[str, ProposalItem] = {}
    for item in items:
        if item.evidence_class not in _ALLOWED_EVIDENCE:
            raise ValueError("unsupported evidence class")
        if item.project_id != project_id:
            raise ValueError("cross-project proposal item")
        if item.requirement_id in by_req:
            raise ValueError("duplicate proposal requirement_id")
        by_req[item.requirement_id] = item

    out: list[Delta] = []
    for req in requirements:
        item = by_req.get(req.requirement_id)
        if item is None:
            out.append(Delta(req.requirement_id, "MISSING", req.expected, None, "UNKNOWN", "", "supplier did not address requirement"))
            continue

        offered = item.offered.strip()
        expected = req.expected.strip()
        if not offered:
            out.append(Delta(req.requirement_id, "MISSING", expected, None, item.evidence_class, item.source_locator, "empty supplier response"))
            continue
        if item.evidence_class in {"UNKNOWN", "ASSUMPTION", "HYPOTHESIS", "ESTIMATE"}:
            out.append(Delta(req.requirement_id, "UNVERIFIED", expected, offered, item.evidence_class, item.source_locator, "evidence class cannot satisfy engineering acceptance"))
            continue
        if offered != expected:
            out.append(Delta(req.requirement_id, "DEVIATION", expected, offered, item.evidence_class, item.source_locator, "offered value differs from canonical requirement"))
            continue
        if item.evidence_class == "CLAIM":
            out.append(Delta(req.requirement_id, "UNVERIFIED", expected, offered, item.evidence_class, item.source_locator, "supplier claim matches text but is not independently verified"))
            continue
        out.append(Delta(req.requirement_id, "MATCH", expected, offered, item.evidence_class, item.source_locator, "verified evidence matches canonical requirement"))

    return tuple(out)


def acceptance_summary(deltas: Sequence[Delta]) -> dict[str, int | bool]:
    counts = {key: 0 for key in ("MATCH", "DEVIATION", "MISSING", "UNVERIFIED", "BLOCKED")}
    for delta in deltas:
        counts[delta.disposition] += 1
    counts["ready_for_acceptance"] = bool(deltas) and all(d.disposition == "MATCH" for d in deltas)
    return counts
