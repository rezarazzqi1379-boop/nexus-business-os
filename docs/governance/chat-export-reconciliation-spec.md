# ChatGPT Export Inventory & Reconciliation Lane

Status: Design/Specification

## Goal
Provide a deterministic, local-first recovery path for official ChatGPT exports so NEXUS can inventory all conversations, map them to projects, detect cross-chat conflicts, and produce a migration/reconciliation manifest without mutating ChatGPT history.

## Required input
- Official ChatGPT export ZIP or extracted `conversations.json`.

## Pipeline
1. Validate export structure and record source hash/version metadata.
2. Parse conversations locally with zero network dependency.
3. Build conversation inventory: stable ID, title, timestamps, message count, attachment/file references when present, project hints, and recovery status.
4. Extract decision-relevant claims, instructions, constraints, file/catalog references, outreach state, and unresolved questions while preserving provenance.
5. Project-map each chat using evidence, not title alone.
6. Detect duplicate project state, conflicting instructions, stale/superseded decisions, cross-project parameter leakage, duplicate outreach risk, and unresolved authority conflicts.
7. Produce a reconciliation manifest linked to the Global Cross-Chat Operating Directive and existing NEXUS Decision Ledger.
8. Never silently merge contradictory states; emit conflicts for Council review.

## Evidence labels
Fact / Sourced Claim / Unsourced Claim / Estimate / Inference / Hypothesis / Assumption / Unknown.

## Required outputs
- `conversation_inventory.json`
- `project_chat_map.json`
- `cross_chat_conflicts.json`
- `supersession_candidates.json`
- `reconciliation_manifest.md`
- privacy-safe summary report

## Safety and privacy
- Local-first processing.
- No external upload by default.
- No mutation of ChatGPT history.
- No credential extraction or secret logging.
- Attachments/files are referenced by provenance; byte-level availability must not be assumed unless present.

## Adversarial tests
- malformed JSON/export schema
- duplicate conversation/message IDs
- missing title/timestamps
- Unicode and RTL text
- very large conversations
- empty/deleted nodes
- conflicting project labels
- same supplier/person appearing in multiple projects
- stale instruction superseded by newer authoritative evidence
- cross-project technical parameter contamination

## Success criteria
- deterministic output for identical input
- provenance retained for every material extracted state
- no network dependency
- no silent fact upgrading
- conflicts remain visible until resolved
- outputs can feed the existing Decision Ledger without creating a second source of truth

## Real replay blocker
A real official ChatGPT export is required to validate the parser and conflict detector against the user's full conversation history. Synthetic fixtures can be used before that input is available.
