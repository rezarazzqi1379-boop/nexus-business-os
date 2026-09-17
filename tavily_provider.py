"""Hardened Tavily search adapter for sandboxed Phase-G experiments.

This module only implements :class:`research_evidence.SearchProvider`.  It does
not register Tavily, approve it for production, or grant network/credential
authority.  Live use remains a separately approved experiment.

The default transport permits exactly one HTTPS origin and blocks redirects.
Callers needing a central egress proxy must inject a policy-enforcing transport;
DNS/IP allow-list enforcement cannot be provided reliably by ``urllib`` here.
"""

from __future__ import annotations

import json
import math
import os
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from typing import Any

from research_evidence import SearchResult

TAVILY_SEARCH_URL = "https://api.tavily.com/search"
MIN_TIMEOUT_SECONDS = 0.1
MAX_TIMEOUT_SECONDS = 60.0
MAX_QUERY_BYTES = 4096
MAX_RESULTS = 20
MAX_RESPONSE_BYTES = 1_000_000
MAX_RESPONSE_RESULTS = 100
MAX_TITLE_CHARS = 512
MAX_URL_CHARS = 2048
MAX_SNIPPET_CHARS = 8_000
MAX_PUBLISHED_AT_CHARS = 128

Transport = Callable[[urllib.request.Request, float], Mapping[str, Any]]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise urllib.error.HTTPError(req.full_url, code, "redirect_blocked", headers, fp)


def _bounded_timeout(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("invalid_tavily_timeout")
    numeric = float(value)
    if not math.isfinite(numeric) or not MIN_TIMEOUT_SECONDS <= numeric <= MAX_TIMEOUT_SECONDS:
        raise ValueError("invalid_tavily_timeout")
    return numeric


def _default_transport(request: urllib.request.Request, timeout: float) -> Mapping[str, Any]:
    """Perform one bounded request; never expose body, URL query, or credential in errors."""
    if request.full_url != TAVILY_SEARCH_URL or request.get_method() != "POST":
        raise RuntimeError("tavily_egress_policy_blocked")
    timeout = _bounded_timeout(timeout)
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            content_type = response.headers.get_content_type()
            if content_type != "application/json":
                raise RuntimeError("tavily_invalid_content_type")
            declared = response.headers.get("Content-Length")
            if declared is not None:
                try:
                    if int(declared) > MAX_RESPONSE_BYTES:
                        raise RuntimeError("tavily_response_too_large")
                except ValueError as exc:
                    raise RuntimeError("tavily_invalid_content_length") from exc
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise RuntimeError("tavily_response_too_large")
    except urllib.error.HTTPError as exc:
        # Deliberately do not read or interpolate the response body/reason.
        if 300 <= exc.code < 400:
            raise RuntimeError("tavily_redirect_blocked") from None
        raise RuntimeError(f"tavily_http_{exc.code}") from None
    except urllib.error.URLError:
        raise RuntimeError("tavily_network_error") from None

    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise RuntimeError("tavily_invalid_json") from None
    if not isinstance(payload, dict):
        raise RuntimeError("tavily_invalid_response_shape")
    return payload


def _bounded_text(value: object, *, field: str, limit: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise RuntimeError(f"tavily_invalid_{field}")
    return value


def _result_from_hit(hit: object) -> SearchResult:
    if not isinstance(hit, dict):
        raise RuntimeError("tavily_malformed_hit")
    title = _bounded_text(hit.get("title"), field="title", limit=MAX_TITLE_CHARS)
    url = _bounded_text(hit.get("url"), field="url", limit=MAX_URL_CHARS)
    snippet = _bounded_text(hit.get("content"), field="snippet", limit=MAX_SNIPPET_CHARS)
    published_at = hit.get("published_date") or None
    if published_at is not None and (
        not isinstance(published_at, str) or len(published_at) > MAX_PUBLISHED_AT_CHARS
    ):
        raise RuntimeError("tavily_invalid_published_at")
    result = SearchResult(title=title, url=url, snippet=snippet, published_at=published_at)
    try:
        result.validate()
    except ValueError:
        raise RuntimeError("tavily_invalid_search_result") from None
    return result


class TavilySearchProvider:
    """Protocol-compatible, EXPERIMENT_ONLY Tavily adapter."""

    provider_id = "tavily"
    experiment_only = True
    production_approved = False

    def __init__(
        self,
        *,
        api_key: str | None = None,
        transport: Transport | None = None,
        timeout: float = 20.0,
    ) -> None:
        key = api_key if api_key is not None else os.getenv("TAVILY_API_KEY", "")
        if not isinstance(key, str) or not key.strip():
            raise RuntimeError("missing_tavily_api_key")
        self._api_key = key
        self._uses_default_transport = transport is None
        self.transport = transport or _default_transport
        self.timeout = _bounded_timeout(timeout)

    def search(self, query: str, *, max_results: int) -> tuple[SearchResult, ...]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("invalid_tavily_query")
        if len(query.encode("utf-8")) > MAX_QUERY_BYTES:
            raise ValueError("tavily_query_too_large")
        if isinstance(max_results, bool) or not isinstance(max_results, int) or not 1 <= max_results <= MAX_RESULTS:
            raise ValueError("invalid_tavily_max_results")

        body = json.dumps(
            {"api_key": self._api_key, "query": query, "max_results": max_results, "include_answer": False},
            separators=(",", ":"),
        ).encode("utf-8")
        request = urllib.request.Request(
            TAVILY_SEARCH_URL,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        try:
            payload = self.transport(request, self.timeout)
        except Exception as exc:
            # Preserve only this module's fixed, sanitized default-transport codes.
            # A custom transport is untrusted even when it raises RuntimeError.
            if self._uses_default_transport and isinstance(exc, (RuntimeError, ValueError)):
                raise
            raise RuntimeError("tavily_transport_error") from None
        if not isinstance(payload, Mapping):
            raise RuntimeError("tavily_invalid_response_shape")
        hits = payload.get("results")
        if not isinstance(hits, list):
            raise RuntimeError("tavily_response_missing_results")
        if len(hits) > MAX_RESPONSE_RESULTS:
            raise RuntimeError("tavily_too_many_response_results")
        return tuple(_result_from_hit(hit) for hit in hits[:max_results])
