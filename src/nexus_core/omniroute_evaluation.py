from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Decision = Literal["REJECT", "WATCH", "SANDBOX_EXPERIMENT", "ADOPT_GATEWAY_ADAPTER"]


@dataclass(frozen=True)
class OmniRouteEvidence:
    version: str
    license_mit: bool
    provider_count_claim: int
    unique_model_count_claim: int
    supports_openai_compatible: bool
    supports_mcp: bool
    supports_a2a: bool
    local_self_host_available: bool
    encryption_at_rest_available: bool
    encryption_fail_open_possible: bool
    guardrails_fail_open: bool
    tos_flags_are_routing_gates: bool
    provider_credentials_required_for_live_use: bool
    external_network_required_for_live_use: bool
    exact_provider_allowlist_supported_by_nexus_adapter: bool = False
    terms_safe_provider_allowlist_supported_by_nexus_adapter: bool = False
    request_response_logging_disabled_by_nexus_adapter: bool = False


@dataclass(frozen=True)
class OmniRouteAssessment:
    decision: Decision
    reasons: tuple[str, ...]
    required_controls: tuple[str, ...]


def assess_omniroute(e: OmniRouteEvidence) -> OmniRouteAssessment:
    """Evaluate OmniRoute only as a provider/model gateway adapter.

    This function deliberately separates upstream feature claims from NEXUS authority.
    It never grants model-selection, project-authority, credential, external-action,
    merge, deployment or production permission.
    """
    reasons: list[str] = []
    controls: list[str] = []

    if not e.version.strip():
        return OmniRouteAssessment("REJECT", ("version is required",), ())
    if not e.license_mit:
        reasons.append("license not verified as MIT")
    if not e.supports_openai_compatible:
        reasons.append("no verified OpenAI-compatible adapter surface")
    if not e.local_self_host_available:
        reasons.append("no verified local/self-host path")
    if reasons:
        return OmniRouteAssessment("REJECT", tuple(reasons), ())

    # Upstream security features are useful but not sufficient for NEXUS.
    if e.encryption_fail_open_possible:
        controls.append("require STORAGE_ENCRYPTION_KEY and reject plaintext credential persistence")
    if e.guardrails_fail_open:
        controls.append("do not rely on OmniRoute guardrails as a NEXUS authorization boundary")
    if not e.tos_flags_are_routing_gates:
        controls.append("NEXUS must maintain its own provider ToS/compliance allowlist before routing")
    if e.provider_credentials_required_for_live_use:
        controls.append("credentials remain outside test fixtures and require exact connector/provider approval")
    if e.external_network_required_for_live_use:
        controls.append("first experiment must use synthetic/sanitized prompts only")

    controls.extend(
        (
            "pin exact OmniRoute release/image digest for experiment",
            "disable web-cookie/session-token providers in NEXUS experiments",
            "allow only explicitly verified API/OAuth/local providers",
            "provider/model catalog is evidence, not authority",
            "no project specs, approval state or production secrets may be inferred from router output",
            "record provider actually selected for every routed call",
            "disable autonomous fallback across providers unless each fallback target is independently allowed",
            "feed measured latency/cost/corrections into NEXUS Adoption Gate",
        )
    )

    adapter_controls_ready = (
        e.exact_provider_allowlist_supported_by_nexus_adapter
        and e.terms_safe_provider_allowlist_supported_by_nexus_adapter
        and e.request_response_logging_disabled_by_nexus_adapter
    )

    if not adapter_controls_ready:
        return OmniRouteAssessment(
            "SANDBOX_EXPERIMENT",
            (
                "strong routing/model-breadth fit",
                "upstream feature and free-tier claims require provider-by-provider verification",
                "NEXUS-specific provider/ToS/logging controls are not yet proven",
            ),
            tuple(dict.fromkeys(controls)),
        )

    return OmniRouteAssessment(
        "ADOPT_GATEWAY_ADAPTER",
        (
            "adapter controls proven",
            "adoption still requires separate measured NEXUS Adoption Gate evidence",
        ),
        tuple(dict.fromkeys(controls)),
    )


def researched_snapshot() -> OmniRouteEvidence:
    """Primary-source snapshot reviewed 2026-08-28; feature counts are upstream claims."""
    return OmniRouteEvidence(
        version="3.8.50",
        license_mit=True,
        provider_count_claim=352,
        unique_model_count_claim=1312,
        supports_openai_compatible=True,
        supports_mcp=True,
        supports_a2a=True,
        local_self_host_available=True,
        encryption_at_rest_available=True,
        encryption_fail_open_possible=True,
        guardrails_fail_open=True,
        tos_flags_are_routing_gates=False,
        provider_credentials_required_for_live_use=True,
        external_network_required_for_live_use=True,
    )
