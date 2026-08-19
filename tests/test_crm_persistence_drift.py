import pytest

from nexus_core.crm_hygiene import LiveCommercialSignal, detect_persistence_drift


def _signal(key: str, ref: str):
    return LiveCommercialSignal(
        signal_key=key,
        counterparty_key=f"company:{key}",
        project_ref="project:octg",
        evidence_ref=ref,
    )


def test_detects_missing_and_stale_commercial_state_without_writing():
    live = (
        _signal("signal:yedi", "gmail:yedi"),
        _signal("signal:oms", "gmail:oms"),
        _signal("signal:marley", "gmail:marley"),
    )
    result = detect_persistence_drift(live, ("signal:suppliertr", "signal:yedi"))
    assert result.missing_signal_keys == ("signal:marley", "signal:oms")
    assert result.stale_persisted_signal_keys == ("signal:suppliertr",)
    assert result.duplicate_live_signal_keys == ()


def test_duplicate_live_signals_are_reported_not_silently_collapsed():
    live = (_signal("signal:yedi", "gmail:1"), _signal("signal:yedi", "gmail:2"))
    result = detect_persistence_drift(live, ())
    assert result.duplicate_live_signal_keys == ("signal:yedi",)


def test_invalid_or_duplicate_persisted_keys_fail_closed():
    with pytest.raises(ValueError, match="invalid_persisted_signal_key"):
        detect_persistence_drift((), ("",))
    with pytest.raises(ValueError, match="duplicate_persisted_signal_key"):
        detect_persistence_drift((), ("signal:a", "signal:a"))
