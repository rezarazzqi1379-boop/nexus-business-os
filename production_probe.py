from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_BODY_BYTES = 65_536
Transport = Callable[[str, str], tuple[int, dict[str, str], bytes]]


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_base_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("base_url_must_be_public_https")
    if parsed.query or parsed.fragment:
        raise ValueError("base_url_query_or_fragment_forbidden")
    try:
        address = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        address = None
    if parsed.hostname.lower() == "localhost" or (address and not address.is_global):
        raise ValueError("private_or_local_target_forbidden")
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def _http_transport(url: str, accept: str) -> tuple[int, dict[str, str], bytes]:
    opener = build_opener(_NoRedirect())
    request = Request(url, headers={"Accept": accept, "User-Agent": "NEXUS-Production-Probe/1.0"})
    try:
        with opener.open(request, timeout=15) as response:
            return response.status, {key.lower(): value for key, value in response.headers.items()}, response.read(MAX_BODY_BYTES + 1)
    except HTTPError as exc:
        return exc.code, {key.lower(): value for key, value in exc.headers.items()}, exc.read(MAX_BODY_BYTES + 1)


def _json_status(body: bytes, key: str, expected: str) -> bool:
    try:
        return json.loads(body.decode("utf-8")).get(key) == expected
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        return False


def run_probe(base_url: str, transport: Transport | None = None, observed_at: str | None = None) -> dict:
    base = validate_base_url(base_url)
    fetch = transport or _http_transport
    specs = (
        ("health", "/health", "application/json", 200),
        ("ready", "/ready", "application/json", 200),
        ("login", "/login", "text/html", 200),
        ("console_redirect", "/console", "text/html", 303),
        ("api_guard", "/v1/system/diagnostics", "application/json", 401),
    )
    checks = []
    required_headers = ("cache-control", "content-security-policy", "x-content-type-options", "x-frame-options")
    for name, path, accept, expected_status in specs:
        status, headers, body = fetch(urljoin(base + "/", path.lstrip("/")), accept)
        if len(body) > MAX_BODY_BYTES:
            raise ValueError("response_body_too_large")
        semantic_ok = True
        if name == "health":
            semantic_ok = _json_status(body, "status", "ok")
        elif name == "ready":
            semantic_ok = _json_status(body, "status", "ready")
        elif name == "login":
            semantic_ok = b'NEXUS' in body and b'action="/auth/login"' in body
        elif name == "console_redirect":
            semantic_ok = headers.get("location") == "/login?next=/console"
        elif name == "api_guard":
            semantic_ok = _json_status(body, "detail", "authentication_required")
        missing_headers = [header for header in required_headers if header not in headers]
        passed = status == expected_status and semantic_ok and not missing_headers
        checks.append({
            "name": name,
            "path": path,
            "expected_status": expected_status,
            "observed_status": status,
            "semantic_ok": semantic_ok,
            "missing_security_headers": missing_headers,
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "passed": passed,
        })
    return {
        "schema_version": "nexus.production-proof.v1",
        "observed_at": observed_at or datetime.now(timezone.utc).isoformat(),
        "base_url": base,
        "credential_mode": "public-boundary-only",
        "passed": all(item["passed"] for item in checks),
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only NEXUS production boundary proof")
    parser.add_argument("base_url")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    result = run_probe(args.base_url)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
