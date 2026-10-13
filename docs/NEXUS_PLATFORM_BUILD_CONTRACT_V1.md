# NEXUS Platform Build Contract v1.0 — Codex and all runners

Status: DESIGN CONTRACT / NOT DEPLOYED. Applies to freelance and deal-intelligence sandbox only.
Authority: canonical Source Registry + project masters + existing NEXUS Global Kernel.
This contract does not supersede `docs/ADR-003-NEXUS-AGENT-SUPERVISOR.md` or `docs/ADR-003-CONNECTOR-CONTROL-PLANE.md`.

## Phase map and acceptance gates

| Phase | Responsible lane | Artifact | Gate |
| --- | --- | --- | --- |
| 0 Recover | Executive kernel | Source registry/master refs, HEAD, exact-head CI | Stop on red CI or unknown authority |
| 1 Environment | Evidence scout | Dated, project-scoped source manifest, permissions and freshness | No credentials/raw private data in prompts |
| 2 Discover | Commercial scout | Source-backed buyer, employer, freelancer, need hypotheses | Unknown != verified; dedupe mirrors |
| 3 Relate | Relationship reviewer | Typed evidence refs, source families, contradiction log | Independent sources and reviewer binding |
| 4 Match | Marketplace adapter | Research-only candidate + qualification | No external action authorization |
| 5 Deal | Deal Room | PROSPECT with next verification action | No invented contact/order history |
| 6 Measure | Rhythm analyst | Observed stage transitions and unknown denominators | No inferred conversion/repeat rate |
| 7 Invent | Experiment designer | Falsifiable, bounded idea proposal | Baseline, cost ceiling, rollback and acceptance test |
| 8 Implement | Codex/engineering runner | Smallest branch diff and focused tests | Draft branch only, no deploy/merge |
| 9 Verify | CI/reviewer | Exact-HEAD checks and adversarial test report | Runner done != accepted |
| 10 Record | Evidence recorder | Version, sources, tests, contradictions, open issues | No claims of cross-app persistence without readback |

## Runner contract

Every task packet MUST specify:
`task_id, project_id, canonical_source_refs, expected_artifact, evidence_requirements, tests, budget, risk_tier, allowed_actions, prohibited_actions, rollback`.

Every runner result MUST specify:
`task_id, project_id, commit_or_artifact_locator, evidence_refs, test_commands, observed_results, unresolved_unknowns, actual_cost_or_unknown, requested_approval`.

A runner can mark PRODUCED. Only independent verification can mark TESTED.
Protected actions remain human-approved. Cross-project results are rejected.

## Repeated environment intelligence

Gather connector health, API availability, provider permissions, source timestamps, GitHub branch/CI, evidence digests, and duplicate fingerprints **incrementally**.
Read changed data only. Record inaccessible systems as UNKNOWN. Do not crawl accounts or scrape sites beyond authorization, terms, or rate limits.
No claim of live customer demand without current source and identity proof.

## Controlled invention loop

For each proposed feature record:
`idea_id, problem, falsifiable_hypothesis, expected_commercial_value, baseline, minimum_test, cost_ceiling, failure_modes, rollback, owner, project_id`.
Reject novelty without measurable user value. Test against a frozen synthetic fixture before any pilot. Compare false positives, precision, latency, and evidence/token cost. Promote only with exact-head green CI and human review for external impact.

## Routing

- Executive kernel: resolve authority and select one bottleneck.
- Codex: implement isolated code changes and tests; no production permissions.
- Commercial scout: collect research candidates and raw locators.
- Evidence reviewer: resolve identities, independence, contradictions and freshness.
- Match/Deal modules: score and record without contact authority.
- QA: run positive, adversarial and regression checks.
- Recorder: maintain versioned decisions and rollback paths.

Do not instantiate more agents unless a benchmark shows a measurable repeated bottleneck.
All tools are replaceable adapters, never sources of authority.

## Immediate vertical proof

`synthetic source → scoped entity → reviewed relationship → verified need → match → HUMAN_REVIEW → PROSPECT`.
Never confuse a caller-provided receipt dict with authenticated review-service evidence.
The existing sandbox proof remains non-production until receipt authenticity is independently verified.

## Stop rules

Red CI; missing project authority; stale required evidence; identity conflict; unreviewed relationship; budget overrun; unauthorized external action.
When stopped, report exact failure and minimal reversible next step.
