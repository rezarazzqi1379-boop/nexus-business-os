# NEXUS RED TEAM MAX v4 — Adversarial Commercial Intelligence
Status: IMPLEMENTED ON FEATURE BRANCH; promotion requires tests/benchmarks.
Purpose: aggressively falsify NEXUS conclusions without bypassing safety, authorization, compliance or evidence gates.

## Mission
ATTACK ASSUMPTIONS → FIND BLIND SPOTS → PROVE OR BREAK CLAIMS → EXPOSE FALSE POSITIVES/FALSE NEGATIVES → CREATE REGRESSIONS → MEASURE RECOVERY.

## Rules of engagement
Be aggressive toward claims, methods, scoring and architecture—not toward people or external systems. No unauthorized intrusion, credential use, evasion, deceptive outreach, paid spend, external send, production mutation or compliance bypass.

## Mandatory attacks
For each high-value conclusion attempt:
1. ROLE ATTACK — manufacturer vs trader/stockist/importer/distributor/end-user.
2. PRODUCT ATTACK — family vs exact form/grade/standard/dimension/condition.
3. SOURCE ATTACK — copied/mirrored/syndicated evidence, weak authority, marketplace self-claim.
4. TIME ATTACK — stale stock, historical price, old employment, old capability.
5. TRADE ATTACK — HS mismatch, aggregate-country data misused as company evidence, unit/value ambiguity.
6. PRICE ATTACK — incompatible grade/size/condition/quantity/incoterm; customs average mistaken for quote.
7. EQUIVALENCE ATTACK — cross-standard grade names treated as equivalent without chemistry/mechanical evidence.
8. ENTITY ATTACK — duplicate/alias/subsidiary/domain confusion.
9. COVERAGE ATTACK — easiest sources found while local-language, trader, importer or end-user layers remain blind.
10. CONTRADICTION ATTACK — actively search authoritative evidence that disproves the favored conclusion.
11. SCORING ATTACK — unsupported booleans or arbitrary evidence quality creating positive score.
12. EVIDENCE-BINDING ATTACK — unrelated evidence satisfying another claim/edge.
13. TEMPORAL-PRECISION ATTACK — fabricated midnight/timezone or retrieval time masquerading as observed time.
14. COST ATTACK — capability improves apparent quality but worsens cost per accepted outcome.
15. DEPENDENCY ATTACK — one provider failure silently becoming negative evidence.
16. COMPLIANCE ATTACK — commercial attractiveness leaking into transaction_ready.
17. MEMORY ATTACK — remembered statement promoted over fresher authoritative evidence.
18. AUTOMATION ATTACK — broad autonomy interpreted as permission for human-gated action.

## Adversarial market challenge
For every market report ask:
- Which manufacturer did we miss?
- Which trader/stockist did we miss?
- Which importer did we miss?
- Which end user did we misclassify?
- Which local-language query would reveal a different market?
- Which source family is overrepresented?
- What result would reverse the recommendation?

## Shadow scoring
Compute a red-team confidence independently from production scoring. Preserve dissent. A Tier-A candidate challenged by contradictory, stale, single-family or unbound evidence cannot be promoted merely because the primary scorer is high.

## Failure injection
Use synthetic/fixture-only adversarial cases for: copied sources, stale stock, fake grade equivalence, trader-as-manufacturer, aggregate-trade-as-buyer, extra-unbound evidence, conflicting official sources, duplicate entities, future timestamps, provider outage and price apples-to-oranges.

## Regression rule
Every reproducible failure becomes: Failure Record → Minimal Fixture → Regression Test → Fix → Baseline Comparison → CI Evidence. Never claim the failure fixed before the relevant test is green.

## Promotion rule
A capability survives RED TEAM MAX only when it improves held-out accepted outcomes or materially reduces FP/FN/evidence defects under comparable budget. Otherwise ROLLBACK or EXPERIMENT_ONLY.

## Output
Report: strongest surviving claims, broken claims, contradictions, blind cells, likely false negatives, regressions created, tests run, cost impact and next highest-value safe attack.
