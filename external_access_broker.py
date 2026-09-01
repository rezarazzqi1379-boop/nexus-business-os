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
    MATERIAL_COMMITMENT = "material_commitment"
    PRODUCTION_WRITE = "production_write"


@dataclass(frozen=True)
class ProviderManifest:
    provider: str
    signup_url: str
    auth_mode: str
    required_gates: tuple[Gate, ...]
    scopes: tuple[str, ...] = ()
    deployment: str = "cloud"
    nexus_role: str = "optional_adapter"
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
        return {"provider": self.provider, "action": self.action, "allowed_automatically": self.allowed_automatically, "human_gates": [g.value for g in self.human_gates], "scopes": list(self.scopes), "approval_fingerprint": self.approval_fingerprint}


def _p(provider, url, auth, gates=(), scopes=(), deployment="cloud", role="optional_adapter", notes=""):
    return ProviderManifest(provider, url, auth, tuple(gates), tuple(scopes), deployment, role, notes)


# User policy: routine free signup/use may proceed without repeated approval where the
# execution environment supports it. Explicit approval is still required for payment
# or a material/legal commitment. CAPTCHA/identity/OAuth are execution handoff gates
# when the provider requires the account holder to complete them; they are not treated
# as blanket permission to bypass provider controls.
DEFAULT_PROVIDERS: dict[str, ProviderManifest] = {
    "1password": _p("1password", "https://start.1password.com/sign-up", "account", role="comparison_only"),
    "bitwarden": _p("bitwarden", "https://vault.bitwarden.com/#/register", "account_or_api", role="credential_vault", notes="Prefer least-privilege organization/API access; self-hosting remains an option."),
    "deepl": _p("deepl", "https://www.deepl.com/signup", "api_key", role="translation_benchmark"),
    "libretranslate": _p("libretranslate", "https://libretranslate.com/", "api_key_or_self_host", deployment="self_host_preferred", role="translation_adapter"),
    "intercom": _p("intercom", "https://www.intercom.com/", "oauth", gates=(Gate.OAUTH_CONSENT,), role="comparison_only"),
    "chatwoot": _p("chatwoot", "https://www.chatwoot.com/", "account_or_api", deployment="self_host_candidate", role="customer_lead_inbox"),
    "loom": _p("loom", "https://www.loom.com/signup", "account", role="comparison_only"),
    "obs": _p("obs", "https://obsproject.com/", "local", deployment="local", role="recording_evidence"),
    "mixpanel": _p("mixpanel", "https://mixpanel.com/register/", "account_or_api", role="comparison_only"),
    "posthog": _p("posthog", "https://app.posthog.com/signup", "api_key", scopes=("event:write", "project:read"), role="observability", notes="Connected separately in ChatGPT; project-scoped keys only."),
    "typeform": _p("typeform", "https://admin.typeform.com/signup", "oauth_or_token", gates=(Gate.OAUTH_CONSENT,), role="comparison_only"),
    "google_forms": _p("google_forms", "https://forms.google.com/", "google_oauth", gates=(Gate.OAUTH_CONSENT,), role="external_intake"),
    "miro": _p("miro", "https://miro.com/signup/", "oauth", gates=(Gate.OAUTH_CONSENT,), role="comparison_only"),
    "excalidraw": _p("excalidraw", "https://excalidraw.com/", "local_or_cloud", deployment="local_or_cloud", role="architecture_visualization"),
    "otter": _p("otter", "https://otter.ai/signup", "account", role="comparison_only"),
    "granola": _p("granola", "https://granola.ai/mcp-signup", "account_mcp", role="meeting_intelligence", notes="ChatGPT connector discovered; live probe currently reports no Granola account."),
    "airtable": _p("airtable", "https://airtable.com/signup", "oauth_or_token", gates=(Gate.OAUTH_CONSENT,), role="comparison_only"),
    "baserow": _p("baserow", "https://baserow.io/", "jwt_or_database_token", deployment="self_host_candidate", role="optional_database_ui", notes="Do not duplicate canonical Postgres/Supabase without a measured gap."),
    "figma": _p("figma", "https://www.figma.com/signup", "oauth_or_token", gates=(Gate.OAUTH_CONSENT,), role="design_primary"),
    "penpot": _p("penpot", "https://design.penpot.app/", "account_or_access_token", deployment="self_host_candidate", role="design_fallback"),
    "zapier": _p("zapier", "https://zapier.com/sign-up", "oauth", gates=(Gate.OAUTH_CONSENT,), role="comparison_only"),
    "n8n": _p("n8n", "https://app.n8n.cloud/register", "oauth_or_api_key", gates=(Gate.OAUTH_CONSENT,), scopes=("workflow:read",), deployment="self_host_preferred", role="orchestration", notes="Never decision authority. Workflow activation and credential writes are separately controlled."),
    "dropbox": _p("dropbox", "https://www.dropbox.com/register", "oauth", gates=(Gate.OAUTH_CONSENT,), role="comparison_only"),
    "nextcloud": _p("nextcloud", "https://nextcloud.com/", "app_password_or_oidc", deployment="self_host_candidate", role="evidence_vault_candidate"),
    "notion": _p("notion", "https://www.notion.so/signup", "oauth", gates=(Gate.OAUTH_CONSENT,), role="operational_state"),
    "obsidian": _p("obsidian", "https://obsidian.md/", "local", deployment="local", role="personal_knowledge_optional"),
    "calendly": _p("calendly", "https://calendly.com/signup", "oauth", gates=(Gate.OAUTH_CONSENT,), role="comparison_only"),
    "cal_diy": _p("cal_diy", "https://cal.com/", "api_or_self_host", deployment="self_host_candidate", role="scheduling_candidate", notes="Cal.com moved free/open-source self-host code to Cal.diy in 2026; hosted commercial API is separate."),
}


