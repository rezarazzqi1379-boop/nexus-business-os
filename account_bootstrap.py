from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from external_access_broker import ExternalAccessBroker, Gate


class BootstrapState(str, Enum):
    READY = "ready"
    HANDOFF_REQUIRED = "handoff_required"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class BootstrapItem:
    provider: str
    state: BootstrapState
    action: str
    gates: tuple[Gate, ...]
    reason: str


@dataclass(frozen=True)
class BootstrapBatch:
    project_id: str
    items: tuple[BootstrapItem, ...]

    @property
    def ready(self) -> tuple[BootstrapItem, ...]:
        return tuple(item for item in self.items if item.state is BootstrapState.READY)

    @property
    def handoffs(self) -> tuple[BootstrapItem, ...]:
        return tuple(item for item in self.items if item.state is BootstrapState.HANDOFF_REQUIRED)


class AccountBootstrapPlanner:
    """Plans many provider onboarding steps without pretending gated actions completed.

    The planner is intentionally non-executing. It separates machine-runnable setup from
    provider-enforced human handoffs and from policy-blocked commercial commitments.
    That lets NEXUS prepare many integrations in parallel while preserving exact state.
    """

    COMPARISON_ROLES = {"comparison_only", "translation_benchmark"}

    def __init__(self, broker: ExternalAccessBroker | None = None):
        self.broker = broker or ExternalAccessBroker()

    def plan(self, project_id: str, providers: Iterable[str] | None = None) -> BootstrapBatch:
        if not project_id.strip():
            raise ValueError("project_id_required")

        selected = tuple(providers or self.broker.providers())
        items: list[BootstrapItem] = []
        for provider in selected:
            manifest = self.broker.manifest(provider)

            if manifest.nexus_role in self.COMPARISON_ROLES:
                items.append(BootstrapItem(provider, BootstrapState.SKIPPED, "none", (), "comparison_only_not_active_stack"))
                continue

            plan = self.broker.plan_connect(provider)
            if Gate.PAYMENT in plan.human_gates or Gate.MATERIAL_COMMITMENT in plan.human_gates:
                items.append(BootstrapItem(provider, BootstrapState.BLOCKED, "connect", plan.human_gates, "commercial_commitment_requires_explicit_approval"))
                continue

            if plan.allowed_automatically:
                items.append(BootstrapItem(provider, BootstrapState.READY, "connect", (), "machine_runnable_or_local_setup"))
            else:
                items.append(BootstrapItem(provider, BootstrapState.HANDOFF_REQUIRED, "connect", plan.human_gates, "provider_enforced_handoff"))

        return BootstrapBatch(project_id=project_id, items=tuple(items))

    def prioritized_active_stack(self, project_id: str) -> BootstrapBatch:
        return self.plan(project_id, (
            "bitwarden",
            "posthog",
            "n8n",
            "chatwoot",
            "nextcloud",
            "cal_diy",
            "libretranslate",
            "penpot",
            "excalidraw",
            "obs",
            "obsidian",
            "google_forms",
            "granola",
            "baserow",
        ))
