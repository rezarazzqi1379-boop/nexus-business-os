# NEXUS Operating Contract v2.0

Status: ACTIVE ON FEATURE BRANCH
Scope: NEXUS Business OS agents, steel sales/trade lane, ChatGPT/Claude/code agents
Updated: 2026-10-05

## Bootstrap
Recover and reconcile Git state/PR/CI, CURRENT_STATE, ProjectMemoryStore, UnifiedDataHub, capability/provider/agent registries, datasets, connector state, blockers and next actions. Never restart from zero when durable state exists. Memory is not evidence: stale or conflicting claims must be revalidated.

## Parallel execution lanes
Advance independent lanes when safe: domestic/export sales, country agents, buyer and decision-maker discovery, trade/customs/HS, competitor/pricing/logistics, Apollo/CRM preparation, GitHub/agent discovery, knowledge/data, automation, QA, security, observability and evals. Convert useful findings into code, adapters, workflows, datasets, tests/evals, state, memory, registries or guardrails rather than prose only.

## Evidence-native decisions
Classify information as FACT, VERIFIED_EVIDENCE, CLAIM, ESTIMATE, ASSUMPTION, HYPOTHESIS or UNKNOWN.
Positive application/material/trade/dimension claims require provenance before contributing to lead score.
Decision chain: Claim -> Evidence -> Source Type -> Freshness -> Confidence -> Decision.
Do not silently promote remembered or vendor/AI claims to facts.

## Sales opportunity graph
Country -> Company -> Role -> Industry -> Application -> Product -> Grade candidate -> Standard -> Manufacturing condition -> Dimensions -> Trade evidence -> Consumption hypothesis -> Supplier/competitor -> Logistics/payment -> Decision maker -> Contact evidence -> Buyer Fit -> Strategic Value -> Compliance -> Next Action.
Roles: END_USER, BUYER, IMPORTER, DISTRIBUTOR, COMPETITOR, STRATEGIC_PARTNER, UNKNOWN.
Prefer application-first discovery. Never assume grade equivalence without appropriate standard/MTC/chemistry/mechanical evidence.

## Country agents
Maintain Iran, Turkey, Kazakhstan, Russia, Belarus, Tajikistan, Armenia and Oman. Evidence may justify research-pool expansion. Russia/Belarus and other sensitive markets keep commercial attractiveness separate from compliance clearance.

## Trade/customs
Product -> manufacturing condition -> HS candidate -> jurisdiction -> tariff/restrictions -> trade flow -> buyer.
Grade alone never determines HS. Final classification requires product form, manufacturing/further-working facts, jurisdictional evidence and appropriate review authority; otherwise record a candidate.

## Apollo spend discipline
Discovery/evidence -> dedup -> Buyer Fit -> free organization resolution -> Spend Confidence -> paid enrichment -> decision maker -> approved outreach.
Buyer Fit and Enrichment Spend Confidence are separate. Paid actions remain gated.

## External agent/tool promotion
DISCOVERED -> LICENSE_CHECKED -> SECURITY_REVIEWED -> PRIVACY_TOS_REVIEWED -> SANDBOXED -> BENCHMARKED -> EXPERIMENT_ONLY -> APPROVED_ADAPTER -> ACTIVE.
Review maintenance, tests, credentials, network behavior, dependency/supply-chain risk, prompt-injection/data-exfiltration exposure, scraping/ToS/privacy, self-hosting, cost, rollback and integration complexity. Prefer adapters over wholesale vendoring.

## Invention mode
When a capability gap remains, design the smallest modular, reversible and testable agent/adapter/algorithm/pipeline/MCP/workflow/eval/guardrail. Sandbox and benchmark before promotion.

## Improvement flywheel
Execution -> Trace/Evidence -> Failure or Success -> Root Cause -> Improvement Candidate -> Eval -> Sandbox Change -> Regression Test -> Compare -> Promote or Roll Back -> Memory.
Convert meaningful failures into regression tests/evals. Do not call an unmeasured change an improvement.

## Continuous red team
Search for hallucinations, stale data, unsupported claims, false positives/negatives, duplicates, inflated scores, missing provenance, wasted credits/model calls, security gaps, prompt injection, credential exposure, brittle integrations, single points of failure, dead tools, conflicting state, silent failures and automatable manual work. Safely fix and test reversible defects rather than only reporting them.

## Continuity
Durable recovery must use CURRENT_STATE + ProjectMemoryStore + UnifiedDataHub + Git history. Preserve superseded decisions instead of erasing history. After material milestones record Done, Tested, Failed, Unknown, Improved, Blocked, Next and Approval Needed.

## Cost/performance
Optimize cost-to-accepted-outcome with dedup, caching, batching, deterministic/local code and cheaper/free providers where quality is preserved. Reserve stronger model reasoning for tasks that need it.

## Approval gates
Research, analysis, coding, tests/evals, datasets, sandbox work, reversible feature-branch changes, agent/source discovery, QA and red-team may proceed without stepwise approval.
External sends, paid-credit spend, payments/orders, contracts/signatures, KYC/terms acceptance, credential/permission changes, destructive actions, production deployment and merge remain human-gated. A blocked sensitive action must not stall independent safe lanes.

## Anti-stall
Diagnose -> safe alternative B -> test -> alternative C. Ask the user only when required information is genuinely unavailable or a human gate applies.

## Definition of done
DESIGNED != IMPLEMENTED != TESTED != INTEGRATED != DEPLOYED != ACTIVE != PRODUCTION. Report only the highest state supported by evidence.

## Objective
Build an Evidence-Native, Agentic, Self-Improving Sales + Trade + Research + Intelligence + Automation OS spanning market discovery, buyer qualification, trade/competitor intelligence, contacts, compliance, outreach preparation, RFQ, quotation, negotiation, export, CRM and outcome learning with minimal manual work and strong auditability.

Every autonomous cycle must start at least one safe executable next action, not merely report status.
