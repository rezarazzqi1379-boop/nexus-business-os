import pytest

from nexus_brain.public_shadow_probe import (
    EXPECTED_TEXT,
    PUBLIC_PROBE_PROMPT,
    build_public_probe_request,
    execute_public_probe,
)


def test_openrouter_request_is_fixed_public_probe_only():
    request = build_public_probe_request("openrouter_free", env={"OPENROUTER_API_KEY": "test-secret"})
    assert request.body["messages"][0]["content"] == PUBLIC_PROBE_PROMPT
    assert EXPECTED_TEXT in PUBLIC_PROBE_PROMPT
    assert request.body["model"] == "openrouter/free"
    assert "test-secret" not in repr(request)


def test_google_request_requires_key_and_uses_fixed_prompt():
    with pytest.raises(ValueError, match="missing_secret_or_account_config:GEMINI_API_KEY"):
        build_public_probe_request("google_ai_studio", env={})
    request = build_public_probe_request("google_ai_studio", env={"GEMINI_API_KEY": "test-secret"})
    assert request.body["contents"][0]["parts"][0]["text"] == PUBLIC_PROBE_PROMPT
    assert "?key=" not in request.url
    assert "test-secret" not in request.url
    assert request.headers["x-goog-api-key"] == "test-secret"
    assert "test-secret" not in repr(request)


def test_cloudflare_request_requires_account_and_token():
    with pytest.raises(ValueError, match="CLOUDFLARE_API_TOKEN"):
        build_public_probe_request("cloudflare_workers_ai", env={})
    with pytest.raises(ValueError, match="CLOUDFLARE_ACCOUNT_ID"):
        build_public_probe_request("cloudflare_workers_ai", env={"CLOUDFLARE_API_TOKEN": "x"})


def test_cloudflare_rejects_non_cf_model():
    with pytest.raises(ValueError, match="invalid_cloudflare_public_probe_model"):
        build_public_probe_request(
            "cloudflare_workers_ai",
            env={
                "CLOUDFLARE_API_TOKEN": "x",
                "CLOUDFLARE_ACCOUNT_ID": "acct",
                "CLOUDFLARE_PUBLIC_PROBE_MODEL": "not-cf-model",
            },
        )


def test_network_gate_is_closed_by_default_even_with_credentials():
    with pytest.raises(PermissionError, match="public_shadow_network_gate_closed"):
        execute_public_probe(
            "openrouter_free",
            env={"OPENROUTER_API_KEY": "test-secret", "NEXUS_PUBLIC_SHADOW_EXECUTE": "1"},
            allow_network=False,
        )


def test_second_gate_is_required():
    with pytest.raises(PermissionError, match="public_shadow_network_gate_closed"):
        execute_public_probe(
            "openrouter_free",
            env={"OPENROUTER_API_KEY": "test-secret"},
            allow_network=True,
        )


def test_unsupported_provider_fails_closed():
    with pytest.raises(ValueError, match="unsupported_public_shadow_provider"):
        build_public_probe_request("unknown", env={})
