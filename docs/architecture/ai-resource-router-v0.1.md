# NEXUS AI Resource Router v0.1

Status: IMPLEMENTED ON FEATURE BRANCH — CI / MERGE / DEPLOYMENT PENDING.

## Purpose

Turn FreeLLM-style free-model discovery into a governed NEXUS capability without making a third-party directory an authority source or allowing free providers to receive sensitive company data by accident.

## Architecture

`Discovery -> Official verification -> Provider Registry -> Sensitivity Gate -> Capability Filter -> Routing Decision -> Future executor`

This module does not call providers, hold API keys, send external messages, or grant consequential authority.

## Authority boundary

- FreeLLM and similar directories are Tier D discovery/research only.
- Current official provider documentation is required before a provider becomes routable by default.
- Provider routing never overrides NEXUS project/engineering/business authority.
- Sensitive data is fail-closed unless a provider is explicitly approved for it.
- Production routing remains a separate gate from implementation/test success.

## Intended low-risk uses

- public web summarization;
- synthetic test generation;
- public/non-sensitive extraction and classification;
- model benchmarking;
- non-sensitive fallback experiments;
- cost and availability discovery.

## Explicitly blocked by default

Do not route Gmail contents, RFQs, quotations, engineering masters, contracts, customer records, supplier negotiations, credentials, payments, legal files, or restricted internal data through unapproved free providers.

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

## Non-goals

No provider API execution, no secrets, no autonomous paid spending, no email send, no engineering decision authority, no automatic model promotion from directory claims.
