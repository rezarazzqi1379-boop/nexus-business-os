from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from source_failover import agent_reach_preflight
from typing import Any

from nexus_chat_bootstrap import ChatIntent, bootstrap_chat, load_manifests
from nexus_connector_control_plane import (
    ActionScope,
    ApprovalScope,
    ConnectorSnapshot,
    ConnectorState,
    EvidenceClass,
    EvidenceEnvelope,
)


CONFIG_PATH = Path(__file__).resolve().parent / "config" / "connectors.json"


def _scope(scope_type: type[ActionScope] | type[ApprovalScope], payload: dict[str, Any] | None):
    return scope_type(**payload) if payload is not None else None


def preflight_event(event: Any, *, config_path: str | Path = CONFIG_PATH) -> dict[str, Any]:
    """Convert an event's bounded control context into the mandatory chat preflight.

    Missing or malformed context fails closed before any model call. Provider
    credentials and raw message bodies are deliberately outside this contract.
    """
    control = event.payload.get("_nexus_preflight")
    if not isinstance(control, dict):
        return {
            "schema_version": "nexus.connector-preflight.v1",
            "project_id": event.project,
            "chat_id": event.event_id,
            "gate": "BLOCK",
            "external_action_authorized": False,
            "findings": [{
                "code": "PREFLIGHT_CONTEXT_MISSING",
                "severity": "BLOCK",
                "subject": event.event_id,
            }],
        }
    try:
        snapshots = [
            ConnectorSnapshot(
                connector_id=item["connector_id"],
                observed_at=item["observed_at"],
                state=ConnectorState(item["state"]),
                source_revision=item.get("source_revision"),
                error_code=item.get("error_code"),
            )
            for item in control.get("snapshots", [])
        ]
        evidence = [
            EvidenceEnvelope(
                evidence_id=item["evidence_id"],
                connector_id=item["connector_id"],
                project_id=item["project_id"],
                semantic_key=item["semantic_key"],
                value=item["value"],
                classification=EvidenceClass(item["classification"]),
                source_locator=item["source_locator"],
                observed_at=item["observed_at"],
                source_revision=item.get("source_revision"),
                supersedes=tuple(item.get("supersedes", [])),
            )
            for item in control.get("evidence", [])
        ]
        intent = ChatIntent(
            chat_id=str(control.get("chat_id", event.event_id)),
            project_id=event.project,
            consequential=bool(control.get("consequential", True)),
            external_action_requested=bool(control.get("external_action_requested", False)),
            requested_action=_scope(ActionScope, control.get("requested_action")),
            exact_approval=_scope(ApprovalScope, control.get("exact_approval")),
        )
        result = bootstrap_chat(
            intent=intent,
            manifests=load_manifests(config_path),
            snapshots=snapshots,
            evidence=evidence,
            required_connectors=control.get("required_connectors", []),
            now=control.get("now"),
        )
        acquisition = control.get("acquisition")
        if acquisition is None:
            result["acquisition"] = {"route": "disabled", "reason": "explicit_acquisition_context_required"}
            return result
        if not isinstance(acquisition, dict):
            raise ValueError("invalid_acquisition_context")
        if acquisition.get("project_id", event.project) != event.project:
            raise ValueError("acquisition_project_mismatch")
        decision = agent_reach_preflight(
            project_id=event.project,
            lane_id=acquisition["lane_id"],
            needs_external_evidence=acquisition["needs_external_evidence"],
            sensitivity=acquisition["sensitivity"],
            native_available=acquisition["native_available"],
            cache_fresh=acquisition["cache_fresh"],
            reach_healthy=acquisition["reach_healthy"],
            health_age_seconds=acquisition["health_age_seconds"],
            remaining_queries=acquisition["remaining_queries"],
        )
        result["acquisition"] = asdict(decision)
        if decision.route == "agent_reach" and not (
            acquisition.get("health_evidence_ref") and
            acquisition.get("health_measurement_kind") == "live_read"
        ):
            result["acquisition"].update(route="blocked", reason="live_read_health_proof_required")
        if result["acquisition"]["route"] == "blocked":
            result["gate"] = "BLOCK"
            result["external_action_authorized"] = False
            result.setdefault("findings", []).append({
                "code": "ACQUISITION_BLOCKED", "severity": "BLOCK",
                "subject": result["acquisition"]["reason"],
            })
        return result
    except (KeyError, TypeError, ValueError) as exc:
        return {
            "schema_version": "nexus.connector-preflight.v1",
            "project_id": event.project,
            "chat_id": event.event_id,
            "gate": "BLOCK",
            "external_action_authorized": False,
            "findings": [{
                "code": "PREFLIGHT_CONTEXT_INVALID",
                "severity": "BLOCK",
                "subject": type(exc).__name__,
            }],
        }
