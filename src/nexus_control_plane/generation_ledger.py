from __future__ import annotations

from dataclasses import dataclass

from nexus_control_plane.recursive_evolution import GenerationAudit


def _refs(value: object, *, required: bool = False) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError("references must be tuples")
    if required and not value:
        raise ValueError("at least one reference is required")
    seen: set[str] = set()
    for ref in value:
        if not isinstance(ref, str) or not ref.strip() or ref != ref.strip():
            raise ValueError("references must be normalized non-empty strings")
        if ref in seen:
            raise ValueError("references must be unique")
        seen.add(ref)
    return value


@dataclass(frozen=True)
class GenerationLedgerEntry:
    generation_id: str
    baseline_version: str
    candidate_version: str
    audit: GenerationAudit
    evidence_refs: tuple[str, ...]
    decision_refs: tuple[str, ...] = ()
    outcome_refs: tuple[str, ...] = ()
    contradiction_refs: tuple[str, ...] = ()
    failure_refs: tuple[str, ...] = ()
    parent_generation_id: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("generation_id", self.generation_id),
            ("baseline_version", self.baseline_version),
            ("candidate_version", self.candidate_version),
        ):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(f"{name} must be a normalized non-empty string")
        if self.baseline_version == self.candidate_version:
            raise ValueError("candidate_version must differ from baseline_version")
        if not isinstance(self.audit, GenerationAudit):
            raise ValueError("audit must be GenerationAudit")
        if self.audit.telemetry.generation_id != self.generation_id:
            raise ValueError("ledger generation_id must match audit telemetry")
        if self.parent_generation_id is not None:
            if not isinstance(self.parent_generation_id, str) or not self.parent_generation_id.strip() or self.parent_generation_id != self.parent_generation_id.strip():
                raise ValueError("parent_generation_id must be normalized when present")
            if self.parent_generation_id == self.generation_id:
                raise ValueError("generation cannot parent itself")
        _refs(self.evidence_refs, required=True)
        _refs(self.decision_refs)
        _refs(self.outcome_refs)
        _refs(self.contradiction_refs)
        _refs(self.failure_refs)


def validate_generation_chain(entries: tuple[GenerationLedgerEntry, ...]) -> tuple[str, ...]:
    """Validate lineage without inventing missing parents or outcomes."""
    if not isinstance(entries, tuple):
        return ("entries must be a tuple",)
    errors: list[str] = []
    seen: dict[str, GenerationLedgerEntry] = {}
    for entry in entries:
        if not isinstance(entry, GenerationLedgerEntry):
            errors.append("ledger contains invalid entry")
            continue
        if entry.generation_id in seen:
            errors.append(f"duplicate generation_id: {entry.generation_id}")
            continue
        if entry.parent_generation_id is not None and entry.parent_generation_id not in seen:
            errors.append(f"missing or out-of-order parent: {entry.parent_generation_id}")
        seen[entry.generation_id] = entry
    return tuple(errors)
