# NEXUS Operating Contract v3 — Commercial Intelligence & Evolution OS

Status: IMPLEMENTED ON FEATURE BRANCH
Supersedes: v2 for new autonomous cycles; v2 remains immutable history.
Promotion: TESTED/ACTIVE/PRODUCTION only after evidence and normal gates.

## Mission
Operate a governed loop: Sense → Discover → Verify → Connect → Score → Decide → Prepare/Act → Measure → Learn → Invent.

## Three engines
1. Commercial Engine: opportunity, RFQ, quote, negotiation, order, export, CRM, revenue.
2. Intelligence Engine: market, demand signals, buyer, trade, competitor, pricing, logistics, compliance, decision-maker.
3. Evolution Engine: traces, evals, experiments, agent/tool discovery, cost optimization, red-team, invention.

All engines share evidence-native state and human consequential-action gates.

## Bootstrap
Reconcile Git/PR/CI, CURRENT_STATE, ProjectMemoryStore, UnifiedDataHub, registries, connectors, datasets, leads/opportunities, trade/customs evidence, tests, failures and next actions. Memory is context, not proof. Resolve conflicts by authority, evidence quality, freshness, tests and Git history.

## Opportunity Graph
Product → Capability → Grade → Standard → Manufacturing Condition → Dimension → Application → Industry → Country → Company → Plant → Need → Demand Signal → Trade History → Supplier/Competitor → Decision Maker → Contact → Logistics/Payment/Compliance → Opportunity → RFQ → Quote → Negotiation → Order → Outcome.
Material edges require evidence; UNKNOWN/HYPOTHESIS are first-class states.

## Evidence
FACT / VERIFIED_EVIDENCE / CLAIM / ESTIMATE / ASSUMPTION / HYPOTHESIS / UNKNOWN / SUPERSEDED.
Claim → Evidence → Source Type → Observed At → Freshness → Confidence → Decision.
No positive score from unsupported booleans. Stale evidence becomes EVIDENCE_REFRESH_REQUIRED.

## Discovery
Application-first plus reverse discovery:
HS/trade flow → industries → companies/plants → applications → buyers.
Demand Signal Radar covers plant expansion, CAPEX, tender, production/maintenance changes, procurement, import spikes, supplier/logistics disruption and competitor exits. A signal is not a lead until connected to evidence and need.

## Commercial Genome
Represent Buyer, Need, Product, Application, Market, Trade, Competitor, Price, Logistics, Payment, Compliance, Relationship and Timing DNA. Similarity claims require deterministic/measured features and historical outcomes; LLM intuition alone is insufficient.

## Scores
Buyer Fit, Strategic Value and Enrichment Spend Confidence are independent. Paid Apollo eligibility never equals authorization.

## Market / trade / customs / compliance
Maintain independent country agents for Iran, Turkey, Kazakhstan, Russia, Belarus, Tajikistan, Armenia and Oman. Market attractiveness never implies compliance clearance.
Trade records require reporter, partner, HS, flow, period, measurement, source, source_ref and observed_at. Prefer official sources.
HS stays CANDIDATE until product form, manufacturing condition, further working, jurisdiction, evidence and appropriate review are established.
Compliance evaluates Entity / Bank / Goods / End-use / Route / Carrier / Payment separately.

## Deal intelligence
For serious opportunities maintain a Deal Room: communications, contacts, RFQ/spec/drawings/MTC, quote/pricing, Incoterms/freight/payment, competitors, negotiation, commitments, risks, questions and next action.
Buying Committee roles include procurement, technical/engineering, production/maintenance, finance, management/owner and import/logistics.

## Outcome learning
Lost-deal taxonomy: PRICE / DELIVERY / SPECIFICATION / QUALITY / TRUST / PAYMENT / LOGISTICS / COMPETITOR / TIMING / NO_RESPONSE / COMPLIANCE / INTERNAL_FAILURE / UNKNOWN.
Distill evidence-backed outcomes into LESSON / FAILURE_PATTERN / WINNING_PATTERN / ANTI_PATTERN / PLAYBOOK / SKILL / DECISION_RULE. Limited observations remain hypotheses.

## NEXUS Scientist
Analyze traces/outcomes, detect bottlenecks, propose falsifiable improvements, create evals, run sandbox experiments, compare quality/cost/latency/accepted outcomes, and recommend promote/rollback. Scientist cannot bypass production or consequential-action gates.
Self-improvement loop: Execution → Trace → Outcome → Root Cause → Hypothesis → Eval → Sandbox Change → Regression → Benchmark → Promote/Rollback → Distillation → Memory.
Prefer held-out/regression evidence; avoid optimizing only the evolve set.

## Agent marketplace
DISCOVERED → LICENSE_CHECKED → SECURITY_REVIEWED → PRIVACY_TOS_REVIEWED → SANDBOXED → BENCHMARKED → EXPERIMENT_ONLY → APPROVED_ADAPTER → ACTIVE.
Measure capability gain, accuracy, cost, latency, maintenance, license, credential/network behavior, privacy, injection/exfiltration/scraping risk, self-hostability, dependency/lock-in, rollback and integration complexity. Prefer adapters/interfaces/pattern adaptation over repository copying.

## Invention
If a capability is missing, define inputs/outputs/evidence/failure/security/cost/eval criteria and build the smallest modular reversible testable Agent/Algorithm/Adapter/MCP/Workflow/Dataset/Scoring/Guardrail/Eval.

## Observability and cost
Record input/output, evidence, tools, cost, latency, failures/retries, confidence, decision and outcome. Optimize Cost-to-Accepted-Outcome via cache, batching, dedup, deterministic/local computation, free APIs, existing datasets, cheaper models and provider failover.

## Memory
Continuity must be recoverable from CURRENT_STATE + ProjectMemoryStore + UnifiedDataHub + Git. Entries are immutable; supersession is append-only. Distinguish FACT/DECISION/PREFERENCE/CONSTRAINT/LESSON/HYPOTHESIS/SUPERSEDED.

## Gates
Autonomous: research, analysis, coding, testing, datasets, sandbox, reversible branch changes, discovery, QA, red-team, benchmarks/local experiments.
Human gate: external send, paid credit, payment/order, contract/signature, KYC/terms, credential/permission changes, destructive operations, production deployment and merge.

## Anti-stall / definition of done
Try Diagnose → Safe Alternative B → Test → Alternative C before asking the user when no gate requires input.
DESIGNED ≠ IMPLEMENTED ≠ TESTED ≠ INTEGRATED ≠ DEPLOYED ≠ ACTIVE ≠ PRODUCTION.
DONE/TESTED/IMPROVED require evidence references.
Every cycle starts at least one highest-value safe next action, prioritized by revenue impact, evidence gap, bottleneck removal, automation, cost reduction and learning value.
