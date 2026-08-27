# NEXUS AI Resource Router v0.1

Status: IMPLEMENTED + TESTED + MERGED TO MAIN through PR #56 on 27 Aug 2026. Superseded for routing-policy behavior by AI Resource Router Hardening v0.2 / PR #57. Not deployed and not production-enabled.

## Purpose

Turn FreeLLM-style free-model discovery into a governed NEXUS capability without making a third-party directory an authority source or allowing free providers to receive sensitive company data by accident.

## Architecture

`Discovery -> Official verification -> Provider Registry -> Sensitivity Gate -> Capability Filter -> Routing Decision -> Future executor`

This module does not call providers, hold API keys, send external messages, or grant consequential authority.

## Authority boundary

- FreeLLM and similar directories are Tier D discovery/research only.
- Current official provider documentation is required before a provider becomes a candidate; v0.2 additionally requires explicit policy verification before routing.
- Provider routing never overrides NEXUS project/engineering/business authority.
- Sensitive data is fail-closed unless a provider is explicitly approved for the relevant sensitivity class.
- Production routing remains a separate gate from implementation/test/merge success.

## Intended low-risk uses

- public web summarization;
- synthetic test generation;
- public/non-sensitive extraction and classification;
- model benchmarking;
- non-sensitive fallback experiments;
- cost and availability discovery.

## Explicitly blocked by default

Do not route Gmail contents, RFQs, quotations, engineering masters, contracts, customer records, supplier negotiations, credentials, payments, legal files, or restricted internal data through unapproved providers.

## Promotion gates

Before any provider is enabled for production or sensitive workloads:

1. verify current official pricing/rate limits;
2. verify privacy, retention and training policy;
3. verify region/account restrictions;
4. isolate credentials in an approved secrets mechanism;
5. add bounded health/latency/cost probes;
6. add workload-specific evals;
7. prove fallback semantics and duplicate prevention;
8. pass repository CI on exact branch head;
9. obtain explicit production promotion approval.

## Historical note

The initial PR #56 CI proved the canonical `evals/` suite but did not execute the new pytest router suite. That proof gap was discovered after merge and is explicitly corrected by v0.2 / PR #57, which also hardens sensitivity and production approval semantics. Do not use the original PR #56 CI result alone as evidence of full router regression coverage.

## Non-goals

No provider API execution, no secrets, no autonomous paid spending, no email send, no engineering decision authority, no automatic model promotion from directory claims.
