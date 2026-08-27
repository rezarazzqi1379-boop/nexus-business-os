from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone


PUBLIC_PROBE_PROMPT = "Return exactly this token and nothing else: NEXUS_PUBLIC_PROBE_OK"
EXPECTED_TEXT = "NEXUS_PUBLIC_PROBE_OK"


@dataclass(frozen=True, repr=False)
class ProbeRequest:
    provider_id: str
    url: str
    headers: dict[str, str]
    body: dict

    def __repr__(self) -> str:
        return (
            f"ProbeRequest(provider_id={self.provider_id!r}, url={self.url!r}, "
            "headers=<redacted>, body=<synthetic-public-probe>)"
        )


@dataclass(frozen=True)
class ProbeResult:
    provider_id: str
    observed_at: str
    healthy: bool
    latency_ms: float
    success_rate: float
    eval_score: float
    estimated_cost_usd: float
    sample_count: int
    error: str | None = None


def _required_env(name: str, env: dict[str, str]) -> str:
    value = env.get(name, "").strip()
    if not value:
        raise ValueError(f"missing_secret_or_account_config:{name}")
    return value


def build_public_probe_request(provider_id: str, *, env: dict[str, str] | None = None) -> ProbeRequest:
    """Build a request that contains synthetic public data only.

    This function never performs network I/O. Credentials are read only from the supplied
    environment mapping and are never returned in logs by this module.
    """
    values = dict(os.environ if env is None else env)

    if provider_id == "openrouter_free":
        key = _required_env("OPENROUTER_API_KEY", values)
        return ProbeRequest(
            provider_id=provider_id,
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            body={
                "model": "openrouter/free",
                "messages": [{"role": "user", "content": PUBLIC_PROBE_PROMPT}],
                "temperature": 0,
                "max_tokens": 16,
            },
        )

    if provider_id == "google_ai_studio":
        key = _required_env("GEMINI_API_KEY", values)
        model = values.get("GEMINI_PUBLIC_PROBE_MODEL", "gemini-2.5-flash").strip()
        if not model:
            raise ValueError("missing_public_probe_model")
        return ProbeRequest(
            provider_id=provider_id,
            url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={"x-goog-api-key": key, "Content-Type": "application/json"},
            body={
                "contents": [{"parts": [{"text": PUBLIC_PROBE_PROMPT}]}],
                "generationConfig": {"temperature": 0, "maxOutputTokens": 16},
            },
        )

    if provider_id == "cloudflare_workers_ai":
        token = _required_env("CLOUDFLARE_API_TOKEN", values)
        account_id = _required_env("CLOUDFLARE_ACCOUNT_ID", values)
        model = values.get("CLOUDFLARE_PUBLIC_PROBE_MODEL", "@cf/meta/llama-3.1-8b-instruct").strip()
        if not model.startswith("@cf/"):
            raise ValueError("invalid_cloudflare_public_probe_model")
        return ProbeRequest(
            provider_id=provider_id,
            url=f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            body={"prompt": PUBLIC_PROBE_PROMPT, "max_tokens": 16, "temperature": 0},
        )

    raise ValueError("unsupported_public_shadow_provider")


def _extract_text(provider_id: str, payload: dict) -> str:
    if provider_id == "openrouter_free":
        return str(payload.get("choices", [{}])[0].get("message", {}).get("content", "")).strip()
    if provider_id == "google_ai_studio":
        candidates = payload.get("candidates", [])
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        return "".join(str(part.get("text", "")) for part in parts).strip()
    if provider_id == "cloudflare_workers_ai":
        result = payload.get("result", {})
        if isinstance(result, dict):
            return str(result.get("response", result.get("text", ""))).strip()
    return ""


def execute_public_probe(
    provider_id: str,
    *,
    env: dict[str, str] | None = None,
    allow_network: bool = False,
    timeout_seconds: float = 20.0,
) -> ProbeResult:
    """Execute one bounded synthetic public probe only after two explicit gates.

    Network execution requires both `allow_network=True` and
    `NEXUS_PUBLIC_SHADOW_EXECUTE=1`. This function cannot accept arbitrary prompts or
    company data. Estimated cost remains 0 for the free-shadow lane and must be replaced
    by provider-reported billing evidence before any paid production promotion.
    """
    values = dict(os.environ if env is None else env)
    if not allow_network or values.get("NEXUS_PUBLIC_SHADOW_EXECUTE") != "1":
        raise PermissionError("public_shadow_network_gate_closed")

    request = build_public_probe_request(provider_id, env=values)
    data = json.dumps(request.body).encode("utf-8")
    http_request = urllib.request.Request(request.url, data=data, headers=request.headers, method="POST")
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(http_request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
        latency_ms = (time.perf_counter() - started) * 1000
        payload = json.loads(raw)
        text = _extract_text(provider_id, payload)
        exact = text == EXPECTED_TEXT
        return ProbeResult(
            provider_id=provider_id,
            observed_at=datetime.now(timezone.utc).isoformat(),
            healthy=True,
            latency_ms=latency_ms,
            success_rate=1.0,
            eval_score=1.0 if exact else 0.0,
            estimated_cost_usd=0.0,
            sample_count=1,
            error=None if exact else "unexpected_probe_output",
        )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError) as exc:
        latency_ms = (time.perf_counter() - started) * 1000
        return ProbeResult(
            provider_id=provider_id,
            observed_at=datetime.now(timezone.utc).isoformat(),
            healthy=False,
            latency_ms=latency_ms,
            success_rate=0.0,
            eval_score=0.0,
            estimated_cost_usd=0.0,
            sample_count=1,
            error=type(exc).__name__,
        )
