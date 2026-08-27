from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


SENSITIVITY_ORDER = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}


@dataclass(frozen=True)
class ProviderRecord:
    id: str
    status: str
    authority: str
    capabilities: tuple[str, ...]
    openai_compatible: bool
    sensitive_data_allowed: bool
    production_role: str
    free_limit: str
    data_training: str
    official_source: str | None = None
    notes: str = ""


@dataclass(frozen=True)
class RoutingRequest:
    capability: str
    sensitivity: str = "public"
    require_openai_compatible: bool = False
    prefer_free: bool = True
    allow_unverified: bool = False
    production: bool = False


@dataclass(frozen=True)
class RoutingDecision:
    provider_id: str | None
    allowed: bool
    reason: str
    alternatives: tuple[str, ...] = ()


@dataclass(frozen=True)
class DiscoveryRecord:
    provider_id: str
    claim: str
    source_url: str
    authority: str = "DISCOVERY_ONLY"


def normalize_freellm_record(provider_id: str, claim: str, source_url: str = "https://freellm.sh/") -> DiscoveryRecord:
    provider_id = provider_id.strip().lower().replace(" ", "-")
    claim = claim.strip()
    if not provider_id or not claim:
        raise ValueError("provider_id and claim are required")
    return DiscoveryRecord(provider_id=provider_id, claim=claim, source_url=source_url)


def discovery_promotion_allowed(record: DiscoveryRecord, *, official_source_verified: bool) -> bool:
    """Discovery claims can never promote themselves into trusted provider facts."""
    if record.authority != "DISCOVERY_ONLY":
        return False
    return bool(official_source_verified)


class ResourceRouter:
    """Fail-closed model/provider selector for low-risk NEXUS workloads.

    This module is a policy layer only. It never holds credentials, performs network calls,
    or grants authority for consequential/external actions.
    """

    def __init__(self, providers: Iterable[ProviderRecord]):
        self.providers = tuple(providers)
        ids = [p.id for p in self.providers]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate provider id")

    @staticmethod
    def _eligible(provider: ProviderRecord, request: RoutingRequest) -> tuple[bool, str]:
        if request.sensitivity not in SENSITIVITY_ORDER:
            return False, "unknown sensitivity class"
        if request.capability not in provider.capabilities:
            return False, "missing capability"
        if request.require_openai_compatible and not provider.openai_compatible:
            return False, "not OpenAI-compatible"
        if request.sensitivity in {"confidential", "restricted"} and not provider.sensitive_data_allowed:
            return False, "provider not approved for sensitive data"
        if not request.allow_unverified and provider.authority != "OFFICIAL_DOCS_VERIFIED":
            return False, "provider is discovery-only/unverified"
        if request.production and (
            provider.status != "VERIFIED_CANDIDATE"
            or "DISABLED" in provider.production_role
            or "EXPERIMENT" in provider.production_role
        ):
            return False, "not approved as production candidate"
        return True, "eligible"

    def route(self, request: RoutingRequest) -> RoutingDecision:
        ranked: list[tuple[int, str]] = []
        rejected: list[str] = []
        for provider in self.providers:
            ok, why = self._eligible(provider, request)
            if not ok:
                rejected.append(f"{provider.id}:{why}")
                continue
            score = 0
            if provider.authority == "OFFICIAL_DOCS_VERIFIED":
                score += 50
            if request.prefer_free:
                score += 10
            if provider.openai_compatible:
                score += 8
            if "multi_provider" in provider.capabilities:
                score += 5
            if provider.id == "vercel_ai_gateway":
                score += 4
            ranked.append((score, provider.id))

        ranked.sort(reverse=True)
        if not ranked:
            return RoutingDecision(
                provider_id=None,
                allowed=False,
                reason="No provider satisfies current capability/sensitivity/verification policy.",
                alternatives=tuple(rejected),
            )
        return RoutingDecision(
            provider_id=ranked[0][1],
            allowed=True,
            reason="Selected by NEXUS policy: verified first, then compatibility/routing utility.",
            alternatives=tuple(provider_id for _, provider_id in ranked[1:]),
        )
