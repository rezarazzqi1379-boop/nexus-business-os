# NEXUS Reuse / Rebuild / Install Decision v1 — 2026-10-13

Status: RESEARCHED / NOT INSTALLED / NOT DEPLOYED.
Authority: Source Registry and canonical masters. This document is an adapter evaluation, not permission to install, deploy or contact third parties.

## External candidates

| Candidate | Observed public evidence | Fit | Decision |
| --- | --- | --- | --- |
| freelancezero/freelancezero | GitHub README: MIT, Next.js 15, Prisma, Postgres, self-hosted marketplace; README describes v0.1 MVP foundation | Marketplace UI/data reference | Evaluate source and license; no production adoption |
| AmirRezaiyan/freelancer-platform | GitHub README: Django REST + React, jobs, bids, messaging | Alternate UI/API reference | Benchmark only |
| Twenty CRM + Activepieces | Published connector: contact/company/opportunity actions and MCP exposure | CRM adapter | Read-only sandbox first, no external writes |
| LangGraph / CrewAI | Public orchestration framework alternatives | Optional agent runner | No new runner until measured bottleneck |
| NEXUS existing Deal Room, Opportunity Graph, Marketplace Adapter, Runner Contract | Exact-head CI and branch evidence in PR #105 | Governing core | Retain and harden |

Source locators:
- https://github.com/freelancezero/freelancezero
- https://github.com/AmirRezaiyan/freelancer-platform
- https://www.activepieces.com/pieces/twenty
- https://github.com/langchain-ai/langgraph
- https://github.com/crewAIInc/crewAI

## Decision and non-goals

Do NOT fork or install a marketplace or CRM yet. The cheapest reversible proof is a read-only compatibility test using a synthetic opportunity and a schema adapter. Reject any candidate that requires secret copying, weak project isolation, hidden paid calls or autonomous outreach. Keep credentials at the provider.

A public README is a CLAIM about functionality, not a verified security audit. Recheck commits, license, vulnerabilities, data export, test quality and maintenance before any adoption.

## Steel backlog preservation

Steel commercial intelligence remains a separate lane from the freelance marketplace. Recover its latest project master and Source Registry before selecting a lead. Do not infer current demand from historic shipment, tender, or aggregate trade. Keep Hydrotester, KCl/SOP, Can Forming and Heat Treatment isolated. Existing relationship/stock/tender unresolved work must remain visible rather than marked completed by platform development.

## First pilot acceptance

1. One synthetic project-scoped buyer, provider and need flows through existing evidence and qualification gates.
2. No synthetic or unreviewed claim becomes a verified customer.
3. Exact-head CI passes and adversarial tests reject cross-project evidence.
4. Measured comparison with current NEXUS baseline: false acceptances, elapsed time, added dependencies and tokens.
5. Rollback is deleting the adapter from the Draft branch; no live CRM/marketplace data touched.

## ChatGPT scope

Repository changes alone do not change all ChatGPT chats, custom instructions or plugin configurations. Cross-chat rollout requires separately verified supported configuration and explicit approval for protected changes. Never report global activation from a GitHub commit.
