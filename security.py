from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
from urllib.parse import quote

from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

PUBLIC_PATHS = frozenset({"/health", "/ready", "/login", "/auth/login", "/assets/login.css"})
MAX_REQUEST_BYTES = 1_048_576
SESSION_COOKIE = "nexus_session"
DEFAULT_SESSION_TTL_SECONDS = 28_800


def auth_required() -> bool:
    return os.getenv("NEXUS_AUTH_REQUIRED", "1").strip() != "0"


def configured_token() -> str:
    return os.getenv("NEXUS_ACCESS_TOKEN", "")


def auth_config_valid() -> bool:
    return (not auth_required()) or len(configured_token()) >= 32


def session_ttl_seconds() -> int:
    raw = os.getenv("NEXUS_SESSION_TTL_SECONDS", str(DEFAULT_SESSION_TTL_SECONDS))
    try:
        return max(300, min(int(raw), 86_400))
    except ValueError:
        return DEFAULT_SESSION_TTL_SECONDS


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


def issue_session(now: int | None = None) -> str:
    token = configured_token()
    if len(token) < 32:
        raise ValueError("service_auth_misconfigured")
    expires = (int(time.time()) if now is None else int(now)) + session_ttl_seconds()
    payload = f"nexus-session-v1:{expires}"
    signature = hmac.new(token.encode("utf-8"), payload.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{expires}.{signature}"


def session_authorized(cookie: str, now: int | None = None) -> bool:
    token = configured_token()
    if not cookie or len(token) < 32:
        return False
    try:
        expiry_text, supplied_signature = cookie.split(".", 1)
        expires = int(expiry_text)
    except (TypeError, ValueError):
        return False
    current = int(time.time()) if now is None else int(now)
    if expires < current or expires > current + session_ttl_seconds() + 60:
        return False
    payload = f"nexus-session-v1:{expires}"
    expected = hmac.new(token.encode("utf-8"), payload.encode("ascii"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(supplied_signature, expected)


class SecurityMiddleware(BaseHTTPMiddleware):
    @staticmethod
    def _secure(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; form-action 'self'; base-uri 'none'"
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
            header_ok = _authorized(request.headers.get("authorization", ""))
            cookie_ok = session_authorized(request.cookies.get(SESSION_COOKIE, ""))
            if not auth_config_valid():
                return self._secure(JSONResponse({"detail": "service_auth_misconfigured"}, status_code=503))
            if not (header_ok or cookie_ok):
                accepts_html = "text/html" in request.headers.get("accept", "")
                if request.method == "GET" and (request.url.path == "/console" or accepts_html):
                    next_path = quote(request.url.path, safe="/")
                    return self._secure(RedirectResponse(f"/login?next={next_path}", status_code=303))
                return self._secure(JSONResponse({"detail": "authentication_required"}, status_code=401,
                                                 headers={"WWW-Authenticate": 'Basic realm="NEXUS"'}))
        response = await call_next(request)
        return self._secure(response)
