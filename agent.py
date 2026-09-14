from __future__ import annotations

import json
from intake import evaluate_event
from nexus_event_preflight import preflight_event
from openai_client import ResponsesClient
from policy import decide_action
from prompt_contract import INSTRUCTIONS
from state import EventRecord, EventStore


async def process_event(store: EventStore, event: EventRecord) -> str:
    if store.begin(event) == "duplicate":
        return json.dumps({"event_id": event.event_id, "status": "duplicate_ignored"})
    preflight = preflight_event(event)
    if preflight["gate"] == "BLOCK":
        store.set_status(event.event_id, "blocked_preflight")
        return json.dumps({
            "event_id": event.event_id,
            "status": "blocked_preflight",
            "preflight": preflight,
        }, ensure_ascii=False)
    requested_action = str(event.payload.get("requested_action", "classify"))
    policy = decide_action(requested_action, approved=preflight["external_action_authorized"])
    intake = evaluate_event(event.project, event.payload)
    envelope = {
        "event_id": event.event_id,
        "project": event.project,
        "event_type": event.event_type,
        "payload": event.payload,
        "preflight": preflight,
        "policy_disposition": policy.disposition,
        "policy_reason": policy.reason,
        "project_status": intake.project.status,
        "intake_disposition": intake.disposition,
        "missing_evidence": intake.missing_evidence,
    }
    try:
        result = ResponsesClient().run(
            instructions=INSTRUCTIONS,
            input_text=json.dumps(envelope, ensure_ascii=False),
        )
    except Exception:
        store.set_status(event.event_id, "retryable_error")
        raise
    store.set_status(event.event_id, "analyzed")
    return result.output_text
