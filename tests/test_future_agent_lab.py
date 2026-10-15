import pytest

from nexus_core.future_agent_lab import FutureCapability, decide, portfolio, ranked_build_queue
from nexus_core.openai_api_adapter import (
    OpenAIAPIConfig,
    build_openai_client,
    live_call_ready,
    redacted_config_snapshot,
)


def test_api_adapter_fails_closed_without_key_and_live_policy():
    config = OpenAIAPIConfig(allow_live_calls=False)
    ready, reasons = live_call_ready(config, {})
    assert ready is False
    assert "OPENAI_API_KEY missing" in reasons
    assert "live API calls are disabled by policy" in reasons
    assert "exact approval-gated executor is not implemented" in reasons


def test_boolean_and_key_cannot_bypass_exact_approval_gate():
    config = OpenAIAPIConfig(allow_live_calls=True)
    env = {"OPENAI_API_KEY": "sk-secret", "NEXUS_OPENAI_MODEL": "test-model"}
    ready, reasons = live_call_ready(config, env)
    assert ready is False
    assert reasons == ("exact approval-gated executor is not implemented",)
    with pytest.raises(RuntimeError, match="exact approval-gated executor is not implemented"):
        build_openai_client(config, env)


def test_api_snapshot_never_returns_raw_key():
    config = OpenAIAPIConfig(allow_live_calls=True)
    snapshot = redacted_config_snapshot(config, {"OPENAI_API_KEY": "sk-secret", "NEXUS_OPENAI_MODEL": "test-model"})
    assert snapshot["api_key_present"] is True
    assert snapshot["model"] == "test-model"
    assert "sk-secret" not in repr(snapshot)


def test_high_leverage_fact_can_build_now():
    item = FutureCapability(
        "X", "x", "NOW", "FACT", "problem", "arch", "accept", "rollback", ("NEXUS_CORE",), 3, 5
    )
    assert decide(item) == "BUILD_NOW"


def test_high_risk_hypothesis_is_deferred():
    item = FutureCapability(
        "X", "x", "LONG", "HYPOTHESIS", "problem", "arch", "accept", "rollback", ("NEXUS_CORE",), 5, 5
    )
    assert decide(item) == "DEFER"


def test_portfolio_preserves_project_scope_and_rollback():
    items = portfolio()
    assert items
    assert all(i.project_refs for i in items)
    assert all(i.rollback for i in items)
    assert all(not i.validate() for i in items)


def test_ranked_queue_prioritizes_build_now():
    queue = ranked_build_queue()
    decisions = [decide(i) for i in queue]
    assert decisions[0] in {"BUILD_NOW", "EXPERIMENT"}
    assert decisions.index("DEFER") >= 0


def test_duplicate_project_refs_invalid():
    item = FutureCapability(
        "X", "x", "NOW", "FACT", "problem", "arch", "accept", "rollback", ("NEXUS_CORE", "NEXUS_CORE"), 1, 1
    )
    assert "duplicate project_refs" in item.validate()


def test_invalid_capability_cannot_be_ranked():
    bad = FutureCapability("", "x", "NOW", "FACT", "problem", "arch", "accept", "rollback", ("NEXUS_CORE",), 1, 1)
    with pytest.raises(ValueError):
        ranked_build_queue((bad,))
