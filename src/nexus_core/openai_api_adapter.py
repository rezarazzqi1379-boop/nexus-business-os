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
    resolved = config.resolve(env)
    reasons: list[str] = []
    if not resolved["api_key_present"]:
        reasons.append("OPENAI_API_KEY missing")
    if not config.allow_live_calls:
        reasons.append("live API calls are disabled by policy")
    return (not reasons, tuple(reasons))


def build_openai_client(config: OpenAIAPIConfig, env: Mapping[str, str] | None = None) -> Any:
    ready, reasons = live_call_ready(config, env)
    if not ready:
        raise RuntimeError("OpenAI live client blocked: " + "; ".join(reasons))
    source = os.environ if env is None else env
    key = source[config.api_key_env]
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - runtime dependency only
        raise RuntimeError("openai package is not installed") from exc
    return OpenAI(api_key=key)


def redacted_config_snapshot(config: OpenAIAPIConfig, env: Mapping[str, str] | None = None) -> dict[str, str | bool]:
    """Safe diagnostic snapshot. Never returns raw credentials."""
    return config.resolve(env)
