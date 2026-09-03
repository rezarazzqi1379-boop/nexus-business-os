# NEXUS Systemic Audit — 2026-08-29

Basis: canonical Master Context v1.9 + Source Registry v1.6 recovered locally; current GitHub main/PR state and Hydrotester Gmail evidence refreshed live. This is an internal audit record, not authority expansion.

## Executive finding
NEXUS has strong fail-closed governance primitives, but current risk has shifted from missing controls to architecture/consolidation debt. The system has many overlapping historical Draft PRs, several duplicate/superseded lanes, a non-protected `main` branch, and incomplete production/runtime proof. The highest-value work is therefore convergence + measured vertical acceptance, not adding more agents or databases.

## P0 findings
1. **Main branch protection gap — FACT.** Live GitHub branch metadata reports `main` as `protected=false`. This means repository policy is not technically enforced at branch level even though NEXUS operating policy requires exact approval for protected/main merge and production changes. Do not change branch protection without exact approval because it is an access/governance mutation.
2. **Architecture sprawl — MEASUREMENT.** Many open Draft PRs remain from older authority lineages. Several are explicitly historical, stacked, superseded, or integration-only. Green historical CI is not current architectural fit. Continue selective transplant/convergence; do not bulk merge.
3. **Canonical storage drift — FACT.** The connected Drive canonical folder previously observed is behind current Master v1.9 / Registry v1.6. Repository binary canonical sync is also incomplete. Canonical selection must continue to use registry/version/hash evidence rather than Drive filename recency.
4. **Production state remains incomplete — UNKNOWN/FACT split.** GitHub main and CI are live; Vercel/Supabase reads have been observed; Railway direct console/runtime and OpenAI API auth smoke remain unverified. Deployment status is not application-health proof.
5. **Supabase access boundary incomplete — FACT.** RLS is enabled across many NEXUS tables but policies/data-path behavior remain unverified. This may be fail-closed rather than exposed, but production readiness cannot be claimed.
6. **Approval authority duplication risk — FACT.** Multiple historical branches implement or discuss approval gates. Current work must reuse one canonical exact-action approval authority; mutable booleans and textual approval references are not authority.

## Project portfolio review
- PRJ-HYD-01 Hydrotester: ACTIVE QUALIFICATION. Fresh vendor replies supersede the old “await replies” state. GH is conditional technical lead; Marley remains commercial benchmark with material throughput deviation; neither is PO-ready. New live evidence on 29 Aug: ANZ Global confirmed it is actively reviewing candidate OEMs against Rev.1.2 and expects its best quote by early next week. This is a pipeline-status FACT/CLAIM from the live thread, not a technical/commercial qualification result. Do not chase ANZ before that stated window unless new evidence requires it.
- PRJ-HTL-01 Heat Treatment: PAUSED_BY_MANAGEMENT. Preserve stable master; no supplier/RFQ restart. Throughput conflict remains a future revalidation hold.
- PRJ-KCL-01 KCl/SOP: COMMERCIAL REFRESH HOLD. Acceptance master governs; quantity/permit/destination/Incoterm/price/payment/sanctions/logistics are dynamic unknowns until live refresh. Historical 1,200 MT/month is not a current commitment.
- PRJ-CAN-01 Can Forming: ENGINEERING CLARIFICATION. D73/D99/400 g/model references remain evidence/candidate configuration, not stable buyer requirement. Final geometry/operations/rate need engineer confirmation before consequential comparison.

## Autonomy path review
Current safe target architecture:
`canonical state -> durable queue -> live access refresh -> authority route -> internal execution OR exact-approval preparation -> settlement plan -> complete/fail/defer -> audit/outcome/measurement`

Recent PR #86 work now supplies:
- access/authority registry;
- freshness-bound access observations;
- queue adapter;
- settlement planner;
- atomic non-failure defer that restores claim attempt budget;
- settlement executor that maps COMPLETE/RETRY/WAIT paths to durable store primitives while leaving HOLD non-mutating.

Exact-head CI evidence:
- defer primitive head `9d96a3438a9bdc4b3a95432050cf4c746af69594`: GitHub Actions run #829 SUCCESS.
- settlement-executor + systemic-audit head `852bcf4c2c466e22d884b60c6d3ce7ef85cb202e`: GitHub Actions run #832 SUCCESS.
- PR #83 measured vertical acceptance head `f93db28ce67537c58e0810015ae664d1fe8152be`: GitHub Actions run #815 SUCCESS.
These are implementation/test facts only; none is merged/deployed/production authority.

## Remaining design defect
`HOLD` currently has no explicit durable parked/manual-review state in the root AutonomyStore. Leaving a held leased item untouched eventually lets its lease expire and may consume future attempt budget when reclaimed. Do not paper over this by treating HOLD as failure or endless defer. Measure real hold cases first, then add the smallest explicit park/resume primitive if repeated need is demonstrated.

## Consolidation policy
Prioritize exact current-main behavior over branch age. Candidate dispositions:
- KEEP/REVIEW first: #86 access/authority + queue settlement; #84 supervisor approval hardening; #83 measured vertical acceptance; #78 OpenAI live-call hardening.
- SELECTIVE TRANSPLANT only: #79 evidence/opportunity components after known semantic fixes; #74 proposal delta if not already covered by current engineering vertical; #67/#68 exact-send/ingress if canonical approval/security owner still needs missing behavior.
- HISTORICAL/STACKED/INCUBATOR review for closure rather than merge: old integration shadows, parallel autonomy/runtime/eval/memory lanes and superseded source-authority PRs.

## Next measurable proof
Run one sanitized Hydrotester replay through the current main + candidate acceptance stack using the same evidence snapshot. Measure only observed values: human corrections, blocked unknowns, duplicate prevention, decision latency, policy violations and cross-project leakage. Unknown measurements remain UNKNOWN; do not fabricate denominators or success scores.

## External-action boundary
No email/message, CRM mutation, Drive canonical overwrite, Supabase policy/schema/data change, branch-protection change, merge, deploy, payment/order/signature or other consequential action is authorized by this audit.
