# ADR 003 Connector Control Plane

## Decision

NEXUS will use a metadata federation control plane instead of copying every
plugin's raw data and credentials into one central database.

Each connector adapter supplies a bounded manifest, a freshness/health snapshot
and project-scoped evidence envelopes. Before a consequential answer or action,
the control plane builds a chat bootstrap preflight. It blocks stale required
sources, missing authority, cross-project evidence, factual contradictions and
external actions without exact approval.

## Security boundary

Credentials remain in the provider or secret manager. NEXUS stores only a
credential locator, never the credential value. Raw provider data remains at its
source unless an approved evidence-ingest workflow explicitly vaults it.

## First vertical proof

The first adapter set is Gmail plus canonical project sources for PRJ-HYD-01.
The acceptance proof is a deterministic test showing that conflicting prices or
technical values cannot pass silently and that data from another project is
rejected.

## Chat integration

Every NEXUS chat entry point must call the same preflight before drafting a
consequential response. A system prompt alone is not evidence that the check ran;
the generated preflight record and its evidence digests are the audit proof.

## Non goals

- Central storage of passwords, OAuth tokens or API keys
- Automatic external writes or messages
- Treating connector availability as data correctness
- Claiming access to providers that did not return a current snapshot

## Rollback

The module is additive. Remove the chat-entry preflight hook and its adapter
configuration to return to the previous behavior; provider data is untouched.
