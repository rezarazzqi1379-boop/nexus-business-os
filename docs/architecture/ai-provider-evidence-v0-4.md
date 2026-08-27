# NEXUS AI Provider Evidence v0.4

Status: POLICY-EVIDENCE REVIEWED / PUBLIC SHADOW ONLY / NO LIVE EXECUTION

## What changed

FreeLLM remains a discovery directory only. A dated snapshot of all 18 entries currently visible on FreeLLM was captured so NEXUS can track discovery drift without treating directory claims as facts.

Four providers were separately reviewed against current official documentation: Cloudflare Workers AI, OpenRouter, Vercel AI Gateway and Google AI Studio. Those reviews are recorded in `ai_provider_policy_evidence_v0.1.json` and promoted into `ai_provider_registry_v0.2.json` with `policy_verified=true`, `max_sensitivity=public`, and `production_approved=false`.

## Current decisions

- Cloudflare Workers AI: strongest direct public-shadow free inference candidate. Official docs currently state 10,000 Neurons/day free and no use of Workers AI customer content for training or service improvement without explicit consent.
- OpenRouter Free: useful public-only compatibility/fallback candidate. OpenRouter retention is opt-in at its layer, but upstream free providers vary and the free router is dynamic.
- Vercel AI Gateway: strongest public-shadow gateway candidate. Gateway-level no-training/no-storage claims, provider allowlists, ZDR routing and observability are useful, but upstream/account configuration must be proven before raising trust.
- Google AI Studio Free: public research candidate only. Current official pricing states Free Tier content may be used to improve Google products; account/model rate limits are dynamic.

## Non-promoted discovery candidates

Cerebras, Kilo Gateway and NVIDIA NIM remain disabled in the governed registry pending direct official policy verification. Other FreeLLM entries remain in the discovery snapshot and are not routable.

## Safety boundary

No provider has production approval. No provider is allowed internal, confidential or restricted NEXUS data. No credentials, API calls, spend, deployment or external actions are introduced by this stage.

## Next executable gate

The next stage is a live public-only shadow trial collecting latency, success, eval and cost observations. That stage requires an account/API credential or an already-connected provider environment. Until then, the repository can select and rank policy-reviewed candidates but cannot call them.
