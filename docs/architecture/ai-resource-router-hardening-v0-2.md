# NEXUS AI Resource Router Hardening v0.2

Status: IMPLEMENTED + FULL-CI TESTED + MERGED TO MAIN through PR #57 on 27 Aug 2026. Not deployed and not production-enabled.

## Why this hardening exists

PR #56 introduced a governed FreeLLM/provider discovery layer, but review of the merged lineage exposed two gaps that had to be corrected before any activation:

1. canonical CI ran only `evals/`, so the newly added `tests/test_nexus_ai_resource_router.py` suite was not part of the original GitHub Actions proof;
2. the v0.1 policy could allow `internal` data to a provider whose `sensitive_data_allowed` flag was false, and production eligibility was inferred from descriptive status strings rather than an explicit approval bit.

These were governance defects, not provider-performance defects.

During full-CI hardening, a pre-existing vault concurrency race was also exposed by `test_concurrent_vault_collision_has_one_winner`. `BusinessOSVault._atomic_create` was corrected to prepare/fsync a private temporary file and atomically publish it, preventing a competing writer from observing partial JSON.

## v0.2 invariants

- CI runs both canonical `unittest` evals and the repository `pytest` regression suite.
- Every provider defaults to `max_sensitivity=public` unless a separate reviewed registry record raises that boundary.
- Every provider defaults to `policy_verified=false`.
- Every provider defaults to `production_approved=false`.
- Official documentation alone does not equal privacy/policy approval.
- FreeLLM remains Tier D discovery only.
- Current registry entries therefore remain non-routable until policy review is explicitly recorded.
- No provider call, credential, spend, deployment, email send, supplier action or other external effect is added by this hardening.

## NEXUS integration rule

The router is an economic/technical selection aid below the NEXUS authority plane. It cannot override Master Context, Source Registry, engineering masters, live evidence, action approvals or project isolation.

Target execution sequence remains:

`Task -> Project/authority validation -> data sensitivity classification -> provider policy gate -> capability/eval/cost selection -> immutable execution intent -> approval if consequential -> executor`

## CI evidence

PR #57 exact head `28d4560a1b800d7a2aa0b576b0a94e8e8c3003e8` completed GitHub Actions run `33064094071` successfully before merge. The workflow includes compile, canonical unittest evaluation and the pytest regression suite. PR #57 was then squash-merged to main as `20a5ca50855b0f0721e0cf5e72a01649d9f8de40`.

## Activation gates

A provider may move beyond discovery only when current official documentation and account-specific terms are captured, privacy/training/retention and regional constraints are reviewed, a maximum sensitivity is explicitly assigned, workload-specific evals are passed, bounded cost/latency behavior is observed, secrets are isolated, fallback/retry semantics are tested and production approval is separately granted.

No field may be inferred from marketing language, directory claims or descriptive role strings.

## Current endpoint

The correct current state is **governed routing infrastructure merged, provider execution disabled**. This is the highest justified promotion state without live account policy evidence, credentials/secrets configuration, workload evals and explicit production approval. Do not label this deployed or production.
