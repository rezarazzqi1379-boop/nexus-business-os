from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from nexus_control_plane.forge_registry import canonical_owner


class ShadowDisposition(str, Enum):
    KEEP = "keep"
    KEEP_SHADOW = "keep_shadow"
    CHECKPOINT = "checkpoint"
    EXPERIMENT = "experiment"
    INCUBATOR = "incubator"
    EXTRACT = "extract"
    HARDENING_HOLD = "hardening_hold"
    HOLD = "hold"
    INTEGRATION_ONLY = "integration_only"
    SUPERSEDED = "superseded"


@dataclass(frozen=True)
class ShadowAuditRecord:
    pr_number: int
    disposition: ShadowDisposition
    evidence_ref: str
    rationale: str
    concern: str | None = None
    owner: str | None = None


def validate_shadow_audit(records: Iterable[ShadowAuditRecord]) -> tuple[str, ...]:
    errors: list[str] = []
    seen: set[int] = set()
    for index, record in enumerate(records):
        if not isinstance(record, ShadowAuditRecord):
            errors.append(f"record[{index}] invalid type")
            continue
        if not isinstance(record.pr_number, int) or isinstance(record.pr_number, bool) or record.pr_number <= 0:
            errors.append(f"record[{index}] invalid pr_number")
        elif record.pr_number in seen:
            errors.append(f"duplicate pr_number:{record.pr_number}")
        else:
            seen.add(record.pr_number)
        if not isinstance(record.disposition, ShadowDisposition):
            errors.append(f"PR{record.pr_number}:invalid disposition")
        if not isinstance(record.evidence_ref, str) or not record.evidence_ref.startswith("https://github.com/"):
            errors.append(f"PR{record.pr_number}:invalid evidence_ref")
        if not isinstance(record.rationale, str) or not record.rationale.strip():
            errors.append(f"PR{record.pr_number}:missing rationale")
        if record.concern is None:
            if record.owner is not None:
                errors.append(f"PR{record.pr_number}:owner without concern")
            continue
        if not isinstance(record.concern, str) or not record.concern.strip():
            errors.append(f"PR{record.pr_number}:invalid concern")
            continue
        expected = canonical_owner(record.concern)
        if expected is None:
            if record.owner is not None:
                errors.append(f"PR{record.pr_number}:unregistered concern cannot claim owner")
        elif record.owner != expected:
            errors.append(f"PR{record.pr_number}:owner mismatch:{record.concern}:{record.owner}!={expected}")
    return tuple(errors)
