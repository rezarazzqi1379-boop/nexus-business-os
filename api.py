from __future__ import annotations

import os
import sqlite3
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from contracts import EventEnvelope
from console_contract import APP_VERSION, build_console_bootstrap
from business_os import BusinessOSVault
from state import EventRecord, EventStore
from canonical_sources import CanonicalStore, hydrostatic_hold_points
from security import SecurityMiddleware, auth_config_valid, auth_required
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


READINESS_CHECKS = _startup_checks()


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
    """Read-only pilot data. No connector write or approval decision is performed here."""
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
