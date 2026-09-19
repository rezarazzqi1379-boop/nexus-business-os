from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EvidenceClass(str, Enum):
    FACT = "FACT"
    CLAIM = "CLAIM"
    ESTIMATE = "ESTIMATE"
    ASSUMPTION = "ASSUMPTION"
    UNKNOWN = "UNKNOWN"


def _utc(value: str, field: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid_{field}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field}_must_include_timezone")
    return parsed.astimezone(timezone.utc).isoformat()


def canonical_digest(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class EventEnvelope:
    event_id: str
    project_id: str
    event_type: str
    source: str
    occurred_at: str
    received_at: str
    payload: dict[str, Any]
    correlation_id: str | None = None
    schema_version: str = "nexus.event.v1"

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "EventEnvelope":
        required = ("event_id", "project_id", "event_type", "source", "occurred_at", "received_at", "payload")
        missing = [name for name in required if name not in value]
        if missing:
            raise ValueError("missing_event_fields:" + ",".join(missing))
        if value.get("schema_version", "nexus.event.v1") != "nexus.event.v1":
            raise ValueError("unsupported_event_schema")
        for name in ("event_id", "project_id", "event_type", "source"):
            if not isinstance(value[name], str) or not value[name].strip():
                raise ValueError(f"invalid_{name}")
        if not isinstance(value["payload"], dict):
            raise ValueError("invalid_payload")
        return cls(
            event_id=value["event_id"].strip(), project_id=value["project_id"].strip(),
            event_type=value["event_type"].strip(), source=value["source"].strip(),
            occurred_at=_utc(value["occurred_at"], "occurred_at"),
            received_at=_utc(value["received_at"], "received_at"), payload=value["payload"],
            correlation_id=value.get("correlation_id"), schema_version="nexus.event.v1",
        )

    @property
    def digest(self) -> str:
        return canonical_digest({
            "schema_version": self.schema_version, "event_id": self.event_id,
            "project_id": self.project_id, "event_type": self.event_type,
            "source": self.source, "occurred_at": self.occurred_at,
            "received_at": self.received_at, "correlation_id": self.correlation_id,
            "payload": self.payload,
        })


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    project_id: str
    classification: EvidenceClass
    statement: str
    source_ref: str
    observed_at: str
    confidence: float

    def __post_init__(self) -> None:
        if not all((self.evidence_id.strip(), self.project_id.strip(), self.statement.strip())):
            raise ValueError("invalid_evidence_identity")
        if not self.source_ref.strip() and self.classification is EvidenceClass.FACT:
            raise ValueError("fact_requires_source")
        if isinstance(self.confidence, bool) or not 0 <= self.confidence <= 1:
            raise ValueError("invalid_confidence")
        _utc(self.observed_at, "observed_at")

