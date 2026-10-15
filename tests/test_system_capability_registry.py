from dataclasses import replace

import pytest

from system_capability_registry import CapabilityActivation, activation_payload, activation_registry


def test_registry_never_confuses_local_install_with_live_or_production():
    items = activation_registry()
    tavily = next(x for x in items if x.capability_id == "tavily-search")
    assert not tavily.live_network_enabled
    assert not tavily.production_approved
    assert activation_payload()["live_network_capabilities"] == []


def test_missing_optional_module_is_explicit(monkeypatch):
    monkeypatch.setattr("system_capability_registry._available", lambda module: False)
    assert all(x.state == "UNAVAILABLE" and not x.local_use_enabled for x in activation_registry())


def test_live_network_cannot_be_self_approved():
    item = CapabilityActivation("x", "x", "EXPERIMENT_ONLY", True, True, False, "candidate", "benchmark")
    with pytest.raises(ValueError, match="production"):
        item.validate()
