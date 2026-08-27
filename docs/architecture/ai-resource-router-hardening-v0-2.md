# NEXUS AI Resource Router Hardening v0.2

Status: IMPLEMENTED ON FEATURE BRANCH — FULL CI PROOF PENDING.

## Why this hardening exists

PR #56 correctly introduced a governed FreeLLM/provider discovery layer, but review of the merged lineage exposed two gaps that must be corrected before any activation:

1. canonical CI ran only `evals/`, so the newly added `tests/test_nexus_ai_resource_router.py` suite was not part of the GitHub Actions proof;
2. the v0.1 policy could allow `internal` data to a provider whose `sensitive_data_allowed` flag was false, and production eligibility was inferred from descriptive status strings rather than an explicit approval bit.

These are governance defects, not provider-performance defects.

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

## Activation gates

A provider may move beyond discovery only when current official documentation and account-specific terms are captured, privacy/training/retention and regional constraints are reviewed, a maximum sensitivity is explicitly assigned, workload-specific evals are passed, bounded cost/latency behavior is observed, secrets are isolated, fallback/retry semantics are tested and production approval is separately granted.

No field may be inferred from marketing language, directory claims or descriptive role strings.
