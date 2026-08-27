from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class PolicyEvidence:
    provider_id: str
    policy_verified: bool
    max_sensitivity: str
    production_approved: bool
    decision: str
    source_urls: tuple[str, ...]


def load_policy_evidence(path: str | Path, *, max_age_days: int = 30, now: datetime | None = None) -> tuple[PolicyEvidence, ...]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "nexus.provider-policy-evidence.v1":
        raise ValueError("unsupported_policy_evidence_schema")
    reviewed = datetime.fromisoformat(payload["reviewed_at"].replace("Z", "+00:00"))
    if reviewed.tzinfo is None:
        raise ValueError("policy_review_requires_timezone")
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    age_days = (current - reviewed.astimezone(timezone.utc)).total_seconds() / 86400
    if age_days < 0:
        raise ValueError("policy_review_from_future")
    if age_days > max_age_days:
        raise ValueError("policy_review_stale")

    out: list[PolicyEvidence] = []
    seen: set[str] = set()
    for row in payload.get("providers", []):
        pid = row["id"]
        if pid in seen:
            raise ValueError("duplicate_policy_evidence")
        seen.add(pid)
        urls = tuple(
            value for key, value in row.items()
            if key.endswith("_evidence") and isinstance(value, str) and value.startswith("https://")
        )
        if row.get("policy_verified") and not urls:
            raise ValueError(f"verified_policy_without_official_evidence:{pid}")
        if row.get("production_approved"):
            raise ValueError(f"production_approval_not_permitted_in_research_evidence:{pid}")
        out.append(PolicyEvidence(
            provider_id=pid,
            policy_verified=bool(row.get("policy_verified", False)),
            max_sensitivity=row.get("max_sensitivity", "public"),
            production_approved=False,
            decision=row.get("decision", "UNKNOWN"),
            source_urls=urls,
        ))
    return tuple(out)
