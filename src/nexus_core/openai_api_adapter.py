from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Mapping


@dataclass(frozen=True)
class OpenAIAPIConfig:
    api_key_env: str = "OPENAI_API_KEY"
    model_env: str = "NEXUS_OPENAI_MODEL"
    default_model: str = "gpt-5.6-sol"
    allow_live_calls: bool = False
    project_id: str = "NEXUS_CORE"

    def resolve(self, env: Mapping[str, str] | None = None) -> dict[str, str | bool]:
        source = os.environ if env is None else env
        key = source.get(self.api_key_env, "").strip()
        model = source.get(self.model_env, self.default_model).strip() or self.default_model
        return {
            "api_key_present": bool(key),
            "model": model,
            "allow_live_calls": self.allow_live_calls,
            "project_id": self.project_id,
        }


def live_call_ready(config: OpenAIAPIConfig, env: Mapping[str, str] | None = None) -> tuple[bool, tuple[str, ...]]:
    """Report configuration readiness without granting live-call authority.

    The boolean configuration flag is retained for compatibility and diagnostics,
    but it cannot substitute for an exact, single-use approval. Until the adapter
    is wired to the canonical approval store and consumes an approval bound to
    project, model, request digest, and expiry, live execution remains blocked.
    """
    resolved = config.resolve(env)
    reasons: list[str] = []
    if not resolved["api_key_present"]:
        reasons.append("OPENAI_API_KEY missing")
    if not config.allow_live_calls:
        reasons.append("live API calls are disabled by policy")
    reasons.append("exact approval-gated executor is not implemented")
    return (False, tuple(reasons))


def build_openai_client(config: OpenAIAPIConfig, env: Mapping[str, str] | None = None) -> Any:
    ready, reasons = live_call_ready(config, env)
    if not ready:
        raise RuntimeError("OpenAI live client blocked: " + "; ".join(reasons))
    raise RuntimeError("unreachable: live client requires exact approval consumption")


def redacted_config_snapshot(config: OpenAIAPIConfig, env: Mapping[str, str] | None = None) -> dict[str, str | bool]:
    """Safe diagnostic snapshot. Never returns raw credentials."""
    return config.resolve(env)
