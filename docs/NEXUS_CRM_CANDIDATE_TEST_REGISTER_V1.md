# NEXUS CRM Candidate Test Register v1

Status: CANDIDATE ASSESSMENT / NO THIRD-PARTY INSTALL VERIFIED.
Date: 2026-10-13. Project lane: STEEL_COMMERCIAL. This document does not replace any canonical project master.

## Candidate registry

| Candidate | Source | Intended test | Observed status |
| --- | --- | --- | --- |
| Twenty CRM | https://github.com/twentyhq/twenty | Companies, contacts, opportunities, custom fields, read-only export | RESEARCHED; NOT INSTALLED |
| EspoCRM | https://github.com/espocrm/espocrm | Accounts, contacts, leads, opportunities, export | RESEARCHED; NOT INSTALLED |
| Activepieces | https://github.com/activepieces/activepieces | Trigger/read-only flow and explicit external-write gate | RESEARCHED; NOT INSTALLED |
| LangGraph | https://github.com/langchain-ai/langgraph | Bounded graph vs existing NEXUS Supervisor | RESEARCHED; NOT INSTALLED |
| Freelancezero | https://github.com/freelancezero/freelancezero | Synthetic opportunity and Deal Room schema mapping | RESEARCHED; NOT INSTALLED |

## Mandatory pilot dataset (synthetic)

Account A: SANDBOX_STEEL_BUYER_A.
Contact A: SANDBOX_CONTACT_A, no real email/phone.
Opportunity A: SANDBOX_OPP_A, current demand UNKNOWN, authority UNKNOWN, project SANDBOX.
A separate unrelated SANDBOX_OTHER project must not be visible through the steel mapping.

## Test gates

T1: source repository and pinned version/commit independently read back.
T2: license, vulnerabilities, maintenance and dependency inventory reviewed.
T3: isolated install reproducible; no secret copied from Windows dirty working tree.
T4: synthetic company/contact/opportunity create and export round-trip verified.
T5: cross-project isolation and duplicate detection pass.
T6: unauthorized send, CRM write, paid API and deployment blocked.
T7: CPU/memory/runtime/operating cost measured, not guessed.
T8: uninstall/rollback and backup restore observed.

No candidate can be called INSTALLED or TESTED until T3-T8 have recorded commands, environment and actual results.

## Decision

Start with schema-only offline comparison of Twenty vs EspoCRM. Select one candidate for isolated installation only after T1-T2, host readiness and permission checks. Do not modify the local dirty branch `research/china-sourcing-v0.1`.
