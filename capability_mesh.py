from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import IntEnum
from typing import Iterable


class CapabilityState(IntEnum):
    AVAILABLE = 10
    CONNECTED = 20
    READ_VERIFIED = 30
    WRITE_ENABLED = 40
    PRODUCTION_APPROVED = 50


@dataclass(frozen=True)
class ProbeRecord:
    provider: str
    state: CapabilityState
    role: str
    checked_at: str
    evidence_locator: str
    blocker: str | None = None

    @property
    def routable(self) -> bool:
        return self.blocker is None and self.state >= CapabilityState.READ_VERIFIED


@dataclass(frozen=True)
class RouteRequest:
    project_id: str
    action_class: str
    required_roles: tuple[str, ...]
    source_project_id: str | None = None
    target_project_id: str | None = None
    material_commitment: bool = False
    payment_required: bool = False


@dataclass(frozen=True)
class RouteDecision:
    allowed: bool
    providers: tuple[str, ...]
    approval_required: bool
    reason: str


class CapabilityMesh:
    """Least-capability router for NEXUS external adapters.

    Adapters provide capabilities; they never become authority. The mesh selects the
    smallest verified provider set for a task and fails closed on unknown or blocked
    state, cross-project transfer, payment/material commitments, and writes without
    a sufficient capability state.
    """

    WRITE_ACTIONS = {"write", "external_write", "publish", "send", "mutate"}
    PRODUCTION_ACTIONS = {"production", "deploy", "production_write"}

    def __init__(self, records: Iterable[ProbeRecord]):
        self._records = {r.provider: r for r in records}

    def providers(self) -> tuple[str, ...]:
        return tuple(sorted(self._records))

    def record(self, provider: str) -> ProbeRecord:
        if provider not in self._records:
            raise KeyError(f"unknown_provider:{provider}")
        return self._records[provider]

    def promote(self, provider: str, new_state: CapabilityState) -> ProbeRecord:
        current = self.record(provider)
        if new_state < current.state:
            raise ValueError("state_regression_requires_explicit_recovery_record")
        if current.blocker:
            raise ValueError("blocked_provider_cannot_self_promote")
        return ProbeRecord(
            provider=current.provider,
            state=new_state,
            role=current.role,
            checked_at=datetime.now(timezone.utc).isoformat(),
            evidence_locator=current.evidence_locator,
            blocker=None,
        )

    def route(self, request: RouteRequest) -> RouteDecision:
        if not request.project_id.strip():
            return RouteDecision(False, (), False, "project_id_required")
        if (
            request.source_project_id
            and request.target_project_id
            and request.source_project_id != request.target_project_id
        ):
            return RouteDecision(False, (), False, "cross_project_transfer_denied")

        approval_required = request.payment_required or request.material_commitment
        if approval_required:
            return RouteDecision(False, (), True, "payment_or_material_commitment_gate")

        candidates: list[ProbeRecord] = []
        for role in request.required_roles:
            matches = [
                r for r in self._records.values()
                if r.role == role and r.blocker is None
            ]
            if not matches:
                return RouteDecision(False, (), False, f"missing_role:{role}")

            minimum = CapabilityState.READ_VERIFIED
            if request.action_class in self.WRITE_ACTIONS:
                minimum = CapabilityState.WRITE_ENABLED
            elif request.action_class in self.PRODUCTION_ACTIONS:
                minimum = CapabilityState.PRODUCTION_APPROVED

            eligible = [r for r in matches if r.state >= minimum]
            if not eligible:
                return RouteDecision(False, (), True, f"insufficient_state:{role}")

            # Pick the least-privileged eligible adapter, then most recently checked.
            eligible.sort(key=lambda r: (int(r.state), r.checked_at), reverse=False)
            candidates.append(eligible[0])

        providers = tuple(dict.fromkeys(r.provider for r in candidates))
        return RouteDecision(True, providers, False, "least_capability_route")


def live_probe_snapshot() -> tuple[ProbeRecord, ...]:
    """Live evidence snapshot from connector probes performed 2 Sep 2026.

    This is implementation evidence, not canonical authority. Refresh before any
    consequential use because connector state is dynamic.
    """
    return (
        ProbeRecord(
            provider="notion",
            state=CapabilityState.READ_VERIFIED,
            role="knowledge_ops",
            checked_at="2026-09-02T00:00:00Z",
            evidence_locator="connector:notion/self",
        ),
        ProbeRecord(
            provider="hubspot",
            state=CapabilityState.READ_VERIFIED,
            role="crm",
            checked_at="2026-09-02T00:00:00Z",
            evidence_locator="connector:hubspot/get_user_details",
            blocker="portal_onboarding_incomplete",
        ),
        ProbeRecord(
            provider="posthog",
            state=CapabilityState.READ_VERIFIED,
            role="observability",
            checked_at="2026-09-02T00:00:00Z",
            evidence_locator="connector:posthog/dashboard/2055621",
        ),
        ProbeRecord(
            provider="canva",
            state=CapabilityState.READ_VERIFIED,
            role="design",
            checked_at="2026-09-02T00:00:00Z",
            evidence_locator="connector:canva/search-designs",
        ),
        ProbeRecord(
            provider="supabase",
            state=CapabilityState.READ_VERIFIED,
            role="structured_memory",
            checked_at="2026-09-02T00:00:00Z",
            evidence_locator="connector:supabase/list_projects",
            blocker="project_inactive",
        ),
        ProbeRecord(
            provider="apollo",
            state=CapabilityState.AVAILABLE,
            role="lead_discovery",
            checked_at="2026-09-02T00:00:00Z",
            evidence_locator="connector:apollo/contacts_search",
            blocker="invalid_access_credentials",
        ),
        ProbeRecord(
            provider="granola",
            state=CapabilityState.AVAILABLE,
            role="meeting_intelligence",
            checked_at="2026-09-02T00:00:00Z",
            evidence_locator="connector:granola/get_account_info",
            blocker="account_not_created",
        ),
    )
