from __future__ import annotations

import hmac
import os
import sqlite3
import time
import uuid
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from contracts import EventEnvelope
from console_contract import APP_VERSION, build_console_bootstrap
from business_os import BusinessOSVault
from state import EventRecord, EventStore
from canonical_sources import CanonicalStore, hydrostatic_hold_points
from security import (SESSION_COOKIE, SecurityMiddleware, auth_config_valid, auth_required,
                      configured_token, issue_session, session_authorized, session_ttl_seconds)
from intake import evaluate_event


ROOT = Path(__file__).resolve().parent
STORE = EventStore(Path(os.getenv("NEXUS_STATE_DB", ROOT / "data" / "state.db")))
VAULT = BusinessOSVault(Path(os.getenv("NEXUS_VAULT_ROOT", ROOT / "nexus_vault")))
CANONICAL = CanonicalStore(Path(os.getenv("NEXUS_CANONICAL_DB", ROOT / "data" / "canonical.db")))
VAULT.initialize()
UI_ROOT = ROOT / "ui"
app = FastAPI(title="NEXUS Autopilot", version=APP_VERSION)
app.add_middleware(SecurityMiddleware)
app.mount("/assets", StaticFiles(directory=UI_ROOT), name="assets")

LOGIN_WINDOW_SECONDS = 300
LOGIN_MAX_ATTEMPTS = 5
_LOGIN_ATTEMPTS: dict[str, list[float]] = {}


def _startup_checks() -> dict[str, bool]:
    checks = {"auth": auth_config_valid(), "state": False, "canonical": False, "vault": False}
    try:
        with sqlite3.connect(STORE.path) as db:
            checks["state"] = db.execute("SELECT 1").fetchone()[0] == 1
        with sqlite3.connect(CANONICAL.path) as db:
            checks["canonical"] = db.execute("SELECT 1").fetchone()[0] == 1
        probe = VAULT.root / f".readiness-{uuid.uuid4().hex}"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        checks["vault"] = True
    except (OSError, sqlite3.Error):
        pass
    return checks


def _safe_next(value: str) -> str:
    return value if value.startswith("/") and not value.startswith("//") else "/console"


def _login_allowed(client_key: str, now: float) -> bool:
    recent = [stamp for stamp in _LOGIN_ATTEMPTS.get(client_key, []) if now - stamp < LOGIN_WINDOW_SECONDS]
    _LOGIN_ATTEMPTS[client_key] = recent
    return len(recent) < LOGIN_MAX_ATTEMPTS


READINESS_CHECKS = _startup_checks()


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse("/console", status_code=303)


@app.get("/login", include_in_schema=False)
def login_page(request: Request, next: str = "/console", error: str = "") -> HTMLResponse | RedirectResponse:
    if session_authorized(request.cookies.get(SESSION_COOKIE, "")):
        return RedirectResponse(_safe_next(next), status_code=303)
    template = (UI_ROOT / "login.html").read_text(encoding="utf-8")
    error_html = '<p class="error" role="alert">نام کاربری یا رمز دسترسی صحیح نیست.</p>' if error else ""
    page = template.replace("{{ERROR}}", error_html).replace("{{NEXT}}", _safe_next(next))
    return HTMLResponse(page)


@app.post("/auth/login", include_in_schema=False)
async def login(request: Request) -> RedirectResponse:
    client_key = request.client.host if request.client else "unknown"
    now = time.monotonic()
    if not _login_allowed(client_key, now):
        response = RedirectResponse("/login?error=rate_limited", status_code=303)
        response.headers["Retry-After"] = str(LOGIN_WINDOW_SECONDS)
        return response
    body = (await request.body()).decode("utf-8", errors="replace")
    fields = parse_qs(body, keep_blank_values=True)
    password = fields.get("password", [""])[0]
    next_path = _safe_next(fields.get("next", ["/console"])[0])
    if not auth_config_valid() or not hmac.compare_digest(password, configured_token()):
        _LOGIN_ATTEMPTS.setdefault(client_key, []).append(now)
        return RedirectResponse(f"/login?error=invalid&next={next_path}", status_code=303)
    _LOGIN_ATTEMPTS.pop(client_key, None)
    response = RedirectResponse(next_path, status_code=303)
    response.set_cookie(SESSION_COOKIE, issue_session(), max_age=session_ttl_seconds(), httponly=True,
                        secure=True, samesite="strict", path="/")
    return response


@app.post("/auth/logout", include_in_schema=False)
def logout() -> RedirectResponse:
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE, path="/", secure=True, httponly=True, samesite="strict")
    return response


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "nexus-autopilot"}


@app.get("/ready")
def ready() -> dict:
    if not all(READINESS_CHECKS.values()):
        raise HTTPException(status_code=503, detail={"status": "not_ready"})
    return {"status": "ready"}


@app.get("/v1/system/diagnostics")
def diagnostics() -> dict:
    return {"status": "ready" if all(READINESS_CHECKS.values()) else "not_ready",
            "checks": READINESS_CHECKS, "auth_required": auth_required()}


@app.get("/console", include_in_schema=False)
def console() -> FileResponse:
    return FileResponse(UI_ROOT / "index.html")


@app.get("/v1/console/bootstrap")
def console_bootstrap() -> dict:
    payload = build_console_bootstrap()
    payload["vault"] = VAULT.status()
    return payload


@app.get("/v1/vault/status")
def vault_status() -> dict:
    return VAULT.status()


@app.get("/v1/canonical/status")
def canonical_status() -> dict:
    return CANONICAL.status()


@app.get("/v1/workflows/hydrostatic-audit")
def hydrostatic_audit() -> dict:
    try:
        return hydrostatic_hold_points(CANONICAL)
    except KeyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/v1/events", status_code=202)
def ingest_event(body: dict) -> dict:
    try:
        envelope = EventEnvelope.from_dict(body)
        intake = evaluate_event(envelope.project_id, envelope.payload)
        result = STORE.begin(EventRecord(envelope.event_id, envelope.project_id, envelope.event_type, body))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"event_id": envelope.event_id, "event_digest": envelope.digest, "status": result,
            "disposition": intake.disposition, "missing_evidence": list(intake.missing_evidence)}
