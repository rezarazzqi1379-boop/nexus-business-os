from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable


class Gate(str, Enum):
    NONE = "none"
    TERMS = "terms"
    CAPTCHA = "captcha"
    IDENTITY = "identity"
    PAYMENT = "payment"
    OAUTH_CONSENT = "oauth_consent"
    PRODUCTION_WRITE = "production_write"


@dataclass(frozen=True)
class ProviderManifest:
    provider: str
    signup_url: str
    auth_mode: str
    required_gates: tuple[Gate, ...]
    scopes: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class AccessPlan:
    provider: str
    action: str
    allowed_automatically: bool
    human_gates: tuple[Gate, ...]
    scopes: tuple[str, ...]
    approval_fingerprint: str

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "action": self.action,
            "allowed_automatically": self.allowed_automatically,
            "human_gates": [g.value for g in self.human_gates],
            "scopes": list(self.scopes),
            "approval_fingerprint": self.approval_fingerprint,
        }


DEFAULT_PROVIDERS: dict[str, ProviderManifest] = {
    "posthog": ProviderManifest(
        provider="posthog",
        signup_url="https://app.posthog.com/signup",
        auth_mode="api_key",
        required_gates=(Gate.TERMS,),
        scopes=("event:write", "project:read"),
        notes="Prefer project-scoped ingestion key; never store secrets in source control.",
    ),
    "n8n": ProviderManifest(
        provider="n8n",
        signup_url="https://app.n8n.cloud/register",
        auth_mode="oauth_or_api_key",
        required_gates=(Gate.TERMS, Gate.OAUTH_CONSENT),
        scopes=("workflow:read",),
        notes="Start read-only. Workflow activation and credential writes remain separately gated.",
    ),
    "hubspot": ProviderManifest(
        provider="hubspot",
        signup_url="https://app.hubspot.com/signup-hubspot/crm",
        auth_mode="oauth",
        required_gates=(Gate.TERMS, Gate.OAUTH_CONSENT),
        scopes=("crm.objects.contacts.read", "crm.objects.companies.read"),
        notes="Read-first connector; outreach and CRM writes require exact action approval.",
    ),
}


class ExternalAccessBroker:
    """Plans account/connectivity work without impersonating a human or bypassing gates.

    The broker may automate reversible machine steps, but pauses for legal acceptance,
    CAPTCHA, identity verification, payment, OAuth consent, or production writes.
    """

    def __init__(self, manifests: Iterable[ProviderManifest] | None = None):
        items = manifests or DEFAULT_PROVIDERS.values()
        self._providers = {item.provider: item for item in items}

    def manifest(self, provider: str) -> ProviderManifest:
        key = provider.strip().lower()
        if key not in self._providers:
            raise KeyError(f"unknown_provider:{key}")
        return self._providers[key]

    def plan_signup(self, provider: str) -> AccessPlan:
        manifest = self.manifest(provider)
        return self._plan(manifest, "signup")

    def plan_connect(self, provider: str) -> AccessPlan:
        manifest = self.manifest(provider)
        gates = list(manifest.required_gates)
        if manifest.auth_mode in {"oauth", "oauth_or_api_key"} and Gate.OAUTH_CONSENT not in gates:
            gates.append(Gate.OAUTH_CONSENT)
        return self._plan(manifest, "connect", tuple(gates))

    def _plan(
        self,
        manifest: ProviderManifest,
        action: str,
        gates: tuple[Gate, ...] | None = None,
    ) -> AccessPlan:
        human_gates = gates if gates is not None else manifest.required_gates
        payload = {
            "provider": manifest.provider,
            "action": action,
            "gates": [g.value for g in human_gates],
            "scopes": list(manifest.scopes),
        }
        fingerprint = sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        return AccessPlan(
            provider=manifest.provider,
            action=action,
            allowed_automatically=len(human_gates) == 0,
            human_gates=human_gates,
            scopes=manifest.scopes,
            approval_fingerprint=fingerprint,
        )
