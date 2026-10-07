# NEXUS Capability Growth Census v2 — 2026-10-07

Purpose: preserve novel mechanisms, evidence, overlap, acceptance tests and disposition so discovery compounds across sessions.

## CAP-ER-001 — Probabilistic Entity Resolution
Mechanism: probabilistic record linkage for records without stable unique IDs.
Evidence: Splink official repository/documentation pattern.
Blind spot addressed: transliteration, aliases, legal-name variants, incomplete company identifiers.
Overlap: partial with deterministic ENTITY_RESOLUTION; genuinely new confidence-based mechanism.
Disposition: STUDY_PATTERN.
Acceptance test: recover known alias matches without increasing false merges across project/entity fixtures.
No runtime installed.

## CAP-PROC-002 — Procurement Event Chain
Mechanism: immutable event/release model across planning → tender → award → contract → implementation, linked by process identity.
Evidence: OCDS schema and primer.
Blind spot addressed: tender-only snapshots miss pre-RFQ planning, amendments, cancellations, supplier changes and implementation.
Overlap: extends Pre-RFQ signals; does not replace them.
Disposition: PROMOTE_SCHEMA_PATTERN.
Acceptance test: reconstruct one buyer process from plan through latest known event while preserving superseded releases.

## CAP-LIN-003 — Evidence Lineage
Mechanism: run/job/dataset lineage; provenance of what produced/consumed evidence.
Evidence: OpenLineage + Marquez concepts.
Blind spot addressed: parallel adapters can lose transformation/run provenance even when source_locator survives.
Overlap: complements Evidence Authority and checkpointing.
Disposition: STUDY_PATTERN; native minimal implementation preferred before external stack.
Acceptance test: every promoted claim can trace source → adapter/run → normalization → claim → decision.

## CAP-DUR-004 — Durable Replay
Mechanism: append-only event history + deterministic replay; completed side effects are not repeated on recovery.
Evidence: Temporal event-history/replay documentation.
Blind spot addressed: cross-session recovery currently restores checkpoint state but not a full deterministic execution history.
Overlap: complements Continuity Contract.
Disposition: PATTERN_DONOR_ONLY.
Acceptance test before any dependency: demonstrate a real repeated crash/retry failure that checkpointing cannot solve, then benchmark native event log vs external runtime.
No Temporal installation justified yet.

## Growth rule
Novelty is not repository count. A mechanism is new only when it closes a measured NEXUS failure mode not already covered. Preserve HOLD/REJECT results to avoid repeated research.
