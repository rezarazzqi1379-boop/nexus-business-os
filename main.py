from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from state import EventRecord, EventStore


ROOT = Path(__file__).resolve().parent
STORE = EventStore(Path(os.getenv("NEXUS_STATE_DB", ROOT / "data" / "state.db")))


def run_payload(payload: dict) -> str:
    import asyncio
    from agent import process_event

    event = EventRecord(
        event_id=str(payload["event_id"]),
        project=str(payload["project"]),
        event_type=str(payload["event_type"]),
        payload=dict(payload.get("payload", {})),
    )
    return asyncio.run(process_event(STORE, event))


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: dict | str) -> None:
        encoded = json.dumps(body, ensure_ascii=False).encode() if isinstance(body, dict) else body.encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send(200, {"status": "ok", "service": "nexus-autopilot", "model_client": "responses_api"})
        else:
            self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/events":
            self._send(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 262_144:
                raise ValueError("invalid_body_size")
            payload = json.loads(self.rfile.read(length))
            self._send(200, run_payload(payload))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})

    def log_message(self, *_: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="JSON event file")
    args = parser.parse_args()
    if args.input:
        print(run_payload(json.loads(Path(args.input).read_text(encoding="utf-8"))))
        return
    port = int(os.getenv("PORT", "8421"))
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
