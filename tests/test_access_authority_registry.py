from nexus_core.access_authority_registry import (
    AccessState,
    ActionClass,
    ConnectorAccess,
    decide_authority,
    detect_registry_conflicts,
)


def access(state: AccessState) -> ConnectorAccess:
    return ConnectorAccess("gmail", state, ("live-read-2026-08-28",))


def test_verified_read_can_be_used_without_expanding_authority():
    result = decide_authority(access(AccessState.READ_VERIFIED), ActionClass.READ)
    assert result.allowed is True
    assert result.exact_approval_required is False


def test_write_capability_is_not_same_as_verified_write():
    result = decide_authority(access(AccessState.WRITE_CAPABLE_UNTESTED), ActionClass.INTERNAL_WRITE)
    assert result.allowed is False
    assert "not been safely verified" in result.reasons[0]


def test_verified_internal_write_can_be_allowed_when_reversible():
    result = decide_authority(access(AccessState.WRITE_VERIFIED), ActionClass.INTERNAL_WRITE)
    assert result.allowed is True
    assert result.exact_approval_required is False


def test_external_message_always_requires_exact_approval_even_with_write_access():
    result = decide_authority(access(AccessState.WRITE_VERIFIED), ActionClass.EXTERNAL_COMMUNICATION)
    assert result.allowed is False
    assert result.exact_approval_required is True


def test_production_change_always_requires_exact_approval():
    result = decide_authority(access(AccessState.WRITE_VERIFIED), ActionClass.PRODUCTION_CHANGE)
    assert result.allowed is False
    assert result.exact_approval_required is True


def test_payment_or_order_always_requires_exact_approval():
    result = decide_authority(access(AccessState.WRITE_VERIFIED), ActionClass.PAYMENT_OR_ORDER)
    assert result.allowed is False
    assert result.exact_approval_required is True


def test_blocked_connector_cannot_be_treated_as_readable():
    blocked = ConnectorAccess("apollo", AccessState.BLOCKED, (), ("401 invalid credentials",))
    result = decide_authority(blocked, ActionClass.READ)
    assert result.allowed is False


def test_conflicting_access_observations_are_detected():
    entries = [
        ConnectorAccess("drive", AccessState.READ_VERIFIED, ("r1",)),
        ConnectorAccess("drive", AccessState.BLOCKED, ()),
    ]
    conflicts = detect_registry_conflicts(entries)
    assert conflicts
    assert "conflicting states" in conflicts[0]


def test_unsubstantiated_non_unknown_state_fails_closed():
    entry = ConnectorAccess("mystery", AccessState.READ_VERIFIED, ())
    result = decide_authority(entry, ActionClass.READ)
    assert result.allowed is False
    assert "requires evidence" in result.reasons[0]
