from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class AccessState(str, Enum):
    READ_VERIFIED = "READ_VERIFIED"
    WRITE_CAPABLE_UNTESTED = "WRITE_CAPABLE_UNTESTED"
    WRITE_VERIFIED = "WRITE_VERIFIED"
    LIMITED = "LIMITED"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class ActionClass(str, Enum):
    READ = "READ"
    INTERNAL_WRITE = "INTERNAL_WRITE"
    EXTERNAL_COMMUNICATION = "EXTERNAL_COMMUNICATION"
    PRODUCTION_CHANGE = "PRODUCTION_CHANGE"
    PAYMENT_OR_ORDER = "PAYMENT_OR_ORDER"
    DESTRUCTIVE = "DESTRUCTIVE"


@dataclass(frozen=True)
class ConnectorAccess:
    connector: str
    state: AccessState
    evidence: tuple[str, ...]
    notes: tuple[str, ...] = ()

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.connector.strip():
            errors.append("connector required")
        if not self.evidence and self.state not in {AccessState.UNKNOWN, AccessState.BLOCKED}:
            errors.append("non-unknown access state requires evidence")
        return tuple(errors)


@dataclass(frozen=True)
class AuthorityDecision:
    allowed: bool
    exact_approval_required: bool
    reasons: tuple[str, ...]


def decide_authority(access: ConnectorAccess, action: ActionClass) -> AuthorityDecision:
    """Translate live connector evidence into a NEXUS execution boundary.

    Connector capability is never execution authority. Reads are allowed only when access is
    live-verified. Internal reversible writes may be prepared/executed only on a verified write
    path; consequential actions always require exact human approval even if the connector itself
    exposes a write API.
    """
    errors = access.validate()
    if errors:
        return AuthorityDecision(False, False, errors)

    if action is ActionClass.READ:
        if access.state in {
            AccessState.READ_VERIFIED,
            AccessState.WRITE_CAPABLE_UNTESTED,
            AccessState.WRITE_VERIFIED,
            AccessState.LIMITED,
        }:
            return AuthorityDecision(True, False, ("live read path available",))
        return AuthorityDecision(False, False, ("read access is not live-verified",))

    if action is ActionClass.INTERNAL_WRITE:
        if access.state is AccessState.WRITE_VERIFIED:
            return AuthorityDecision(True, False, ("verified reversible internal write path",))
        if access.state is AccessState.WRITE_CAPABLE_UNTESTED:
            return AuthorityDecision(False, False, ("write capability exists but has not been safely verified",))
        return AuthorityDecision(False, False, ("write access unavailable or insufficiently verified",))

    if action in {
        ActionClass.EXTERNAL_COMMUNICATION,
        ActionClass.PRODUCTION_CHANGE,
        ActionClass.PAYMENT_OR_ORDER,
        ActionClass.DESTRUCTIVE,
    }:
        write_possible = access.state in {AccessState.WRITE_CAPABLE_UNTESTED, AccessState.WRITE_VERIFIED}
        if not write_possible:
            return AuthorityDecision(False, True, ("connector cannot currently support the requested consequential write",))
        return AuthorityDecision(False, True, ("connector capability does not replace exact human approval",))

    return AuthorityDecision(False, False, ("unknown action class",))


def detect_registry_conflicts(entries: Iterable[ConnectorAccess]) -> tuple[str, ...]:
    """Reject contradictory access observations for the same connector."""
    seen: dict[str, AccessState] = {}
    conflicts: list[str] = []
    for entry in entries:
        key = entry.connector.strip().lower()
        previous = seen.get(key)
        if previous is not None and previous != entry.state:
            conflicts.append(f"{entry.connector}: conflicting states {previous.value} vs {entry.state.value}")
        seen[key] = entry.state
    return tuple(conflicts)
