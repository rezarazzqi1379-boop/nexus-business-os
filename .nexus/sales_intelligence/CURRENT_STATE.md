# NEXUS Steel Sales Intelligence — Current State

Updated: 2026-10-05
Owner: ASAK TEJARAT FATER
Execution owner: chatgpt-nexus
Status: ACTIVE_RESEARCH

## Mission
Build an evidence-led sales/export engine for Esfarayen-origin forged/alloy steel products. Discover and qualify buyers, channels, competitors, trade flows, decision makers, customs/compliance constraints, and sales opportunities without treating unverified claims as facts.

## Active markets
Turkey, Iran, Kazakhstan, Russia, Belarus, Tajikistan, Armenia, Oman.

## Product families in scope
20MnCr5/related case-hardening grades; 42CrMo4/related Q&T grades; 8620; C15; C45/CK series; S355J2G3; St52; other forged/alloy steel only when canonical product evidence supports it.
Grade equivalence is never assumed. Standard, condition, chemistry/mechanical properties, dimensions and MTC must be checked.

## Pipeline
live discovery -> company evidence -> material/application evidence -> trade evidence -> product/dimension fit -> competitor/channel classification -> compliance gate -> Apollo free organization resolution -> buyer score -> spend gate -> contact enrichment -> human-approved outreach -> RFQ -> quote -> negotiation -> PO.

## Current evidence-backed operating decisions
- Apollo is a resolver/enrichment/CRM layer, not the sole discovery engine.
- Free Apollo organization lookup is preferred before paid enrichment.
- Paid enrichment requires a spend gate.
- Russia and Belarus require an additional entity/bank/goods/end-use/route/carrier/payment compliance gate before consequential outreach or transaction work.
- End users with explicit material/application evidence outrank generic steel traders for buyer qualification.
- Buyer Fit and Enrichment Spend Confidence are separate scores.
- No external message, quote, order, payment, signature, deployment, merge, or irreversible action is authorized by this file.

## Apollo validation
Organization enrichment validated for Naci Uyar Demir Celik and Salda Metal.
Free organization resolution validated for Erkal Haddecilik, Efor Celik, Hur Celik, Modulsan and ReWeld.
Generic industry phrases produced false negatives; discover names/domains elsewhere first.

## Known candidate patterns
Turkey: gear/gearbox users (8620/20MnCr5), shaft/heavy machinery users (42CrMo4/C45), stockists/distributors, heavy forging.
Oman: machine shops/end users plus material suppliers for oil & gas/industrial maintenance.
Kazakhstan: mining/heavy machinery/repair/shaft/gear focus.
Armenia and Tajikistan: qualify with product-specific trade evidence before scale.
Russia/Belarus: technically relevant markets but compliance-separated from commercial attractiveness.

## Agent/repository adoption policy
External repositories are evidence/implementation candidates, not trusted dependencies. Review license, maintenance, credentials handling, network behavior, scraping/ToS risk, tests and rollback before adoption. Prefer adapters over copying whole systems.

## Continuity protocol
At the start of every substantial steel-sales task:
1. Read this file plus AGENTS.md and project memory.
2. Recover unresolved blockers and the last completed stage.
3. Do not re-run paid enrichment or outreach merely because context is missing.
4. Append durable evidence-backed progress to project memory/UnifiedDataHub where available.
5. Update this state when a material project decision or milestone changes.

## Next work
Build country candidate universes; add provider/capability registry for sales/trade; add deterministic buyer-fit/spend/compliance gates; qualify Tier-A companies; evaluate public agent repos in sandbox; connect approved adapters to existing NEXUS control plane; add tests; then prepare outreach packages for explicit approval.


## 2026-10-05 QA / agent-discovery checkpoint
- Draft PR #103 opened against nexus/consolidated-2026-09-30; GitHub now reports mergeable=true.
- No GitHub Actions workflow/status is currently attached to PR head 2595e3d6fd8b3e01813582fb8821e99bed9604db; do not claim tests passed until a runner executes them.
- UN Comtrade MCP candidate: cyanheads/un-comtrade-mcp-server. Strong fit for country/HS lookup and bilateral flows. Keep EXPERIMENT_ONLY until local license/credential/runtime review; UN data redistribution restrictions mean local user-key use is preferred over a hosted proxy.
- OpenEnrich candidate: openenrich/openenrich. Potential low-cost/local enrichment waterfall; AGPL-3.0 and SMTP/network behavior require license/security/ToS review before adoption.
- sales-intelligence-mcp and LeadPipe MCP are pattern candidates for scoring/CRM adapters, not trusted production dependencies.
- Provider selection principle: native/official data and existing connected tools first; public repos provide adapters/patterns only after measured sandbox evaluation.


