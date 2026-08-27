from nexus_core.omniroute_evaluation import OmniRouteEvidence, assess_omniroute, researched_snapshot


def test_researched_snapshot_is_sandbox_only_before_nexus_controls():
    result = assess_omniroute(researched_snapshot())
    assert result.decision == "SANDBOX_EXPERIMENT"
    assert any("ToS" in item or "compliance" in item for item in result.required_controls)
    assert any("synthetic" in item for item in result.required_controls)


def test_fail_open_guardrail_never_becomes_authorization_boundary():
    result = assess_omniroute(researched_snapshot())
    assert any("authorization boundary" in item for item in result.required_controls)


def test_tos_advisory_requires_nexus_allowlist():
    result = assess_omniroute(researched_snapshot())
    assert any("ToS/compliance allowlist" in item for item in result.required_controls)


def test_missing_core_adapter_surface_rejects():
    base = researched_snapshot()
    bad = OmniRouteEvidence(**{**base.__dict__, "supports_openai_compatible": False})
    assert assess_omniroute(bad).decision == "REJECT"


def test_adapter_ready_still_does_not_self_authorize_production():
    base = researched_snapshot()
    ready = OmniRouteEvidence(**{
        **base.__dict__,
        "exact_provider_allowlist_supported_by_nexus_adapter": True,
        "terms_safe_provider_allowlist_supported_by_nexus_adapter": True,
        "request_response_logging_disabled_by_nexus_adapter": True,
    })
    result = assess_omniroute(ready)
    assert result.decision == "ADOPT_GATEWAY_ADAPTER"
    assert any("separate measured NEXUS Adoption Gate" in reason for reason in result.reasons)


def test_provider_and_model_counts_are_not_authority():
    base = researched_snapshot()
    inflated = OmniRouteEvidence(**{**base.__dict__, "provider_count_claim": 999999, "unique_model_count_claim": 999999})
    result = assess_omniroute(inflated)
    assert result.decision == "SANDBOX_EXPERIMENT"
