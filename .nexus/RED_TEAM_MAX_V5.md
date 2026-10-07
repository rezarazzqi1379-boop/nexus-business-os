# NEXUS RED TEAM MAX v5 — Historical + Adversarial System Audit
Status: IMPLEMENTED ON FEATURE BRANCH; promotion requires regression/benchmark evidence.
Extends RED TEAM MAX v4 and preserves the v3 principle: assume historical NEXUS state may be wrong, stale, contradictory, costly or incomplete.

## Mission
Re-audit the system, not only the latest answer:
Opportunity Graph + Commercial Genome + Country Agents + Buyer Scores + Trade Evidence + Memory + Agents + Tools + MCP/API + Architecture + historical decisions.

Cycle:
RE-AUDIT EVIDENCE → FIND FP/FN → FIND BLIND SPOTS → DETECT STATE DRIFT → AUTOPSY LOST OPPORTUNITIES/FAILURES → BENCHMARK AGENTS/TOOLS/ARCHITECTURE → SAFE FIX → REGRESSION TEST → MEASURE → PROMOTE/ROLLBACK → DISTILL LESSONS → UPDATE STATE/MEMORY → RESUME COMMERCIAL MISSION.

## Historical Decision Autopsy
For material prior decisions record:
decision_id, original_claim, original_evidence, original_time, action/outcome, current_evidence, contradiction, freshness, failure_mode, commercial_cost, supersession_required, regression_candidate.
Never rewrite history. Preserve original decision and append a superseding record when evidence changes.

## State Drift Audit
Compare current reality against stored state for company roles, product capability, stock, price, contacts, trade flows, compliance, provider/tool health, branch/CI status and opportunity stage.
Classify: CONSISTENT / DRIFTED / STALE / CONTRADICTED / UNKNOWN.
Drift in volatile fields (stock, price, employment, sanctions/compliance, availability) gets priority.

## Lost Opportunity Autopsy
For LOST, abandoned, stalled or never-promoted candidates test whether the cause was real or a NEXUS failure:
SOURCE_GAP, QUERY_GAP, LANGUAGE_GAP, ROLE_MISCLASSIFICATION, PRODUCT_FIT_ERROR, BAD_HS, STALE_DATA, ENTITY_RESOLUTION, DEDUP, BAD_SCORE, CONTACT_FAILURE, PROVIDER_FAILURE, COST_GATE, COMPLIANCE_FILTER, HUMAN_GATE, TIMING, UNKNOWN.
Estimate recoverability and commercial value before reopening.

## Architecture Attack
Challenge whether Opportunity Graph edges are evidence-bound; Commercial Genome outcomes have outcome evidence; Country Agents share discovery fabric without silos; Buyer Scores cannot reward unsupported features; Memory respects supersession; provider failures cannot become negative market evidence; agent/tool additions improve held-out outcomes.

## Tool/Agent Benchmark
For competing Agent/Tool/MCP/API methods compare on the same benchmark and budget: accepted-result precision, recall/coverage, evidence quality, latency, monetary/token/credit cost, reliability and commercial contribution.
Do not promote a more complex tool unless measured value improves.

## Safe Fix Protocol
Reproduce → minimal fixture → root cause → smallest reversible fix → focused test → full regression → benchmark/ablation when material → document evidence.
No green test = no TESTED claim. No measured improvement = no PROMOTED claim.

## Aggressive attacks
Role, product/form/grade/dimension, source independence, freshness, trade inference, price comparability, grade equivalence, entity duplication, coverage, contradiction, scoring, evidence binding, temporal precision, cost, provider dependency, compliance leakage, memory authority and automation authorization.

## Output
Report: broken historical assumptions, surviving claims, state drift, FP/FN, blind cells, lost opportunities worth reopening, architecture defects, tool/agent winners and losers, safe fixes, regressions, measured improvement, supersessions and next highest-value safe action.

## Hard boundary
Aggressive means epistemically and technically adversarial, never unauthorized. No intrusion, credential misuse, deceptive outreach, paid spend, external send, production mutation, compliance bypass, destructive action or merge without the required human gate.
