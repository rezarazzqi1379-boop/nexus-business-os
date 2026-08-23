from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from nexus_control_plane.live_telemetry import TelemetryEvent, TelemetryKind, summarize_telemetry


class TelemetryStoreError(RuntimeError):
    pass


class JsonlTelemetryStore:
    """Append-only local durable telemetry store for shadow/runtime observation.

    This is storage, not execution authority. Duplicate event ids fail closed rather
    than being silently overwritten. Production database integration is deliberately
    out of scope for this primitive.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    @staticmethod
    def _validate(event: TelemetryEvent) -> None:
        try:
            summarize_telemetry((event,))
        except (TypeError, ValueError) as exc:
            raise TelemetryStoreError("invalid telemetry event") from exc

    @staticmethod
    def _encode(event: TelemetryEvent) -> str:
        payload = asdict(event)
        payload["kind"] = event.kind.value
        payload["evidence_refs"] = list(event.evidence_refs)
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _decode(line: str) -> TelemetryEvent:
        try:
            payload = json.loads(line)
            payload["kind"] = TelemetryKind(payload["kind"])
            payload["evidence_refs"] = tuple(payload.get("evidence_refs", ()))
            event = TelemetryEvent(**payload)
            JsonlTelemetryStore._validate(event)
            return event
        except (KeyError, TypeError, ValueError, json.JSONDecodeError, TelemetryStoreError) as exc:
            raise TelemetryStoreError("corrupt telemetry record") from exc

    def read_all(self) -> tuple[TelemetryEvent, ...]:
        if not self.path.exists():
            return ()
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise TelemetryStoreError("telemetry store read failed") from exc
        events = tuple(self._decode(line) for line in lines if line.strip())
        try:
            summarize_telemetry(events)
        except (TypeError, ValueError) as exc:
            raise TelemetryStoreError("telemetry store integrity failure") from exc
        return events

    def append(self, event: TelemetryEvent) -> None:
        self._validate(event)
        existing = self.read_all()
        if any(item.event_id == event.event_id for item in existing):
            raise TelemetryStoreError(f"duplicate telemetry event id: {event.event_id}")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(self._encode(event) + "\n")
                handle.flush()
        except OSError as exc:
            raise TelemetryStoreError("telemetry store append failed") from exc

    def snapshot(self):
        return summarize_telemetry(self.read_all())
