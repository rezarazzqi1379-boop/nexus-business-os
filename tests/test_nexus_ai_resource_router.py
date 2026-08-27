from pathlib import Path

from nexus_brain.provider_registry import load_provider_registry
from nexus_brain.resource_router import (
    ResourceRouter,
    RoutingRequest,
    discovery_promotion_allowed,
    normalize_freellm_record,
)


REGISTRY = Path("data/operational/ai_provider_registry_v0.1.json")


def router():
    return ResourceRouter(load_provider_registry(REGISTRY))


def test_registry_is_unique_and_loadable():
    providers = load_provider_registry(REGISTRY)
    ids = [provider.id for provider in providers]
    assert providers
    assert len(ids) == len(set(ids))


def test_public_multi_provider_prefers_verified_gateway():
    decision = router().route(RoutingRequest(capability="multi_provider", sensitivity="public"))
    assert decision.allowed is True
    assert decision.provider_id == "vercel_ai_gateway"


def test_confidential_company_data_fails_closed():
    decision = router().route(RoutingRequest(capability="text", sensitivity="confidential"))
    assert decision.allowed is False
    assert decision.provider_id is None


def test_unverified_provider_is_not_routed_by_default():
    decision = router().route(
        RoutingRequest(capability="code", sensitivity="public", require_openai_compatible=True)
    )
    assert decision.allowed is False
    assert any(item.startswith("cerebras:") for item in decision.alternatives)


def test_freellm_discovery_claim_cannot_self_promote():
    record = normalize_freellm_record("Example Provider", "1000 requests/day")
    assert record.authority == "DISCOVERY_ONLY"
    assert discovery_promotion_allowed(record, official_source_verified=False) is False
    assert discovery_promotion_allowed(record, official_source_verified=True) is True


def test_unknown_sensitivity_fails_closed():
    decision = router().route(RoutingRequest(capability="text", sensitivity="secret-plus"))
    assert decision.allowed is False


def test_production_does_not_use_experiment_only_free_router():
    decision = router().route(
        RoutingRequest(capability="text", sensitivity="public", production=True)
    )
    assert decision.provider_id != "openrouter_free"
