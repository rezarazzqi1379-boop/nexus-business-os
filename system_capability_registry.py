"""One read model for NEXUS local capability activation state."""
from __future__ import annotations

import importlib.util
from dataclasses import asdict, dataclass
from typing import Literal

ActivationState = Literal["ACTIVE_LOCAL", "EXPERIMENT_ONLY", "BLOCKED", "UNAVAILABLE"]


@dataclass(frozen=True)
class CapabilityActivation:
    capability_id: str
    module_name: str
    state: ActivationState
    local_use_enabled: bool
    live_network_enabled: bool
    production_approved: bool
    authority: str
    next_gate: str

    def validate(self) -> None:
        if not self.capability_id.strip() or not self.module_name.strip() or not self.authority.strip():
            raise ValueError("invalid_capability_activation")
        if self.state not in {"ACTIVE_LOCAL", "EXPERIMENT_ONLY", "BLOCKED", "UNAVAILABLE"}:
            raise ValueError("invalid_activation_state")
        if self.state == "UNAVAILABLE" and self.local_use_enabled:
            raise ValueError("unavailable_capability_cannot_be_enabled")
        if self.live_network_enabled and not self.production_approved:
            raise ValueError("live_network_requires_production_approval")


def _available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def activation_registry() -> tuple[CapabilityActivation, ...]:
    specs = (
        ("conversation-control", "conversation_control", "ACTIVE_LOCAL", True, "PROJECT_CONTRACT", "continue measured use"),
        ("owner-decision", "owner_decision_runtime", "ACTIVE_LOCAL", True, "OWNER_DELEGATED_LOCAL", "retain consequential approval gate"),
        ("collaboration-growth", "collaboration_growth", "ACTIVE_LOCAL", True, "DERIVED_WORKFLOW_SIGNALS", "continue privacy-safe evaluation"),
        ("self-improvement", "self_improvement_runtime", "ACTIVE_LOCAL", True, "EXPERIENCE_GATED", "adoption gate for every promotion"),
        ("continuous-research", "continuous_research", "ACTIVE_LOCAL", True, "UNVERIFIED_CLAIMS", "independent-source corroboration"),
        ("coordination-kit", "coordination_kit", "ACTIVE_LOCAL", True, "GIT_DERIVED_HANDOFF", "authenticated human actor binding"),
        ("fal-structural-model", "fal_reconciliation", "EXPERIMENT_ONLY", True, "AUTHORITY_RECONCILIATION_PENDING", "human-approved canonical authority"),
        ("tavily-search", "tavily_provider", "EXPERIMENT_ONLY", True, "PHASE_G_CANDIDATE", "credential-safe live benchmark approval"),
    )
    result = []
    for capability_id, module, desired_state, local, authority, gate in specs:
        installed = _available(module)
        item = CapabilityActivation(
            capability_id, module, desired_state if installed else "UNAVAILABLE",
            local and installed, False, False, authority, gate)
        item.validate()
        result.append(item)
    return tuple(result)


def activation_payload() -> dict:
    items = activation_registry()
    return {
        "schema_version": "nexus.capability-activation.v1",
        "capabilities": [asdict(item) for item in items],
        "live_network_capabilities": [item.capability_id for item in items if item.live_network_enabled],
        "production_approved_capabilities": [item.capability_id for item in items if item.production_approved],
    }
