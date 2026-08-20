from datetime import datetime, timedelta, timezone

from hypothesis import given, strategies as st

from nexus_core.capability_health import (
    CapabilityHealth,
    capability_can_satisfy,
    diagnose_capability_health,
    validate_capability_health,
)

NOW = datetime(2026, 8, 19, 18, 30, tzinfo=timezone.utc)


def record(**overrides):
    values = {
        "capability_id": "gmail.read",
        "state": "verified_read",
        "checked_at": "2026-08-19T18:00:00+00:00",
        "route_ref": "connector:gmail:list_labels",
        "evidence_ref": "probe:2026-08-19:gmail",
        "proven_access": ("read",),
    }
    values.update(overrides)
    return CapabilityHealth(**values)


def test_verified_read_never_implies_write():
    health = record()
    assert capability_can_satisfy(health, required_access="read", now=NOW) is True
    assert capability_can_satisfy(health, required_access="write", now=NOW) is False


def test_verified_write_requires_explicit_write_proof():
    health = record(state="verified_write", proven_access=("read",))
    assert "verified_write requires explicit write proof" in validate_capability_health(health)


def test_unavailable_capability_cannot_claim_proven_access():
    health = record(state="not_available_here", proven_access=("read",))
    assert "unavailable or unverified capability cannot claim proven access" in validate_capability_health(health)


def test_stale_health_blocks_runtime_use_and_surfaces_warning():
    health = record(checked_at=(NOW - timedelta(hours=7)).isoformat())
    assert capability_can_satisfy(health, required_access="read", now=NOW) is False
    findings = diagnose_capability_health((health,), now=NOW)
    assert any(f.code == "stale_health_check" for f in findings)


def test_future_health_evidence_is_fail_closed():
    health = record(checked_at=(NOW + timedelta(seconds=1)).isoformat())
    assert capability_can_satisfy(health, required_access="read", now=NOW) is False
    assert any(f.code == "future_health_check" and f.severity == "block" for f in diagnose_capability_health((health,), now=NOW))


def test_duplicate_health_records_are_blocking_findings():
    findings = diagnose_capability_health((record(), record()), now=NOW)
    assert any(f.code == "duplicate_health_record" and f.severity == "block" for f in findings)


def test_zotero_style_external_availability_is_not_runtime_access():
    health = record(
        capability_id="zotero.local",
        state="not_available_here",
        route_ref="codex:zotero-local-api",
        evidence_ref="plugin-manager:not-installed-here",
        proven_access=(),
    )
    assert validate_capability_health(health) == []
    assert capability_can_satisfy(health, required_access="read", now=NOW) is False


@given(st.one_of(st.none(), st.integers(), st.lists(st.text()), st.dictionaries(st.text(), st.text())))
def test_malformed_runtime_health_objects_fail_closed(value):
    assert validate_capability_health(value)
    assert capability_can_satisfy(value, required_access="read", now=NOW) is False
