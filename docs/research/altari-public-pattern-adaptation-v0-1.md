# Altari / SkillTree Public-Pattern Adaptation v0.1

Date: 2026-08-23
Status: Shadow experiment; no deploy, send, payment, permission broadening, or production mutation.

## Purpose

Study publicly observable Altari / SkillTree product patterns and adapt the useful ideas into NEXUS Business OS without claiming access to paid/private workflows or creating a cosmetic 137-agent swarm.

## Verified public patterns

Public material states that SkillTree maps 137 AI jobs across seven departments: Sales, Deals, Marketing, Operations, Intelligence, Customer, and Back Office. It also describes a shared company knowledge base / "second brain", an onboarding interview, an audit engine, department dashboards, and runnable editable workflows. Public examples include Outbound Writer, Lead Sourcing, Cold-Call Scripts, Proposal Writer, Follow-Ups, Meeting Recaps, Content Engine, Carousel Designer, SEO Briefs, Client Onboarding, Client Ops, Status Updates, Prospect Dossiers, Competitor Watch, Market Sizing, Support Triage, FAQ Engine, Churn Watch, Invoicing, Reconciliation, Expense Coding, Prospect Research, Company Research, LinkedIn Outreach, Content Repurposer, Buying-Committee Mapping, Trend Analyst, Invoice Generator, and Support Answerer.

Sources:
- https://altari.ai/
- https://skilltree.altari.ai/
- https://altari.ai/guide/skilltree

## Important evidence boundary

The public website does **not** expose the internal paid workflow files, private prompts, hidden orchestration logic, connector credentials, client data, or complete implementation details for all 137 jobs. Therefore NEXUS must not label any reconstruction as an exact copy of those private internals. `src/nexus_control_plane/workforce.py` stores only publicly observed labels plus NEXUS-original capabilities, and marks provenance explicitly.

## What NEXUS should copy conceptually

1. One company brain, many task capabilities.
2. Job-by-job capability mapping rather than generic chatbot behavior.
3. Audit first: identify workflow leakage and ROI before automating.
4. Department-level command centers with shared state.
5. Finished-work outputs rather than prompt-only assistance.
6. Deployment order based on dependencies and measured value.
7. Business context injected into every job.

## What NEXUS should improve

NEXUS must retain stronger evidence and safety semantics than the public Altari marketing surface demonstrates:

- Fact / Claim / Estimate / Inference / Hypothesis / Assumption / Unknown remain distinct.
- Engineering/business authority hierarchy prevents supplier claims from overriding buyer-confirmed requirements.
- Duplicate Guard checks existing outreach before communication work.
- External actions use exact action-scoped approval, not generic batch permission.
- Opportunity discovery remains separate from outreach authority.
- Learning uses measured outcomes and versioned improvement proposals rather than uncontrolled self-modification.
- Every capability has provenance and an action class.
- Consequential capabilities fail closed without human approval.

## Target topology

Do not run 137 autonomous model loops. Represent the 137 jobs as a **capability catalog** routed through a small number of durable NEXUS roles:

`Signal -> Orchestrator -> Evidence Verifier -> domain capability -> QA/Evaluator -> Approval Gateway (when consequential) -> Execute -> Outcome Ledger -> Learning Governor`

Recommended role boundary:

- Orchestrator: selects work and capability; deterministic policy where possible.
- Evidence Verifier: provenance and epistemic class.
- Research/Intelligence Worker: prospect, company, competitor, market, opportunity research.
- Commercial Worker: lead sourcing, outbound drafts, follow-ups, proposals, objections.
- Engineering Reviewer: technical compatibility and authority checks.
- Operations Worker: documents, scheduling, onboarding, status workflows.
- Marketing Worker: content/reel/trend/SEO repurposing.
- Customer Worker: support triage/answer drafts/churn signals.
- Back Office Worker: invoice/report/reconciliation/expense preparation.
- QA/Evaluator: deterministic and adversarial checks.
- Approval Gateway: exact external/financial/destructive action authorization.
- Learning Governor: measured post-outcome improvement proposals.

This keeps model context separation where it is useful while avoiding dozens of cosmetic agents.

## Public-pattern to NEXUS mapping

- SkillTree Second Brain -> NEXUS Source-of-Truth + Company Digital Twin + Evidence Ledger.
- SkillTree Audit Engine -> NEXUS workflow audit + opportunity/value scoring + capability governor.
- SkillTree 137 jobs -> NEXUS capability registry, not 137 independent runtimes.
- SkillTree department dashboards -> NEXUS Operator Console / Command Center views.
- SkillTree onboarding interview -> NEXUS structured business-genome intake backed by evidence.
- SkillTree deployment playbook -> NEXUS dependency-aware capability promotion gates.
- Altari continuous improvement claim -> NEXUS Outcome Ledger -> pattern miner -> PR19 evolution proposal -> eval -> human promotion gate.

## Acceptance gates before wider integration

1. CI passes for the new registry and existing suite.
2. No existing Core invariant is bypassed.
3. Public-observed capabilities always retain source refs.
4. External/financial action classes always require human approval.
5. A real NEXUS commercial case is replayed through at least one Sales/Intelligence/Deals chain.
6. Outcome usefulness is measured against current baseline; no promotion merely because the architecture looks comprehensive.
7. Consolidation review determines whether this registry belongs in canonical Core or an incubator package.

## First real NEXUS pilot

Use one active procurement case and run:

`Inbound/current signal -> company research -> prospect/counterparty dossier -> requirement/evidence verification -> proposal/RFQ draft -> duplicate check -> human approval if sending -> observed outcome`

Measure correction rate, unsupported-claim rate, duplicate-action rate, time-to-decision, and human acceptance. This is more valuable than creating 137 speculative prompt files before proving the shared execution contract.
