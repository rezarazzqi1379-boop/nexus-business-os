from __future__ import annotations

import hashlib
import json

from intake import evaluate_event


def build_delegate_packet(event_id: str, project_id: str, payload: dict) -> dict:
    """Create a portable task packet; this function never transmits it."""
    decision = evaluate_event(project_id, payload)
    packet = {
        "schema": "nexus.delegate.v1",
        "event_id": event_id,
        "project": project_id,
        "objective": decision.project.objective,
        "disposition": decision.disposition,
        "missing_evidence": decision.missing_evidence,
        "allowed_action": decision.policy.disposition,
        "constraints": {
            "facts_not_claims": True,
            "external_action_requires_approval": True,
            "do_not_duplicate_outreach": True,
        },
        "payload": payload,
    }
    canonical = json.dumps(packet, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return {**packet, "packet_sha256": hashlib.sha256(canonical.encode()).hexdigest()}

