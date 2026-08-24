from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


ALLOWED_INSTALL_STATES = frozenset({"installed", "not_installed", "unknown"})
ALLOWED_PERMISSION_LEVELS = frozenset({"read_only", "ask_before_writes", "full_access", "unknown"})
ALLOWED_PROBE_STATES = frozenset({"passed", "failed", "not_run"})


@dataclass(frozen=True)
class CapabilityObservation:
    capability_id: str
    observed_at: str
    manifest_install_state: str
    permission_install_state: str
    permission_level: str
    read_probe: str
    write_needed: bool
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class CapabilityAssessment:
    capability_id: str
    effective_state: str
    risk: str
    recommendation: str
    reasons: tuple[str, ...]


def validate_observation(item: CapabilityObservation) -> None:
    if not item.capability_id.strip() or not item.observed_at.strip():
        raise ValueError("invalid_capability_identity")
    if item.manifest_install_state not in ALLOWED_INSTALL_STATES:
        raise ValueError("invalid_manifest_state")
    if item.permission_install_state not in ALLOWED_INSTALL_STATES:
        raise ValueError("invalid_permission_state")
    if item.permission_level not in ALLOWED_PERMISSION_LEVELS:
        raise ValueError("invalid_permission_level")
    if item.read_probe not in ALLOWED_PROBE_STATES:
        raise ValueError("invalid_probe_state")
    if not isinstance(item.write_needed, bool):
        raise ValueError("invalid_write_need")
    if not item.evidence_refs or any(not ref.strip() for ref in item.evidence_refs):
        raise ValueError("capability_evidence_required")


def assess_capability(item: CapabilityObservation) -> CapabilityAssessment:
    validate_observation(item)
    reasons: list[str] = []
    if item.manifest_install_state != item.permission_install_state:
        return CapabilityAssessment(
            item.capability_id,
            "contradictory",
            "high",
            "block_sensitive_use_and_resolve_state",
            ("manifest and permission services disagree",),
        )
    if item.manifest_install_state != "installed":
        return CapabilityAssessment(
            item.capability_id,
            "unavailable",
            "low",
            "do_not_install_without_measured_need",
            ("capability is not confirmed installed",),
        )
    if item.read_probe == "failed":
        return CapabilityAssessment(
            item.capability_id,
            "degraded",
            "medium",
            "keep_fail_closed_and_diagnose",
            ("live read probe failed",),
        )
    if item.permission_level == "full_access" and not item.write_needed:
        reasons.append("permission broader than current read-only need")
        return CapabilityAssessment(
            item.capability_id,
            "available",
            "high",
            "propose_scope_down_with_human_approval",
            tuple(reasons),
        )
    if item.read_probe == "not_run":
        return CapabilityAssessment(
            item.capability_id,
            "unverified",
            "medium",
            "run_smallest_read_only_probe",
            ("manifest state alone does not prove usable connection",),
        )
    return CapabilityAssessment(
        item.capability_id,
        "available",
        "low",
        "keep_current_scope",
        ("installed state and read probe agree",),
    )


def audit_capabilities(items: Iterable[CapabilityObservation], *, max_items: int = 100) -> tuple[CapabilityAssessment, ...]:
    observations = tuple(items)
    if not 1 <= len(observations) <= max_items <= 500:
        raise ValueError("invalid_capability_batch")
    seen: set[str] = set()
    results: list[CapabilityAssessment] = []
    for item in observations:
        validate_observation(item)
        if item.capability_id in seen:
            raise ValueError("duplicate_capability_id")
        seen.add(item.capability_id)
        results.append(assess_capability(item))
    risk_order = {"high": 0, "medium": 1, "low": 2}
    return tuple(sorted(results, key=lambda result: (risk_order[result.risk], result.capability_id)))