## 2026-10-05 autonomous cycle checkpoint
- PR #103 head d7cdef5 was CI-tested by GitHub Actions run 37283892058: compile, canonical unittest, failure-derived eval suites and pytest regression all succeeded.
- ProjectMemoryStore contract is now restored at nexus_core/project_memory.py and the incompatible root duplicate was removed.
- Evidence-aware buyer scoring is implemented and covered by repository tests.
- Conservative HS candidate engine added: 722840 is only a candidate for alloy-steel bars/rods not further worked than forged; 722830 is only a candidate for other bars/rods not further worked than hot-rolled/hot-drawn/extruded. Grade alone never yields final classification.
- Country discovery is now application-first: gears/gearboxes -> case-hardening grades such as 20MnCr5/8620; shafts/heavy engineering -> 42CrMo4/C45; every lead still needs company-specific evidence.
- Merge/production remains gated; Apollo paid enrichment and external outreach remain unspent/unsent.


## Operating contract v2 activation
- .nexus/OPERATING_CONTRACT_V2.md is now the feature-branch operating contract for autonomous NEXUS cycles.
- AGENTS.md bootstraps substantial autonomous work from that contract.
- Contract codifies evidence-native scoring, agent promotion funnel, improvement/eval flywheel, anti-stall behavior, durable continuity, cost optimization and human gates.
- This is IMPLEMENTED on feat/steel-sales-intelligence-v1; ACTIVE/PRODUCTION status requires the normal merge/promotion gate.


