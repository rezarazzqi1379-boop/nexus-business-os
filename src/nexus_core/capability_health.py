from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Literal

HealthState = Literal[
    "verified_read",
    "verified_write",
    "degraded",
    "installed_unverified",
    "not_available_here",
    "blocked",
]

AccessKind = Literal["read", "write"]

_ALLOWED_STATES = {
    "verified_read",
    "verified_write",
    "degraded",
    "installed_unverified",
    "not_available_here",
    "blocked",
}
_ALLOWED_ACCESS = {"read", "write"}


@dataclass(frozen=True)
class CapabilityHealth:
    capability_id: str
    state: HealthState
    checked_at: str
    route_ref: str
    evidence_ref: str
    proven_access: tuple[AccessKind, ...] = ("read",)


@dataclass(frozen=True)
class CapabilityHealthFinding:
    capability_id: str
    code: str
    severity: Literal["info", "warning", "block"]
    detail: str


def _aware_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value or value != value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def _clean_ref(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value == value.strip() and len(value) <= 256


def validate_capability_health(health: object) -> list[str]:
    if not isinstance(health, CapabilityHealth):
        return ["health must be a CapabilityHealth"]

    errors: list[str] = []
    if not _clean_ref(health.capability_id):
        errors.append("capability_id must be a bounded canonical string")
    if health.state not in _ALLOWED_STATES:
        errors.append("state is unsupported")
    if _aware_datetime(health.checked_at) is None:
        errors.append("checked_at must be a timezone-aware ISO timestamp")
    if not _clean_ref(health.route_ref):
        errors.append("route_ref must be a bounded canonical string")
    if not _clean_ref(health.evidence_ref):
        errors.append("evidence_ref must be a bounded canonical string")
    if not isinstance(health.proven_access, tuple):
        errors.append("proven_access must be a tuple")
    else:
        if len(set(health.proven_access)) != len(health.proven_access):
            errors.append("proven_access cannot contain duplicates")
        if any(access not in _ALLOWED_ACCESS for access in health.proven_access):
            errors.append("proven_access contains unsupported access kind")

    if health.state == "verified_read" and "write" in health.proven_access:
        errors.append("verified_read cannot prove write access")
    if health.state == "verified_write" and "write" not in health.proven_access:
        errors.append("verified_write requires explicit write proof")
    if health.state in {"blocked", "not_available_here", "installed_unverified"} and health.proven_access:
        errors.append("unavailable or unverified capability cannot claim proven access")
    return errors


def capability_can_satisfy(
    health: object,
    *,
    required_access: AccessKind,
    now: datetime,
    max_age_seconds: int = 21_600,
) -> bool:
    if validate_capability_health(health):
        return False
    if required_access not in _ALLOWED_ACCESS:
        return False
    if now.tzinfo is None or now.utcoffset() is None:
        return False
    if not isinstance(max_age_seconds, int) or isinstance(max_age_seconds, bool) or max_age_seconds < 0:
        return False

    assert isinstance(health, CapabilityHealth)
    checked = _aware_datetime(health.checked_at)
    assert checked is not None
    age_seconds = (now.astimezone(timezone.utc) - checked).total_seconds()
    if age_seconds < 0 or age_seconds > max_age_seconds:
        return False

    if health.state in {"degraded", "installed_unverified", "not_available_here", "blocked"}:
        return False
    return required_access in health.proven_access


def diagnose_capability_health(
    records: Iterable[object],
    *,
    now: datetime,
    max_age_seconds: int = 21_600,
) -> tuple[CapabilityHealthFinding, ...]:
    findings: list[CapabilityHealthFinding] = []
    seen: set[str] = set()

    for record in records:
        errors = validate_capability_health(record)
        if errors:
            capability_id = record.capability_id if isinstance(record, CapabilityHealth) and isinstance(record.capability_id, str) else "unknown"
            findings.append(CapabilityHealthFinding(capability_id, "invalid_health_record", "block", "; ".join(errors)))
            continue

        assert isinstance(record, CapabilityHealth)
        if record.capability_id in seen:
            findings.append(CapabilityHealthFinding(record.capability_id, "duplicate_health_record", "block", "multiple health records exist for one capability"))
            continue
        seen.add(record.capability_id)

        checked = _aware_datetime(record.checked_at)
        assert checked is not None
        if now.tzinfo is None or now.utcoffset() is None:
            findings.append(CapabilityHealthFinding(record.capability_id, "invalid_diagnostic_clock", "block", "diagnostic time must be timezone-aware"))
            continue
        age_seconds = (now.astimezone(timezone.utc) - checked).total_seconds()
        if age_seconds < 0:
            findings.append(CapabilityHealthFinding(record.capability_id, "future_health_check", "block", "health evidence is timestamped in the future"))
        elif age_seconds > max_age_seconds:
            findings.append(CapabilityHealthFinding(record.capability_id, "stale_health_check", "warning", "capability health evidence is stale"))

        if record.state == "degraded":
            findings.append(CapabilityHealthFinding(record.capability_id, "connector_degraded", "warning", "connector responds but required route/capability is degraded"))
        elif record.state in {"installed_unverified", "not_available_here"}:
            findings.append(CapabilityHealthFinding(record.capability_id, "route_unverified", "warning", "installation or external availability is not runtime proof"))
        elif record.state == "blocked":
            findings.append(CapabilityHealthFinding(record.capability_id, "connector_blocked", "block", "authentication, permission or connector failure blocks use"))

    return tuple(findings)