class ExternalAccessBroker:
    """Governed planner for external accounts and connectors.

    Reversible free account/setup work can be planned automatically. Payment and
    material commitments always require explicit approval. Provider-enforced CAPTCHA,
    identity verification and OAuth consent are surfaced as execution handoffs and are
    never bypassed.
    """

    def __init__(self, manifests: Iterable[ProviderManifest] | None = None):
        items = manifests or DEFAULT_PROVIDERS.values()
        self._providers = {item.provider: item for item in items}

    def providers(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))

    def manifest(self, provider: str) -> ProviderManifest:
        key = provider.strip().lower()
        if key not in self._providers:
            raise KeyError(f"unknown_provider:{key}")
        return self._providers[key]

    def plan_signup(self, provider: str) -> AccessPlan:
        return self._plan(self.manifest(provider), "signup")

    def plan_connect(self, provider: str) -> AccessPlan:
        manifest = self.manifest(provider)
        gates = list(manifest.required_gates)
        if manifest.auth_mode in {"oauth", "oauth_or_api_key", "google_oauth"} and Gate.OAUTH_CONSENT not in gates:
            gates.append(Gate.OAUTH_CONSENT)
        return self._plan(manifest, "connect", tuple(gates))

    def plan_payment(self, provider: str) -> AccessPlan:
        return self._plan(self.manifest(provider), "payment", (Gate.PAYMENT,))

    def plan_material_commitment(self, provider: str) -> AccessPlan:
        return self._plan(self.manifest(provider), "material_commitment", (Gate.MATERIAL_COMMITMENT,))

    def _plan(self, manifest: ProviderManifest, action: str, gates: tuple[Gate, ...] | None = None) -> AccessPlan:
        human_gates = gates if gates is not None else manifest.required_gates
        payload = {"provider": manifest.provider, "action": action, "gates": [g.value for g in human_gates], "scopes": list(manifest.scopes)}
        fingerprint = sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        return AccessPlan(manifest.provider, action, len(human_gates) == 0, human_gates, manifest.scopes, fingerprint)
