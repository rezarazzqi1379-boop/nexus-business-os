from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ModelResponse:
    response_id: str
    output_text: str
    input_tokens: int
    output_tokens: int


Transport = Callable[[urllib.request.Request, float], dict]


def _default_transport(request: urllib.request.Request, timeout: float) -> dict:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        safe_body = exc.read(2048).decode("utf-8", errors="replace")
        raise RuntimeError(f"openai_http_{exc.code}:{safe_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("openai_network_error") from exc


def _extract_output_text(payload: dict) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct:
        return direct
    chunks: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    if not chunks:
        raise RuntimeError("openai_response_missing_text")
    return "\n".join(chunks)


class ResponsesClient:
    def __init__(self, *, api_key: str | None = None, model: str | None = None,
                 transport: Transport | None = None, timeout: float = 60) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("missing_openai_api_key")
        self.model = model or os.getenv("NEXUS_MODEL", "gpt-5.6-luna")
        self.transport = transport or _default_transport
        self.timeout = timeout

    def run(self, *, instructions: str, input_text: str) -> ModelResponse:
        body = json.dumps({"model": self.model, "instructions": instructions, "input": input_text}).encode()
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=body,
            method="POST",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        payload = self.transport(request, self.timeout)
        usage = payload.get("usage") or {}
        return ModelResponse(
            response_id=str(payload.get("id", "")),
            output_text=_extract_output_text(payload),
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
        )

