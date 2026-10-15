from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ResolutionMode(str, Enum):
    OFFICIAL_API = "official_api"
    EXISTING_CONNECTOR = "existing_connector"
    SELF_HOST = "self_host"
    PROVIDER_SIGNUP = "provider_signup"
    HUMAN_HANDOFF = "human_handoff"
    BLOCKED = "blocked"


class ControlGate(str, Enum):
    NONE = "none"
    OAUTH = "oauth"
    EMAIL_VERIFICATION = "email_verification"
    CAPTCHA = "captcha"
    IDENTITY = "identity"
    TERMS = "terms"
    PAYMENT = "payment"
    PRODUCTION = "production"


@dataclass(frozen=True)
class ProviderPath:
    provider: str
    preferred_modes: tuple[ResolutionMode, ...]
    gates: tuple[ControlGate, ...]
    self_host_available: bool = False
    notes: str = ""


@dataclass(frozen=True)
class ResolutionDecision:
    provider: str
    mode: ResolutionMode
    can_continue_machine_side: bool
    human_gate: ControlGate
    reason: str


DEFAULT_PATHS: dict[str, ProviderPath] = {
    "n8n": ProviderPath("n8n", (ResolutionMode.SELF_HOST, ResolutionMode.PROVIDER_SIGNUP), (ControlGate.OAUTH,), True, "Prefer self-host for governed orchestration."),
    "vaultwarden": ProviderPath("vaultwarden", (ResolutionMode.SELF_HOST,), (), True, "Bitwarden-compatible credential boundary; unofficial implementation."),
    "bitwarden": ProviderPath("bitwarden", (ResolutionMode.SELF_HOST, ResolutionMode.PROVIDER_SIGNUP), (ControlGate.EMAIL_VERIFICATION,), True, "Prefer official self-host when support/assurance matters."),
    "chatwoot": ProviderPath("chatwoot", (ResolutionMode.SELF_HOST, ResolutionMode.PROVIDER_SIGNUP), (ControlGate.EMAIL_VERIFICATION,), True, "Self-host can reduce signup friction; harden before production."),
    "nextcloud": ProviderPath("nextcloud", (ResolutionMode.SELF_HOST,), (), True, "Use scripted provisioning/app tokens after deployment target exists."),
    "cal_diy": ProviderPath("cal_diy", (ResolutionMode.SELF_HOST,), (), True, "Keep separate from hosted commercial Cal.com."),
    "penpot": ProviderPath("penpot", (ResolutionMode.SELF_HOST, ResolutionMode.PROVIDER_SIGNUP), (ControlGate.EMAIL_VERIFICATION,), True, "Design fallback."),
    "libretranslate": ProviderPath("libretranslate", (ResolutionMode.SELF_HOST,), (), True, "Benchmark Persian before sensitive use."),
    "granola": ProviderPath("granola", (ResolutionMode.PROVIDER_SIGNUP,), (ControlGate.EMAIL_VERIFICATION,), False, "Current connector reports no account."),
    "apollo": ProviderPath("apollo", (ResolutionMode.EXISTING_CONNECTOR, ResolutionMode.PROVIDER_SIGNUP), (ControlGate.OAUTH,), False, "Existing connector currently has invalid credentials."),
    "posthog": ProviderPath("posthog", (ResolutionMode.EXISTING_CONNECTOR,), (), False, "Already live-probed READ_VERIFIED."),
    "hubspot": ProviderPath("hubspot", (ResolutionMode.EXISTING_CONNECTOR,), (), False, "Already live-probed READ_VERIFIED."),
}


class ProviderResolutionPlanner:
    """Choose the smallest legitimate path around operational blockers.

    This planner deliberately does not bypass CAPTCHA, anti-bot systems, identity
    checks, OAuth consent, Terms acceptance, payment controls, or provider access
    restrictions. Instead it prefers official APIs/connectors or self-hosting and
    surfaces the exact provider-enforced gate when human action is unavoidable.
    """

    def __init__(self, paths: dict[str, ProviderPath] | None = None):
        self.paths = paths or DEFAULT_PATHS

    def resolve(self, provider: str, *, connector_healthy: bool = False, deployment_target: bool = False) -> ResolutionDecision:
        key = provider.strip().lower()
        if key not in self.paths:
            return ResolutionDecision(key, ResolutionMode.BLOCKED, False, ControlGate.NONE, "unknown_provider")
        path = self.paths[key]

        if connector_healthy and ResolutionMode.EXISTING_CONNECTOR in path.preferred_modes:
            return ResolutionDecision(key, ResolutionMode.EXISTING_CONNECTOR, True, ControlGate.NONE, "healthy_existing_connector")

        if path.self_host_available and ResolutionMode.SELF_HOST in path.preferred_modes:
            if deployment_target:
                return ResolutionDecision(key, ResolutionMode.SELF_HOST, True, ControlGate.NONE, "self_host_bootstrap")
            return ResolutionDecision(key, ResolutionMode.SELF_HOST, False, ControlGate.PRODUCTION, "deployment_target_required")

        if ResolutionMode.PROVIDER_SIGNUP in path.preferred_modes:
            gate = path.gates[0] if path.gates else ControlGate.NONE
            if gate is ControlGate.NONE:
                return ResolutionDecision(key, ResolutionMode.PROVIDER_SIGNUP, True, gate, "provider_signup_machine_side")
            return ResolutionDecision(key, ResolutionMode.HUMAN_HANDOFF, False, gate, "provider_enforced_human_gate")

        return ResolutionDecision(key, ResolutionMode.BLOCKED, False, ControlGate.NONE, "no_valid_resolution_path")

    def batch(self, providers: tuple[str, ...], *, healthy_connectors: frozenset[str] = frozenset(), deployment_target: bool = False) -> tuple[ResolutionDecision, ...]:
        return tuple(self.resolve(p, connector_healthy=p in healthy_connectors, deployment_target=deployment_target) for p in providers)
