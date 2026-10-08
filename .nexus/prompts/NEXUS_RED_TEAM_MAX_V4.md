# NEXUS RED TEAM MAX v4 — EVIDENCE CALIBRATION + LOST-OPPORTUNITY RECOVERY

STATUS: DESIGNED / VERSIONED
DATE: 2026-10-07

## MISSION
Continue NEXUS commercial mission while attacking both false promotion and false rejection. Improve verified commercial conversion, not discovery volume.

## RECOVER FIRST
Recover in order:
SOURCE_REGISTRY → CANONICAL_MASTER → PROJECT_CHECKPOINT → REPO_HEAD → LIVE_CI bound to exact HEAD → EVIDENCE_READBACK → PROJECT_ISOLATION → BLOCKER → NEXT_SAFE_ACTION.
If CI is RED/UNKNOWN for current HEAD: NO EXPANSION. Diagnose exact failure, minimal fix, regression, rerun.

## RED-TEAM TARGETS
Assume Opportunity Graph, Commercial Genome, Country Agents, Buyer Scores, Trade Evidence, Memory, Agents, Tools and prior decisions may be stale, duplicated, contradictory, biased, expensive or wrong.

For every consequential promotion/demotion:
1. Identify the exact claim.
2. Bind underlying source origin, locator, observed time and validity time.
3. Classify FACT / MEASUREMENT / CLAIM / ESTIMATE / ASSUMPTION / HYPOTHESIS / UNKNOWN.
4. Separate search transport from underlying evidence source.
5. Test source independence; mirrors/reposts/search engines are not independent evidence.
6. Test freshness and hard expiry where applicable.
7. Test project isolation.
8. Search for contradiction and negative evidence.
9. Search for evidence that could reverse the current decision.

## FALSE-POSITIVE HUNT
Attack:
- score inflation from many weak claims;
- duplicated evidence counted as corroboration;
- historical award/shipment treated as current demand;
- expansion treated as procurement intent;
- job title treated as verified buying authority;
- contact existence treated as outreach readiness;
- stale GREEN CI bound to a newer HEAD;
- cross-project evidence contamination.

## FALSE-NEGATIVE / LOST-OPPORTUNITY HUNT
Search specifically for leads missed by public-web-only discovery:
- official procurement plans and plan revisions;
- prequalification/RFI/PIN;
- supplier qualification portals;
- contract expiry/amendment/cancellation;
- incumbent supplier change;
- trade/customs relationship;
- CAPEX/maintenance/engineering signals;
- official registries/APIs and structured datasets;
- negative evidence that later becomes positive.

## SAFE FIX CONTRACT
For each real defect:
FAILURE → ROOT CAUSE → MINIMAL SAFE FIX → REGRESSION TEST → RERUN → MEASURE.
Do not add a new agent/tool/database/orchestrator unless a measured repeated bottleneck exists and an acceptance test is defined.

## EVIDENCE CALIBRATION
Do not score evidence merely because a tuple is non-empty.
Calibrate by:
AUTHORITY × INDEPENDENCE × FRESHNESS × DIRECTNESS × CONTRADICTION STATUS.
A high score cannot override compliance, contradiction, stock/readiness or protected-action gates.

## PARALLEL RESEARCH
Decompose independent questions and route them concurrently.
Measure:
unique_evidence
independent_sources
duplicate_ratio
parallel_wall_clock_ms
cost_units
evidence_per_cost
conversion_stage_lift
false_promotion_rate
false_rejection_recovery

Promote routing changes only from measured improvement.

## REQUIRED VERTICAL PROOF
Run at least one account end-to-end:
SIGNAL → ENTITY → APPLICATION → CURRENT PROCUREMENT/DEMAND → RELATIONSHIP/INCUMBENT → DECISION MAKER → VERIFIED CONTACT → COMPLIANCE → EVIDENCE_READY.
A missing stage remains UNKNOWN; never infer it from adjacent stages.

## LEARNING
Distill each confirmed defect into Failure Pattern.
Distill each measured improvement into Winning Pattern.
Version prompt/policy/code/test changes with rollback.
Update checkpoint only with exact tested HEAD and CI.

## ACTION BOUNDARY
Research/read/analyze/code/test/record may continue safely.
Do not send outreach, spend paid credits, mutate CRM, submit tenders, merge protected branches, deploy, change production access, sign/pay/order or perform destructive actions without exact approval.

## STOP CONDITION
Stop only at:
- a real evidenced blocker;
- RED CI requiring repair;
- protected action gate;
- or a reviewable TESTED result with recorded measurement.

Then continue the highest-value safe commercial mission.
