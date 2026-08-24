from __future__ import annotations

import base64
import hmac
import os

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

PUBLIC_PATHS = frozenset({"/health", "/ready"})
MAX_REQUEST_BYTES = 1_048_576


def auth_required() -> bool:
    return os.getenv("NEXUS_AUTH_REQUIRED", "1").strip() != "0"


def configured_token() -> str:
    return os.getenv("NEXUS_ACCESS_TOKEN", "")


def auth_config_valid() -> bool:
    return (not auth_required()) or len(configured_token()) >= 32


def _authorized(header: str) -> bool:
    token = configured_token()
    if not token:
        return False
    if header.startswith("Bearer "):
        supplied = header[7:].strip()
    elif header.startswith("Basic "):
        try:
            decoded = base64.b64decode(header[6:], validate=True).decode("utf-8")
            _, supplied = decoded.split(":", 1)
        except (ValueError, UnicodeDecodeError):
            return False
    else:
        return False
    return hmac.compare_digest(supplied, token)


class SecurityMiddleware(BaseHTTPMiddleware):
    @staticmethod
    def _secure(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'"
        return response

    async def dispatch(self, request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH"}:
            content_length = request.headers.get("content-length")
            if content_length is None:
                return self._secure(JSONResponse({"detail": "content_length_required"}, status_code=411))
            try:
                size = int(content_length)
            except ValueError:
                return self._secure(JSONResponse({"detail": "invalid_content_length"}, status_code=400))
            if size < 0 or size > MAX_REQUEST_BYTES:
                return self._secure(JSONResponse({"detail": "request_too_large"}, status_code=413))
        if auth_required() and request.url.path not in PUBLIC_PATHS:
            if not auth_config_valid():
                return self._secure(JSONResponse({"detail": "service_auth_misconfigured"}, status_code=503))
            if not _authorized(request.headers.get("authorization", "")):
                return self._secure(JSONResponse({"detail": "authentication_required"}, status_code=401,
                                                 headers={"WWW-Authenticate": 'Basic realm="NEXUS"'}))
        response = await call_next(request)
        return self._secure(response)
