# EOE sourcing evidence pilot v0.1
Status: IMPLEMENTED AS REVIEWABLE CONTRACT ONLY; NOT INTEGRATED OR DEPLOYED
Date: 2026-10-14
Source governance: NEXUS Source Registry v1.8, Master Context v2.1.
Scope: EOE conversion press pilot. Do NOT map to PRJ-CAN-01 (necking/flanging/beading).
Project ID: PRJ-EOE-PILOT-01 (provisional; registry approval required before promotion).

## Input contract
P4 machine identity and interfaces: UNKNOWN.
Capacity: 600 EPM, total vs per-lane UNKNOWN.
Product: FA EOE sizes 300/307/401; tooling compatibility UNVERIFIED.
307 curl: engineer claim 94 mm vs uploaded specification 93.35 ± 0.15 mm, unresolved.
307 internal coating: engineer claim white vs uploaded specification Aluminum, unresolved.

## Evidence record
Required fields: project_id, source_locator, captured_at, source_date, supplier_name,
supplier_role, model, condition, listing_status, availability_checked_at,
capacity_epm, capacity_basis, tooling_sizes, quote_status, quote_value,
currency, incoterm, included_scope, contradictions, reviewer, next_action.
Enumerations:
listing_status = ACTIVE_VERIFIED | ADVERTISED_UNVERIFIED | SOLD | UNKNOWN
quote_status = FORMAL_QUOTE | PUBLIC_ADVERTISED_PRICE | NO_PRICE
capacity_basis = TOTAL | PER_LANE | UNKNOWN
Evidence categories: FACT | MEASUREMENT | CLAIM | ESTIMATE | ASSUMPTION | HYPOTHESIS | UNKNOWN.

## Deterministic acceptance cases
T1 SOLD listing must never become ACTIVE_VERIFIED.
T2 PUBLIC_ADVERTISED_PRICE must never become FORMAL_QUOTE.
T3 capacity_basis UNKNOWN must block capacity suitability PASS.
T4 cross-project EOE -> PRJ-CAN-01 spec copy must fail.
T5 outreach must fail without exact recipient, subject, payload, attachments,
   Persian explanation, latest thread check, and exact approval.
T6 recommended suppliers require source_locator and evidence category.

## Rollout gate
1. Inspect existing repo modules and tests; avoid duplicate engines.
2. Implement minimum parser/validator in existing sourcing lane, not a new platform.
3. Add automated tests T1–T6; run targeted tests and regressions.
4. Only then consider a PR. Do not merge/deploy without separate exact approval.
5. Track verified qualified suppliers, comparable quotes, cycle time, and costs.

## Rollback
Delete this pilot file/branch if superseded. Preserve audit and source evidence.
