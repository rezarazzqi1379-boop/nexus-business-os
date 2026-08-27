from datetime import datetime, timezone
from pathlib import Path

import pytest

from nexus_brain.provider_policy_evidence import load_policy_evidence
from nexus_brain.provider_registry import load_provider_registry
from nexus_brain.resource_router import ResourceRouter, RoutingRequest

EVIDENCE = Path("data/operational/ai_provider_policy_evidence_v0.1.json")
REGISTRY = Path("data/operational/ai_provider_registry_v0.2.json")
NOW = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


def test_policy_evidence_is_fresh_unique_and_source_bound():
    records = load_policy_evidence(EVIDENCE, max_age_days=30, now=NOW)
    assert len(records) == 4
    assert len({record.provider_id for record in records}) == 4
    assert all(record.source_urls for record in records)
    assert all(record.production_approved is False for record in records)


def test_policy_evidence_staleness_fails_closed():
    with pytest.raises(ValueError, match="policy_review_stale"):
        load_policy_evidence(EVIDENCE, max_age_days=1, now=datetime(2026, 9, 5, tzinfo=timezone.utc))


def test_reviewed_registry_routes_public_text_but_never_internal():
    router = ResourceRouter(load_provider_registry(REGISTRY))
    public = router.route(RoutingRequest(capability="text", sensitivity="public"))
    assert public.allowed is True
    assert public.provider_id in {"cloudflare_workers_ai", "openrouter_free", "google_ai_studio"}
    internal = router.route(RoutingRequest(capability="text", sensitivity="internal"))
    assert internal.allowed is False
    assert internal.provider_id is None


def test_production_still_fails_closed_for_all_reviewed_providers():
    router = ResourceRouter(load_provider_registry(REGISTRY))
    decision = router.route(RoutingRequest(capability="text", sensitivity="public", production=True))
    assert decision.allowed is False
    assert decision.provider_id is None


def test_vercel_gateway_is_public_shadow_candidate_only():
    router = ResourceRouter(load_provider_registry(REGISTRY))
    decision = router.route(RoutingRequest(
        capability="multi_provider",
        sensitivity="public",
        require_openai_compatible=True,
    ))
    assert decision.allowed is True
    assert decision.provider_id == "vercel_ai_gateway"
