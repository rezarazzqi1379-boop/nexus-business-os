from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib import request


@dataclass(frozen=True)
class PostHogConfig:
    api_key: str
    host: str
    enabled: bool

    @classmethod
    def from_env(cls) -> "PostHogConfig":
        api_key = os.getenv("POSTHOG_PROJECT_API_KEY", "").strip()
        host = os.getenv("POSTHOG_HOST", "").strip().rstrip("/")
        enabled = os.getenv("NEXUS_POSTHOG_ENABLED", "0").strip() == "1"
        if enabled and (not api_key or not host):
            raise ValueError("PostHog enabled but POSTHOG_PROJECT_API_KEY or POSTHOG_HOST is missing")
        return cls(api_key=api_key, host=host, enabled=enabled)


class PostHogAdapter:
    """Minimal dependency-free analytics adapter.

    Analytics is opt-in and must never authorize, mutate, or influence NEXUS
    approval decisions. Failures are returned to the caller instead of blocking
    the governed execution path.
    """

    def __init__(self, config: PostHogConfig | None = None) -> None:
        self.config = config or PostHogConfig.from_env()

    def status(self) -> dict[str, object]:
        return {
            "enabled": self.config.enabled,
            "configured": bool(self.config.api_key and self.config.host),
            "host": self.config.host if self.config.host else None,
        }

    def capture(self, event: str, distinct_id: str, properties: dict | None = None) -> dict[str, object]:
        if not self.config.enabled:
            return {"sent": False, "reason": "disabled"}
        if not event or not distinct_id:
            raise ValueError("event and distinct_id are required")
        payload = {
            "api_key": self.config.api_key,
            "event": event,
            "properties": {"distinct_id": distinct_id, **(properties or {})},
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.config.host}/capture/",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=3) as response:
                return {"sent": 200 <= response.status < 300, "status": response.status}
        except Exception as exc:  # observability must not break governed execution
            return {"sent": False, "reason": type(exc).__name__}
