from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence
from urllib.parse import urlparse

TrustState = Literal["UNVERIFIED", "REVIEWED", "TRUSTED"]
AccessMode = Literal["READ_ONLY", "WRITE", "EXECUTE"]
BrokerDecision = Literal["REJECT", "REVIEW", "SANDBOX_ELIGIBLE"]


@dataclass(frozen=True)
class MCPCandidate:
    server_id: str
    name: str
    registry_source: str
    repository_url: str
    publisher: str
    trust_state: TrustState
    requested_access: tuple[AccessMode, ...]
    tool_names: tuple[str, ...]
    provenance_verified: bool = False
    schema_reviewed: bool = False
    secrets_required: bool = False
    external_side_effects: bool = False


@dataclass(frozen=True)
class MCPAssessment:
    decision: BrokerDecision
    reasons: tuple[str, ...]


def _https_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except Exception:
        return False
    return parsed.scheme == "https" and bool(parsed.netloc)


def assess_mcp(candidate: MCPCandidate) -> MCPAssessment:
    """Fail-closed preflight for discovered MCP servers.

    This broker only decides whether a server is eligible for a local sandbox review.
    It never connects to the server, grants credentials, or authorizes external actions.
    """
    reasons: list[str] = []
    if not candidate.server_id.strip() or not candidate.name.strip():
        reasons.append("stable server identity is required")
    if not _https_url(candidate.registry_source):
        reasons.append("registry source must be HTTPS")
    if candidate.repository_url and not _https_url(candidate.repository_url):
        reasons.append("repository URL must be HTTPS")
    if not candidate.publisher.strip():
        reasons.append("publisher identity is required")
    if not candidate.tool_names:
        reasons.append("tool schema is empty")
    if len(set(candidate.tool_names)) != len(candidate.tool_names):
        reasons.append("duplicate tool names")
    if not candidate.provenance_verified:
        reasons.append("publisher/repository provenance not verified")
    if not candidate.schema_reviewed:
        reasons.append("tool schema not reviewed")
    if candidate.trust_state == "UNVERIFIED":
        reasons.append("server trust is unverified")

    risky_access = any(mode in {"WRITE", "EXECUTE"} for mode in candidate.requested_access)
    if risky_access:
        reasons.append("write/execute access requires separate exact-scope approval")
    if candidate.secrets_required:
        reasons.append("credential requirement needs isolated least-privilege review")
    if candidate.external_side_effects:
        reasons.append("external side effects require human-gated action policy")

    hard_fail = any(
        text in reasons
        for text in (
            "stable server identity is required",
            "registry source must be HTTPS",
            "repository URL must be HTTPS",
            "publisher identity is required",
            "tool schema is empty",
            "duplicate tool names",
        )
    )
    if hard_fail:
        return MCPAssessment("REJECT", tuple(reasons))

    if reasons:
        return MCPAssessment("REVIEW", tuple(reasons))

    if candidate.trust_state != "TRUSTED" or candidate.requested_access != ("READ_ONLY",):
        return MCPAssessment("REVIEW", ("only trusted read-only candidates are sandbox eligible",))

    return MCPAssessment("SANDBOX_ELIGIBLE", ())


def deduplicate_candidates(candidates: Sequence[MCPCandidate]) -> tuple[MCPCandidate, ...]:
    seen: dict[str, MCPCandidate] = {}
    for item in candidates:
        if item.server_id in seen and seen[item.server_id] != item:
            raise ValueError(f"conflicting MCP candidate identity: {item.server_id}")
        seen[item.server_id] = item
    return tuple(seen[key] for key in sorted(seen))
