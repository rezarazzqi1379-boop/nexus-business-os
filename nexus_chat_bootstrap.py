from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from nexus_connector_control_plane import (
    ConnectorControlPlane,
    ConnectorManifest,
    ConnectorSnapshot,
    EvidenceEnvelope,
)


REQUIRED_AUTHORITY_KEYS = ("authority.source_registry", "authority.project_master")


@dataclass(frozen=True)
class ChatIntent:
    chat_id: str
    project_id: str
    consequential: bool = True
    external_action_requested: bool = False
    exact_approval_id: str | None = None


def load_manifests(path: str | Path) -> list[ConnectorManifest]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "nexus.connector-config.v1":
        raise ValueError("unsupported_connector_config")
    return [
        ConnectorManifest(
            connector_id=item["connector_id"],
            system=item["system"],
            authority_scope=tuple(item["authority_scope"]),
            project_scope=tuple(item["project_scope"]),
            read_capable=bool(item["read_capable"]),
            write_capable=bool(item["write_capable"]),
            freshness_seconds=int(item["freshness_seconds"]),
            credential_locator=item.get("credential_locator"),
        )
        for item in payload["connectors"]
    ]


def bootstrap_chat(
    *,
    intent: ChatIntent,
    manifests: Iterable[ConnectorManifest],
    snapshots: Iterable[ConnectorSnapshot],
    evidence: Iterable[EvidenceEnvelope],
    required_connectors: Iterable[str],
    now: str | None = None,
) -> dict[str, Any]:
    evidence_items = list(evidence)
    result = ConnectorControlPlane(manifests).preflight(
        project_id=intent.project_id,
        snapshots=snapshots,
        evidence=evidence_items,
        required_connectors=required_connectors,
        now=now,
        external_action_requested=intent.external_action_requested,
        exact_approval_id=intent.exact_approval_id,
    )
    available_keys = {
        item.semantic_key for item in evidence_items if item.project_id == intent.project_id
    }
    if intent.consequential:
        missing = [key for key in REQUIRED_AUTHORITY_KEYS if key not in available_keys]
        for key in missing:
            result["findings"].append(
                {"code": "REQUIRED_AUTHORITY_MISSING", "severity": "BLOCK", "subject": key}
            )
        if missing:
            result["gate"] = "BLOCK"
            result["external_action_authorized"] = False
    result["chat_id"] = intent.chat_id
    result["instruction_contract"] = (
        "Recover authority and live connector snapshots before consequential work; "
        "isolate project evidence; stop on BLOCK; never treat availability as correctness."
    )
    return result

