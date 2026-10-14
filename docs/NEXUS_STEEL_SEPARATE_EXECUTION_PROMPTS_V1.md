# NEXUS — Separate execution prompts v1 (2026-10-13)

Status: DRAFT / REVIEW REQUIRED. Project ID: PRJ-STEEL-SALES. Work on existing Draft PR #111 branch `nexus/steel-buyer-evidence-2026-10-13`. Read `docs/NEXUS_CROSS_CHAT_RECOVERY_2026-10-13.md`, latest Source Registry and relevant canonical master first. Revalidate HEAD/CI and evidence each run. No merge, deploy, external outreach, paid enrichment, live CRM writes or protected changes without exact approval. Do not confuse GitHub CI with production proof.

## Prompt 1 — Source authority and cross-chat recovery

Recover the latest GitHub main/branch SHA, PR #111 status, workflow runs and open issues. Find the latest Source Registry and steel-sales canonical master; compare versions and supersession history against the 2026-09-01 v1.8/v2.1 baselines. If a newer canonical source cannot be verified, mark SOURCE_UNVERIFIED. Produce a dated authority matrix (source, locator, version, authority, contradiction, next verification). Update only Draft-branch evidence. Acceptance: every promoted fact has a locator and an authority decision; no cross-project leakage.

## Prompt 2 — Steel tender original-source verification

Read existing register and primary-source validation. Verify RU-STEEL-001 notice 32616452647 and OM-STEEL-002 GT 147792321 at original operator/issuer, preserving exact publication and deadline claims, time zones, legal buyer, line items, eligibility, bid security, product grade and documents. Resolve conflicting Russian deadline only from authoritative documents; otherwise DEADLINE_CONFLICT. Record new dated observations under existing IDs, not duplicate buyers. Acceptance: no VERIFIED_ACTIVE_BUYER without official live status, product fit and participation terms.

## Prompt 3 — Buyer identity and decision-maker discovery

For existing named entities, verify legal registration, purchasing role, company website, procurement function and named decision-maker using public evidence. Separate buyer, supplier, broker, operator and unknown. Do not infer emails, private phone numbers, employment, or current procurement authority. No paid Apollo enrichment or contact without approval. Acceptance: each person-company link has a dated source or UNKNOWN; zero invented contacts.

## Prompt 4 — Customs, HS and product-to-buyer matching

Define the exact available steel product specifications before HS or buyer matching: alloy, flat/long, hot/cold rolled, width, thickness, grade, standard, quantity, origin and destination. Do not treat HS 7208 (width >=600 mm) as a match for 400 mm strip. Verify country and HS-specific shipment records rather than company_total counts. Acceptance: product match matrix with MATCH/MISMATCH/UNKNOWN, source, and reason; no claim of imports from ambiguous trade previews.

## Prompt 5 — Fail-closed code and regression tests

Inspect `nexus_steel_buyer_signal_gate.py` and `tests/test_nexus_steel_buyer_signal_gate.py`. First add failing tests for invalid URL hosts, duplicate legal entity + notice + product + date, contradictory deadline claims, project isolation, CLOSED_UNKNOWN taxonomy, unverified original document, and product mismatch. Implement the smallest backward-compatible fix without changing existing accepted classification semantics silently. Run focused tests, full relevant tests and CI for exact HEAD. Acceptance: no active buyer promotion on missing/contradictory evidence; all new tests green; record counts and SHA. Avoid schema expansion without acceptance tests.

## Prompt 6 — Independent QA, recording and handoff

Compare the changed branch against main, read all PR #111 changed files and tests, audit evidence for duplication, unsupported claims, data leakage and source authority. Separate DESIGNED/IMPLEMENTED/TESTED/MERGED/DEPLOYED/PRODUCTION. Record exact HEAD SHA, CI run ID/conclusion, observed limitations, source locators and rollback path in Draft PR. Update recovery pointer only after checking concurrent changes. Acceptance: reproducible evidence and no unsupported green/prod claims.

## Recommended order and non-interference

1. Authority recovery; 2. source validation and buyer identity in read-only parallel; 3. product/customs matching; 4. code/tests on the single existing Draft branch; 5. QA and continuity update. Before each write re-fetch the target file SHA and branch HEAD; do not overwrite concurrent work. Keep original evidence intact and record supersession instead of deletion.

## Verified baseline at preparation

- PR #111 draft; prior documentation commit `1e491e536b2b20cac90c701bf469ca71ed9e4ada`.
- GitHub Actions run `38387857078` SUCCESS on that exact commit (not on this prompts-only commit).
- Previous audit: `docs/NEXUS_STEEL_GATE_AUDIT_2026-10-13_V1.md`.
- No new buyer signals, verified contacts, or commercial conversions claimed by this file.
