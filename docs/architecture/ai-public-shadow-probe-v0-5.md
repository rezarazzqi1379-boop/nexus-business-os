# NEXUS AI Public Shadow Probe v0.5

Status: IMPLEMENTED / NETWORK EXECUTION GATED / PUBLIC SYNTHETIC INPUT ONLY

This stage prepares the first live provider-evidence path without allowing arbitrary NEXUS data to leave the system.

Supported probe builders: Cloudflare Workers AI, OpenRouter Free, Google AI Studio.

The probe prompt is hard-coded synthetic public text: `Return exactly this token and nothing else: NEXUS_PUBLIC_PROBE_OK`. Callers cannot pass Gmail, RFQ, engineering, customer, supplier, legal or internal content into the probe API.

Actual network execution requires two independent gates: the caller must pass `allow_network=True` and the environment must contain `NEXUS_PUBLIC_SHADOW_EXECUTE=1`. Provider account credentials must exist only in environment/secrets, never in repository data.

The probe records health, latency, success and a deterministic exact-output eval. A single result is not sufficient for the economy layer default minimum sample count; repeated bounded runs are still required before ranking evidence is admissible.

No provider is production-approved by this change. No paid spend is authorized. Estimated cost is fixed at zero only for the free-shadow lane and must be replaced with provider/billing evidence before any paid promotion.

The next real gate is account credential availability. Once a reviewed provider credential is available in an approved secrets mechanism, the same bounded synthetic probe can collect live observations without exposing company data.
