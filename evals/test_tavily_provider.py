from __future__ import annotations

import io
import json
import urllib.error

import pytest

from tavily_provider import (
    MAX_QUERY_BYTES,
    MAX_RESPONSE_RESULTS,
    MAX_RESULTS,
    TAVILY_SEARCH_URL,
    TavilySearchProvider,
    _default_transport,
)


class FakeTransport:
    def __init__(self, response=None, error=None):
        self.response, self.error, self.request, self.timeout = response, error, None, None

    def __call__(self, request, timeout):
        self.request, self.timeout = request, timeout
        if self.error:
            raise self.error
        return self.response


def test_protocol_shape_and_fixed_endpoint() -> None:
    tx = FakeTransport({"results": [{"title": "t", "url": "https://example.test/x", "content": "c"}]})
    provider = TavilySearchProvider(api_key="canary", transport=tx)
    assert provider.search("query", max_results=1)[0].title == "t"
    assert provider.experiment_only and not provider.production_approved
    assert tx.request.full_url == TAVILY_SEARCH_URL
    assert json.loads(tx.request.data)["api_key"] == "canary"


@pytest.mark.parametrize("timeout", [0, -1, 61, float("inf"), float("nan"), True, "20"])
def test_timeout_is_positive_finite_and_bounded(timeout) -> None:
    with pytest.raises(ValueError, match="invalid_tavily_timeout"):
        TavilySearchProvider(api_key="x", transport=FakeTransport({"results": []}), timeout=timeout)


def test_query_byte_limit_and_result_limit() -> None:
    provider = TavilySearchProvider(api_key="x", transport=FakeTransport({"results": []}))
    with pytest.raises(ValueError, match="query_too_large"):
        provider.search("é" * (MAX_QUERY_BYTES // 2 + 1), max_results=1)
    for bad in (0, MAX_RESULTS + 1, True, 1.5):
        with pytest.raises(ValueError, match="invalid_tavily_max_results"):
            provider.search("q", max_results=bad)


def test_malformed_and_oversized_payloads_fail_closed() -> None:
    for payload, code in [
        ([], "invalid_response_shape"),
        ({}, "response_missing_results"),
        ({"results": "bad"}, "response_missing_results"),
        ({"results": ["bad"]}, "malformed_hit"),
        ({"results": [{"title": "x" * 513, "url": "https://e.test", "content": "c"}]}, "invalid_title"),
        ({"results": [{}] * (MAX_RESPONSE_RESULTS + 1)}, "too_many_response_results"),
    ]:
        provider = TavilySearchProvider(api_key="x", transport=FakeTransport(payload))
        with pytest.raises(RuntimeError, match=code):
            provider.search("q", max_results=1)


@pytest.mark.parametrize("error_type", [Exception, RuntimeError, ValueError])
def test_custom_transport_exception_message_is_sanitized(error_type) -> None:
    secret = "canary-secret-value"
    provider = TavilySearchProvider(api_key=secret, transport=FakeTransport(error=error_type(secret)))
    with pytest.raises(RuntimeError) as caught:
        provider.search("q", max_results=1)
    assert str(caught.value) == "tavily_transport_error"
    assert secret not in repr(caught.value)


def test_http_error_body_and_reason_never_leak(monkeypatch) -> None:
    secret = "canary-secret-value"
    error = urllib.error.HTTPError(
        TAVILY_SEARCH_URL, 401, secret, hdrs={}, fp=io.BytesIO(secret.encode())
    )
    class Opener:
        def open(self, request, timeout):
            raise error
    monkeypatch.setattr("urllib.request.build_opener", lambda *handlers: Opener())
    request = __import__("urllib.request").request.Request(TAVILY_SEARCH_URL, data=b"{}", method="POST")
    with pytest.raises(RuntimeError) as caught:
        _default_transport(request, 2)
    assert str(caught.value) == "tavily_http_401"
    assert secret not in repr(caught.value)


def test_default_transport_blocks_redirect_and_wrong_origin(monkeypatch) -> None:
    request = __import__("urllib.request").request.Request("https://evil.test/search", data=b"{}", method="POST")
    with pytest.raises(RuntimeError, match="egress_policy_blocked"):
        _default_transport(request, 2)

    redirect = urllib.error.HTTPError(TAVILY_SEARCH_URL, 302, "redirect", hdrs={}, fp=io.BytesIO())
    class Opener:
        def open(self, request, timeout):
            raise redirect
    monkeypatch.setattr("urllib.request.build_opener", lambda *handlers: Opener())
    request = __import__("urllib.request").request.Request(TAVILY_SEARCH_URL, data=b"{}", method="POST")
    with pytest.raises(RuntimeError, match="redirect_blocked"):
        _default_transport(request, 2)
