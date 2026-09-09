from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable


class EvidenceClass(str, Enum):
    FACT = "FACT"
    MEASUREMENT = "MEASUREMENT"
    CLAIM = "CLAIM"
    ESTIMATE = "ESTIMATE"
    ASSUMPTION = "ASSUMPTION"
    HYPOTHESIS = "HYPOTHESIS"
    UNKNOWN = "UNKNOWN"


class ConnectorState(str, Enum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


class Gate(str, Enum):
    SAFE = "SAFE"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class ApprovalScope:
    approval_id: str
    action_type: str
    recipient: str
    destination: str
    content_digest: str
    attachments_digest: str
    version: str

    def is_complete(self) -> bool:
        return all(
            value.strip()
            for value in (
                self.approval_id,
                self.action_type,
                self.recipient,
                self.destination,
                self.content_digest,
                self.attachments_digest,
                self.version,
            )
        )


@dataclass(frozen=True)
class ConnectorManifest:
    connector_id: str
    system: str
    authority_scope: tuple[str, ...]
    project_scope: tuple[str, ...]
    read_capable: bool
    write_capable: bool
    freshness_seconds: int
    credential_locator: str | None = None

    def __post_init__(self) -> None:
        if not self.connector_id or not self.system:
            raise ValueError("connector_identity_required")
        if self.freshness_seconds <= 0:
            raise ValueError("freshness_must_be_positive")
        if self.credential_locator and any(
            marker in self.credential_locator.casefold()
            for marker in ("password=", "token=", "secret=", "api_key=")
        ):
            raise ValueError("credential_value_forbidden_use_locator_only")


@dataclass(frozen=True)
class ConnectorSnapshot:
    connector_id: str
    observed_at: str
    state: ConnectorState
    source_revision: str | None = None
    error_code: str | None = None


@dataclass(frozen=True)
class EvidenceEnvelope:
    evidence_id: str
    connector_id: str
    project_id: str
    semantic_key: str
    value: Any
    classification: EvidenceClass
    source_locator: str
    observed_at: str
    source_revision: str | None = None
    supersedes: tuple[str, ...] = ()

    @property
    def value_digest(self) -> str:
        normalized = json.dumps(self.value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone_required")
    return parsed.astimezone(timezone.utc)


class ConnectorControlPlane:
    """Builds a fail-closed, project-isolated preflight for each chat/task.

    This class stores no credentials and performs no remote writes. Connector
    adapters provide bounded manifests, health snapshots and evidence envelopes.
    """

    def __init__(self, manifests: Iterable[ConnectorManifest]):
        items = list(manifests)
        self.manifests = {item.connector_id: item for item in items}
        if len(self.manifests) != len(items):
            raise ValueError("duplicate_connector_id")

    def preflight(
        self,
        *,
        project_id: str,
        snapshots: Iterable[ConnectorSnapshot],
        evidence: Iterable[EvidenceEnvelope],
        required_connectors: Iterable[str] = (),
        now: str | None = None,
        external_action_requested: bool = False,
        exact_approval: ApprovalScope | None = None,
    ) -> dict[str, Any]:
        if not project_id:
            raise ValueError("project_id_required")
        observed_now = _parse_time(now or datetime.now(timezone.utc).isoformat())
        snapshot_items = list(snapshots)
        snapshot_map = {item.connector_id: item for item in snapshot_items}
        required = sorted(set(required_connectors))
        findings: list[dict[str, Any]] = []

        if len(snapshot_map) != len(snapshot_items):
            findings.append(self._finding("DUPLICATE_CONNECTOR_SNAPSHOT", "BLOCK", "snapshots"))

        for connector_id in required:
            manifest = self.manifests.get(connector_id)
            snapshot = snapshot_map.get(connector_id)
            if manifest is None:
                findings.append(self._finding("UNKNOWN_CONNECTOR", "BLOCK", connector_id))
                continue
            if not manifest.read_capable:
                findings.append(self._finding("REQUIRED_CONNECTOR_NOT_READ_CAPABLE", "BLOCK", connector_id))
            if project_id not in manifest.project_scope and "*" not in manifest.project_scope:
                findings.append(self._finding("PROJECT_SCOPE_DENIED", "BLOCK", connector_id))
            if snapshot is None or snapshot.state is ConnectorState.UNAVAILABLE:
                findings.append(self._finding("REQUIRED_CONNECTOR_UNAVAILABLE", "BLOCK", connector_id))
                continue
            age = (observed_now - _parse_time(snapshot.observed_at)).total_seconds()
            if age < 0:
                findings.append(self._finding("SNAPSHOT_FROM_FUTURE", "BLOCK", connector_id))
            elif age > manifest.freshness_seconds:
                findings.append(self._finding("STALE_CONNECTOR_SNAPSHOT", "BLOCK", connector_id))
            elif snapshot.state is ConnectorState.DEGRADED:
                findings.append(self._finding("CONNECTOR_DEGRADED", "REVIEW", connector_id))

        evidence_items = list(evidence)
        evidence_ids = [item.evidence_id for item in evidence_items]
        if len(set(evidence_ids)) != len(evidence_ids):
            findings.append(self._finding("DUPLICATE_EVIDENCE_ID", "BLOCK", "evidence"))

        selected: list[EvidenceEnvelope] = []
        for item in evidence_items:
            manifest = self.manifests.get(item.connector_id)
            if manifest is None:
                findings.append(self._finding("EVIDENCE_UNKNOWN_CONNECTOR", "BLOCK", item.evidence_id))
                continue
            if item.project_id != project_id:
                findings.append(self._finding("CROSS_PROJECT_EVIDENCE", "BLOCK", item.evidence_id))
                continue
            if project_id not in manifest.project_scope and "*" not in manifest.project_scope:
                findings.append(self._finding("EVIDENCE_PROJECT_SCOPE_DENIED", "BLOCK", item.evidence_id))
                continue
            evidence_time = _parse_time(item.observed_at)
            evidence_age = (observed_now - evidence_time).total_seconds()
            if evidence_age < 0:
                findings.append(self._finding("EVIDENCE_FROM_FUTURE", "BLOCK", item.evidence_id))
            elif evidence_age > manifest.freshness_seconds:
                findings.append(self._finding("STALE_EVIDENCE", "BLOCK", item.evidence_id))
            source_snapshot = snapshot_map.get(item.connector_id)
            if source_snapshot is None or source_snapshot.state is ConnectorState.UNAVAILABLE:
                findings.append(self._finding("EVIDENCE_SOURCE_UNAVAILABLE", "BLOCK", item.evidence_id))
            selected.append(item)

        active = self._remove_superseded(selected, findings)
        grouped: dict[str, list[EvidenceEnvelope]] = {}
        for item in active:
            grouped.setdefault(item.semantic_key, []).append(item)
        for semantic_key, items in grouped.items():
            digests = {item.value_digest for item in items}
            if len(digests) > 1:
                severity = "BLOCK" if any(
                    item.classification in {EvidenceClass.FACT, EvidenceClass.MEASUREMENT}
                    for item in items
                ) else "REVIEW"
                findings.append(self._finding("CONTRADICTORY_VALUES", severity, semantic_key))

        if external_action_requested and (exact_approval is None or not exact_approval.is_complete()):
            findings.append(self._finding("EXACT_APPROVAL_REQUIRED", "BLOCK", "external_action"))

        gate = Gate.SAFE
        if any(item["severity"] == "BLOCK" for item in findings):
            gate = Gate.BLOCK
        elif findings:
            gate = Gate.REVIEW

        return {
            "schema_version": "nexus.connector-preflight.v1",
            "project_id": project_id,
            "generated_at": observed_now.isoformat(),
            "gate": gate.value,
            "external_action_authorized": bool(
                external_action_requested and exact_approval is not None
                and exact_approval.is_complete() and gate is not Gate.BLOCK
            ),
            "required_connectors": required,
            "evidence_count": len(active),
            "evidence_digests": {item.evidence_id: item.value_digest for item in active},
            "findings": findings,
            "chat_bootstrap": {
                "must_recover_before_answer": True,
                "fail_closed": True,
                "project_isolation": project_id,
                "allowed_without_approval": ["read", "analyze", "draft", "test"],
                "blocked_without_exact_approval": ["send", "publish", "pay", "sign", "deploy", "delete"],
            },
        }

    @staticmethod
    def _remove_superseded(
        evidence: list[EvidenceEnvelope], findings: list[dict[str, Any]]
    ) -> list[EvidenceEnvelope]:
        ids = {item.evidence_id for item in evidence}
        by_id = {item.evidence_id: item for item in evidence}
        superseded: set[str] = set()
        for item in evidence:
            for previous in item.supersedes:
                if previous not in ids:
                    findings.append(ConnectorControlPlane._finding(
                        "SUPERSESSION_TARGET_MISSING", "REVIEW", previous
                    ))
                    continue
                target = by_id[previous]
                if target.semantic_key != item.semantic_key:
                    findings.append(ConnectorControlPlane._finding(
                        "INVALID_CROSS_KEY_SUPERSESSION", "BLOCK", previous
                    ))
                    continue
                if previous == item.evidence_id or item.evidence_id in target.supersedes:
                    findings.append(ConnectorControlPlane._finding(
                        "SUPERSESSION_CYCLE", "BLOCK", previous
                    ))
                    continue
                superseded.add(previous)
        return [item for item in evidence if item.evidence_id not in superseded]

    @staticmethod
    def _finding(code: str, severity: str, subject: str) -> dict[str, str]:
        return {"code": code, "severity": severity, "subject": subject}

    def export_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": "nexus.connector-manifest.v1",
            "connectors": [asdict(self.manifests[key]) for key in sorted(self.manifests)],
        }
