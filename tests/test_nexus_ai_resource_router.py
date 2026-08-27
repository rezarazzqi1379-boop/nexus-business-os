from pathlib import Path

from nexus_brain.provider_registry import load_provider_registry
from nexus_brain.resource_router import (
    ProviderRecord,
    ResourceRouter,
    RoutingRequest,
    discovery_promotion_allowed,
    normalize_freellm_record,
)


REGISTRY = Path("data/operational/ai_provider_registry_v0.1.json")


def router():
    return ResourceRouter(load_provider_registry(REGISTRY))


def approved_public_gateway():
    return ResourceRouter((
        ProviderRecord(
            id="approved_gateway",
            status="VERIFIED_CANDIDATE",
            authority="OFFICIAL_DOCS_VERIFIED",
            capabilities=("text", "multi_provider"),
            openai_compatible=True,
            sensitive_data_allowed=False,
            production_role="PUBLIC_ONLY_CANDIDATE",
            free_limit="test fixture",
            data_training="REVIEWED",
            max_sensitivity="public",
            production_approved=False,
            policy_verified=True,
            official_source="https://example.invalid/official",
        ),
    ))


def test_registry_is_unique_and_loadable():
    providers = load_provider_registry(REGISTRY)
    ids = [provider.id for provider in providers]
    assert providers
    assert len(ids) == len(set(ids))


def test_current_registry_fails_closed_until_policy_review_is_recorded():
    decision = router().route(RoutingRequest(capability="text", sensitivity="public"))
    assert decision.allowed is False
    assert decision.provider_id is None
    assert any("policy review incomplete" in item for item in decision.alternatives)


def test_explicitly_policy_verified_public_gateway_can_route_public_work():
    decision = approved_public_gateway().route(
        RoutingRequest(capability="multi_provider", sensitivity="public", require_openai_compatible=True)
    )
    assert decision.allowed is True
    assert decision.provider_id == "approved_gateway"


def test_internal_company_data_fails_closed_by_default():
    decision = approved_public_gateway().route(RoutingRequest(capability="text", sensitivity="internal"))
    assert decision.allowed is False
    assert decision.provider_id is None


def test_confidential_company_data_fails_closed():
    decision = approved_public_gateway().route(RoutingRequest(capability="text", sensitivity="confidential"))
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
    decision = approved_public_gateway().route(RoutingRequest(capability="text", sensitivity="secret-plus"))
    assert decision.allowed is False


def test_production_requires_explicit_approval_even_for_verified_provider():
    decision = approved_public_gateway().route(
        RoutingRequest(capability="text", sensitivity="public", production=True)
    )
    assert decision.allowed is False
    assert decision.provider_id is None
    assert any("not explicitly production-approved" in item for item in decision.alternatives)
