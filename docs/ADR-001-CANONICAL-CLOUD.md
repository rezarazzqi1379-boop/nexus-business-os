# ADR-001: Canonical cloud-first NEXUS runtime

Date: 2026-08-24  
Status: Accepted

## Decision

Run NEXUS as a private, managed Linux container with persistent storage. Use
Railway for the first controlled pilot. Keep local installation only for
development, emergency recovery and offline work.

## Why

- removes dependency on a particular Windows machine;
- stays online without the owner's computer;
- makes health checks, restart and HTTPS operationally simple;
- preserves portability through Docker, SQLite and filesystem-based vault data;
- can later move to another container host without rewriting the application.

## Boundaries

- No external write, send, payment, contract, deployment or permission change
  is self-authorized. Exact-scope, single-use approval remains mandatory.
- API-free operation covers deterministic workflows, canonical documents,
  queueing, audit, UI, backup and review. Live LLM reasoning and third-party
  connectors require the corresponding provider credentials.
- A browser-session automation pretending to be an API is not the canonical
  design: it is fragile, hard to audit and may violate provider terms.

## Evolution path

Pilot: one container + persistent volume.  Growth: managed Postgres, encrypted
object-storage backups, scheduled workers and observability.  Scale: split web,
worker and connector services while retaining the same policy and evidence
contracts.
