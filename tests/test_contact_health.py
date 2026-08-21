from datetime import datetime, timezone

import pytest

from nexus_autonomy.contact_health import (
    ContactChannelState,
    SupplierEntityState,
    assess_supplier_channel,
)


def supplier(validity="verified"):
    return SupplierEntityState(
        supplier_id="minetal",
        validity=validity,
        evidence_refs=("web://official-company-page",),
    )


def channel(state="healthy", **overrides):
    data = dict(
        supplier_id="minetal",
        channel_id="info@minetalgroup.com",
        channel_type="email",
        state=state,
        observed_at=datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc),
        evidence_refs=("gmail://delivery-status",),
        failure_reason="mail delivery failed" if state == "failed" else None,
    )
    data.update(overrides)
    return ContactChannelState(**data)


def test_failed_email_does_not_reject_verified_supplier():
    result = assess_supplier_channel(supplier("verified"), channel("failed"))
    assert result.can_research_supplier is True
    assert result.can_use_channel_for_outreach is False
    assert "supplier may remain valid" in result.reason


def test_verified_supplier_does_not_make_unverified_channel_usable():
    result = assess_supplier_channel(supplier("verified"), channel("unverified"))
    assert result.can_use_channel_for_outreach is False


def test_healthy_channel_does_not_override_unverified_supplier():
    result = assess_supplier_channel(supplier("unverified"), channel("healthy"))
    assert result.can_research_supplier is True
    assert result.can_use_channel_for_outreach is False


def test_verified_supplier_and_healthy_channel_are_eligible_but_not_authorized():
    result = assess_supplier_channel(supplier("verified"), channel("healthy"))
    assert result.can_use_channel_for_outreach is True
    assert "subject to normal action approval" in result.reason


def test_rejected_supplier_blocks_even_healthy_channel():
    result = assess_supplier_channel(supplier("rejected"), channel("healthy"))
    assert result.can_research_supplier is False
    assert result.can_use_channel_for_outreach is False


def test_failed_channel_requires_reason():
    with pytest.raises(ValueError):
        channel("failed", failure_reason=None)


def test_channel_timestamp_must_be_timezone_aware():
    with pytest.raises(ValueError):
        channel("healthy", observed_at=datetime(2026, 8, 21, 12, 0))


def test_supplier_channel_mismatch_fails_closed():
    with pytest.raises(ValueError):
        assess_supplier_channel(
            supplier("verified"),
            channel("healthy", supplier_id="other-supplier"),
        )
