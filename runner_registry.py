from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class RunnerStatus(str, Enum):
    APPROVED = "approved"
    EXPERIMENTAL = "experimental"
    BLOCKED = "blocked"


class CapabilityRisk(str, Enum):
    READ = "read"
    WRITE_LOCAL = "write_local"
    EXEC = "exec"
    EXTERNAL = "external"
    PROHIBITED = "prohibited"


_SECRET_PATTERN = re.compile(
    r"(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|Bearer\s+[A-Za-z0-9._~-]{16,})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RunnerManifest:
    runner_id: str
    version: str
    status: RunnerStatus
    local_first: bool
    signed_binary: bool
    open_beta: bool
    known_blockers: tuple[str, ...]
    allowed_capabilities: tuple[CapabilityRisk, ...] = (CapabilityRisk.READ,)


OPENWORKER = RunnerManifest(
    runner_id="openworker",
    version="unverified-latest",
    status=RunnerStatus.EXPERIMENTAL,
    local_first=True,
    signed_binary=False,
    open_beta=True,
    known_blockers=(
        "windows_binary_not_code_signed",
        "untrusted_xlsx_preview_dependency_requires_remediation",
        "live_nexus_compatibility_not_verified",
    ),
)


@dataclass(frozen=True)
class WorkPacket:
    packet_id: str
    project_id: str
    objective: str
    capability: CapabilityRisk
    workspace_subpath: str
    inputs: dict[str, Any]
    approval_id: str | None = None
    schema_version: str = "nexus.runner.v1"

    @property
    def digest(self) -> str:
        body = asdict(self)
        body["capability"] = self.capability.value
        encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()


def validate_runner_packet(packet: WorkPacket, runner: RunnerManifest = OPENWORKER) -> dict[str, Any]:
    if packet.schema_version != "nexus.runner.v1":
        raise ValueError("unsupported_runner_schema")
    if not all((packet.packet_id.strip(), packet.project_id.strip(), packet.objective.strip())):
        raise ValueError("invalid_runner_packet_identity")
    if packet.workspace_subpath.startswith(("/", "\\")) or ".." in packet.workspace_subpath.split("/"):
        raise ValueError("workspace_scope_escape")
    serialized = json.dumps(packet.inputs, ensure_ascii=False)
    if _SECRET_PATTERN.search(serialized):
        raise ValueError("secret_material_forbidden_in_packet")
    if runner.status is RunnerStatus.BLOCKED:
        raise ValueError("runner_blocked")
    if packet.capability not in runner.allowed_capabilities:
        raise ValueError("runner_capability_not_allowed")
    if packet.approval_id:
        raise ValueError("approval_delegation_forbidden")
    return {
        "runner_id": runner.runner_id,
        "packet_digest": packet.digest,
        "disposition": "prepare_only",
        "external_action_authorized": False,
        "nexus_approval_remains_authoritative": True,
    }


@dataclass(frozen=True)
class MCPServerCandidate:
    server_id: str
    provenance: str
    risk: CapabilityRisk
    required_for: tuple[str, ...]
    enabled: bool = False


NEXUS_MCP_BASELINE = (
    MCPServerCandidate("github", "official_or_vendor", CapabilityRisk.READ, ("code_review",)),
    MCPServerCandidate("gmail", "official_or_vendor", CapabilityRisk.READ, ("need_radar",)),
    MCPServerCandidate("notion", "official_or_vendor", CapabilityRisk.READ, ("project_memory",)),
    MCPServerCandidate("hubspot", "official_or_vendor", CapabilityRisk.READ, ("crm_hygiene", "lead_validation")),
    MCPServerCandidate("filesystem", "reference", CapabilityRisk.READ, ("vault",)),
    MCPServerCandidate("playwright", "official_or_vendor", CapabilityRisk.READ, ("ui_verification",)),
)


def activation_plan(candidates: tuple[MCPServerCandidate, ...] = NEXUS_MCP_BASELINE) -> list[dict[str, Any]]:
    return [
        {
            "server_id": item.server_id,
            "enabled": item.enabled,
            "initial_scope": "read_only",
            "risk": item.risk.value,
            "required_for": list(item.required_for),
            "approval_rule": "nexus_exact_scope_gate_for_any_write",
        }
        for item in candidates
    ]
