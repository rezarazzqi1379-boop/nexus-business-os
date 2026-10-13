# NEXUS Outcome Management v1

Status: IMPLEMENTED / PENDING CI

## New management method
Manage the portfolio by verified outcome and bottleneck, not task volume.

Priority heuristic:
Evidence Strength × Expected Value × Conversion Lift / (1 + Cost + Risk)

This score never overrides contradiction, critical unknowns, project isolation, compliance or action gates.

## Operating cadence
RECOVER portfolio → identify one bottleneck per active project → rank reviewable outcomes → choose highest-value safe vertical proof → execute/test → record evidence delta → measure conversion/cost/failure delta → stop low-yield work → checkpoint.

## Required cycle record
- outcome_id / project_id
- objective
- current bottleneck
- evidence strength and source refs
- expected value and why
- conversion-stage lift
- cost/risk
- critical unknowns
- stopped/deprioritized work
- next safe action
- exact approval gate

## Learning
A winning pattern must reproduce. A failure pattern must become a regression, routing rule, source rule or prompt change. Repeated research with no evidence/conversion lift is a signal to change method, not search harder.