## 2026-10-05 v2 evidence-quality cycle
- FACT: Operating Contract v2 head b238230 passed GitHub Actions tests run 37284820844 (#956).
- IMPLEMENTED after that tested head: steel_evidence_quality.py adds deterministic domain-based lead identity and evidence freshness states FRESH/STALE/UNKNOWN/INVALID_FUTURE, with regression tests.
- IMPLEMENTED after that tested head: nexus_milestone.py requires evidence refs for DONE/TESTED/IMPROVED machine-readable milestones, with regression tests.
- VERIFIED EXTERNAL EVIDENCE: UN Comtrade currently documents a free registered tier with up to 500 API calls/day and up to 100,000 records/call; use official Comtrade as the preferred trade-data provider before paid aggregators where coverage is sufficient.
- VERIFIED EXTERNAL EVIDENCE: EAEU official material lists HS 7228 30 for other alloy-steel bars/rods not further worked than hot-rolled/hot-drawn/extruded and 7228 40 for not further worked than forged. NEXUS still treats these as candidates until product/jurisdiction evidence is complete.
- NEXT: wait for CI on the new evidence-quality/milestone head, then wire freshness/dedup into country lead validation and create normalized trade-query adapter schema.


## RED TEAM MAX checkpoint
- TESTED FACT: head e1562c0 passed GitHub Actions run 37285002206 (#959).
- DEFECT FOUND/FIXED: country lead validation accepted evidence without freshness metadata. Validator now requires observed_at and rejects stale/future/unknown dates from supporting Tier-A; regression tests added.
- ARCHITECTURE DEFECT FOUND: ProjectMemoryStore describes itself as append-first but supersede() rewrites a namespace JSONL file. This preserves logical history in normal operation but is not a true append-only audit log and has weaker crash/concurrency semantics. Do not claim append-only durability until redesigned/tested.
- NEXT: implement append-only supersession events with backward-compatible query semantics and regression tests; then add normalized trade-query/result records with provenance and source timestamp.


## 2026-10-05 NEXUS v3 activation checkpoint
- IMPLEMENTED: Operating Contract v3, machine-readable operating policy v3, and v3 capability roadmap on feature branch.
- v3 supersedes v2 for future autonomous cycles; v2 retained as immutable historical contract.
- VERIFIED FAILURE: GitHub Actions run 37285877122 (#967) failed with 9 ProjectMemory tests because _supersessions() was referenced but missing. This invalidated the prior claim that append-only Memory was tested.
- FIX IMPLEMENTED: missing append-only supersession helpers added in commit c03f1543; requires new CI before TESTED status.
- v3 core additions: three-engine architecture, Opportunity Graph, Demand Signal Radar, Reverse Buyer Discovery, Commercial Genome, Deal Room, Lost Deal Autopsy, NEXUS Scientist, experience distillation, held-out eval discipline and cost-to-accepted-outcome.
- NEXT: require green CI, then implement Opportunity Graph + Demand Signal schemas and machine-validate v3 agent promotion stages.


## 2026-10-05 RED TEAM MAX v3
- CI run #976 was still in progress at bootstrap; no TESTED claim made for the latest Memory/Graph changes.
- STATE DRIFT FIXED: agent candidate registry now includes PRIVACY_TOS_REVIEWED required by Operating Contract v3.
- SCHEMA DRIFT FIXED: country lead evidence now declares type/ref/observed_at requirements and claim-only evidence cannot qualify Tier A.
- FALSE-POSITIVE LOOPHOLE FIXED: steel_country_leads now separates current evidence from current qualifying (non-CLAIM) evidence; validation clock is injectable for deterministic tests.
- GRAPH HARDENING IMPLEMENTED: FACT/VERIFIED_EVIDENCE graph edges require evidence and fresh observed_at; malformed/undated evidence is rejected.
- MEMORY FAILURE LESSON: persistence-format regressions require multi-event parse tests; prior CI #970 exposed literal newline serialization. Fix is implemented but remains untested until a green subsequent CI.
- NEXT: close CI; then implement reverse-buyer discovery contract and persist Opportunity Graph/Demand Signals into UnifiedDataHub with deterministic IDs.


## 2026-10-05 NEXUS v3 commercial/evolution cycle
- FAILED CI EVIDENCE: run #985 preserved the legacy suite at 1266 passed but new tests had 2 failures: Python banker rounding made 86.5 -> 86, and UnifiedDataHub rejected timezone-naive observed_at.
- FIX IMPLEMENTED: opportunity queue now uses deterministic Decimal ROUND_HALF_UP; v3 evidence adapter normalizes date/datetime input to timezone-aware ISO at the hub boundary.
- IMPLEMENTED: Commercial Genome baseline with explicit DNA dimensions, evidence-required historical outcomes, deterministic Jaccard feature similarity and comparable-case ranking.
- IMPLEMENTED: Deal Room contract with evidence-gated advanced stages and mandatory next action for open deals.
- IMPLEMENTED: NEXUS Scientist experiment contract; no evidence -> reject, no held-out eval -> human review, measured held-out gain with non-increased cost -> PROMOTE_CANDIDATE only, never production deployment.
- AGENT DISCOVERY: added self-evolve, Future AGI, Saber skills and sales-agent-foundation as DISCOVERED only. No external code integrated; promotion funnel still applies.
- NEXT: await CI; on green mark these capabilities TESTED, then add Lost Deal Autopsy/Experience Distillation and Agent Health observability.


## 2026-10-05 RED TEAM MAX v3 — commercial learning
- BOOTSTRAP FACT: PR #103 head 00663f6 was mergeable=true; CI #991 was pending, so previous commercial/evolution additions were not promoted to TESTED.
- BLIND SPOT FIXED: Commercial Genome now rejects unknown outcomes and blank opportunity IDs; evidenced outcome is still mandatory.
- BLIND SPOT FIXED: NEXUS Scientist rejects out-of-range metrics and negative costs before any promotion recommendation.
- BLIND SPOT FIXED: LOST Deal Room state requires a loss reason.
- IMPLEMENTED: lost_deal_autopsy with controlled reason taxonomy; specific loss reasons require evidence. Repeated identical evidenced patterns become LESSON only at >=3 cases; smaller samples remain HYPOTHESIS.
- OPEN DESIGN ISSUE: v3 evidence adapter currently normalizes date-only observed_at to UTC midnight. This is convenient but can imply precision not present in source evidence. Next evolution should separate observed_date/source_precision from retrieved_at timestamp instead of silently manufacturing precision.
- NEXT: await CI; implement explicit evidence temporal precision + Agent Health observability; then connect distilled patterns to ProjectMemory only after evidence refs and threshold validation.


## 2026-10-05 NEXUS v3 evidence/observability cycle
- BOOTSTRAP: head 8234dc8; PR #103 mergeable=true; CI #995 pending. No premature TESTED promotion.
- IMPLEMENTED: EvidenceTime separates source observed_value + temporal precision from timezone-aware retrieved_at; avoids manufacturing source precision.
- IMPLEMENTED: AgentTrace + deterministic Agent Health Score covering success, evidence use, silent failure and retry penalty; invalid negative cost/latency/retry traces fail closed.
- IMPLEMENTED: Experience Distillation memory gate. Promoted knowledge requires evidence and >=3 cases; single-case observations may persist only as HYPOTHESIS.
- IMPLEMENTED: Commercial Genome historical outcome aggregation ignores UNKNOWN/unevidenced outcomes and reports deterministic comparable-case counts/outcome distribution.
- NEXT: CI closure; integrate EvidenceTime into v3 hub adapter without breaking existing source dates; then wire eligible distilled knowledge into append-only ProjectMemory and add cost-to-accepted-outcome metrics.
