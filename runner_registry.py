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
    sandbox_required: bool = False
    network_allowed: bool = False
    can_receive_secrets: bool = False


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


HERDR = RunnerManifest(
    runner_id="herdr",
    version="0.8.2",
    status=RunnerStatus.EXPERIMENTAL,
    local_first=True,
    signed_binary=False,
    open_beta=False,
    known_blockers=(
        "live_nexus_compatibility_not_verified",
        "windows_plugins_are_preview",
        "agent_state_detection_can_fall_back_to_idle",
        "requires_owner_managed_machine_or_remote_host",
    ),
)


# OpenCode is intentionally registered as an experimental shadow worker, not an authority.
# It may prepare/rewrite/test code only inside an explicitly scoped sandbox packet. It cannot
# receive NEXUS approvals, secrets, network authority, or any external-action capability.
OPENCODE_SHADOW = RunnerManifest(
    runner_id="opencode",
    version="unverified-latest",
    status=RunnerStatus.EXPERIMENTAL,
    local_first=True,
    signed_binary=False,
    open_beta=True,
    known_blockers=(
        "exact_runtime_version_not_pinned",
        "provider_terms_and_retention_not_verified_for_sensitive_data",
        "live_nexus_repo_benchmark_not_completed",
        "no_production_promotion_authorized",
    ),
    allowed_capabilities=(CapabilityRisk.READ, CapabilityRisk.WRITE_LOCAL, CapabilityRisk.EXEC),
    sandbox_required=True,
    network_allowed=False,
    can_receive_secrets=False,
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


def _normalized_workspace(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def validate_runner_packet(packet: WorkPacket, runner: RunnerManifest = OPENWORKER) -> dict[str, Any]:
    if packet.schema_version != "nexus.runner.v1":
        raise ValueError("unsupported_runner_schema")
    if not all((packet.packet_id.strip(), packet.project_id.strip(), packet.objective.strip())):
        raise ValueError("invalid_runner_packet_identity")
    if packet.workspace_subpath.startswith(("/", "\\")) or ".." in packet.workspace_subpath.replace("\\", "/").split("/"):
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
    if bool(packet.inputs.get("network_enabled")) and not runner.network_allowed:
        raise ValueError("runner_network_not_allowed")
    if bool(packet.inputs.get("contains_secrets")) and not runner.can_receive_secrets:
        raise ValueError("runner_secret_access_not_allowed")
    workspace = _normalized_workspace(packet.workspace_subpath)
    if runner.sandbox_required and packet.capability in (CapabilityRisk.WRITE_LOCAL, CapabilityRisk.EXEC):
        if not workspace.casefold().startswith("sandbox/"):
            raise ValueError("sandbox_scope_required")

    disposition = "prepare_only"
    if runner.sandbox_required and packet.capability in (CapabilityRisk.WRITE_LOCAL, CapabilityRisk.EXEC):
        disposition = "sandbox_only"
    return {
        "runner_id": runner.runner_id,
        "packet_digest": packet.digest,
        "disposition": disposition,
        "workspace_subpath": workspace,
        "network_authorized": False,
        "external_action_authorized": False,
        "nexus_approval_remains_authoritative": True,
        "runner_is_authority": False,
    }


@dataclass(frozen=True)
class MCPServerCandidate:
    server_id: str
    provenance: str
    risk: CapabilityRisk
    required_for: tuple[str, ...]
    enabled: bool = False
    project_scopes: tuple[str, ...] = ()
    cost_class: str = "existing_or_free"
    health_probe: str = "read_only_identity_probe"
    fallback: str = "manual_or_native_workflow"


NEXUS_MCP_BASELINE = (
    MCPServerCandidate("github", "official_or_vendor", CapabilityRisk.READ, ("code_review", "ci_evidence"), project_scopes=("portfolio_platform",)),
    MCPServerCandidate("gmail", "official_or_vendor", CapabilityRisk.READ, ("need_radar", "thread_reconciliation"), project_scopes=("hydrostatic_tester", "kcl_mop", "can_forming")),
    MCPServerCandidate("google_drive", "official_or_vendor", CapabilityRisk.READ, ("source_retrieval", "document_lineage")),
    MCPServerCandidate("notion", "official_or_vendor", CapabilityRisk.READ, ("project_memory", "decision_log")),
    MCPServerCandidate("hubspot", "official_or_vendor", CapabilityRisk.READ, ("crm_hygiene", "lead_validation")),
    MCPServerCandidate("apollo", "official_or_vendor", CapabilityRisk.READ, ("lead_research", "relationship_paths"), cost_class="paid_or_credit_metered", health_probe="read_only_usage_and_identity_probe", fallback="official_web_and_crm_research"),
    MCPServerCandidate("filesystem", "reference", CapabilityRisk.READ, ("vault", "local_evidence")),
    MCPServerCandidate("playwright", "official_or_vendor", CapabilityRisk.READ, ("ui_verification", "authenticated_read_probe")),
    MCPServerCandidate("zotero", "official_or_vendor", CapabilityRisk.READ, ("research_library", "citation_traceability")),
    MCPServerCandidate("canva", "official_or_vendor", CapabilityRisk.READ, ("brand_asset_review", "presentation_drafts"), project_scopes=("portfolio_platform",)),
    MCPServerCandidate("figma", "official_or_vendor", CapabilityRisk.READ, ("design_system_review", "design_to_code_evidence"), project_scopes=("portfolio_platform",)),
    MCPServerCandidate("supabase", "official_or_vendor", CapabilityRisk.READ, ("schema_inspection", "data_health"), project_scopes=("portfolio_platform",), health_probe="read_only_project_and_schema_probe", fallback="local_sqlite_and_repository_schema"),
)


def activation_plan(candidates: tuple[MCPServerCandidate, ...] = NEXUS_MCP_BASELINE) -> list[dict[str, Any]]:
    ids = [item.server_id for item in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate_mcp_server_id")
    return [
        {
            "server_id": item.server_id,
            "enabled": item.enabled,
            "initial_scope": "read_only",
            "risk": item.risk.value,
            "required_for": list(item.required_for),
            "project_scopes": list(item.project_scopes),
            "cost_class": item.cost_class,
            "health_probe": item.health_probe,
            "fallback": item.fallback,
            "approval_rule": "nexus_exact_scope_gate_for_any_write",
        }
        for item in candidates
    ]


def activation_waves(candidates: tuple[MCPServerCandidate, ...] = NEXUS_MCP_BASELINE) -> dict[str, list[str]]:
    """Create a conservative, deterministic rollout without activating tools."""
    ids = [item.server_id for item in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate_mcp_server_id")
    paid = {item.server_id for item in candidates if item.cost_class != "existing_or_free"}
    wave_1 = ("github", "gmail", "google_drive", "filesystem")
    wave_2 = ("notion", "hubspot", "playwright", "zotero")
    wave_3 = ("canva", "figma", "supabase", "apollo")
    known = set(ids)
    return {
        "now_read_only": [item for item in wave_1 if item in known and item not in paid],
        "next_project_pilots": [item for item in wave_2 if item in known and item not in paid],
        "later_or_metered": [item for item in wave_3 if item in known],
        "unclassified": sorted(known - set(wave_1) - set(wave_2) - set(wave_3)),
    }
