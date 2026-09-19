# NEXUS Model/Runner Arena v0.1

Status: SHADOW EVALUATION CONTRACT — NO LIVE MODEL CALLS, NO PRODUCTION PROMOTION.

## Purpose

Provide one deterministic, model-neutral comparison surface for coding/review workers without creating another authority, orchestration system, provider router, or agent swarm.

Sequence:

`same task -> same repo snapshot -> same acceptance contract -> candidate execution evidence -> hard safety/quality gates -> deterministic comparison -> advisory result -> NEXUS promotion gate`

## Non-negotiable comparability

Candidates are comparable only when they receive the same task ID, exact repository snapshot and exact acceptance contract. Any mismatch fails closed.

## Hard rejection gates

A candidate cannot win if any of the following is observed:
- task incomplete;
- tests failed;
- regression introduced;
- authority/specification violation;
- cross-project contamination;
- security finding.

These gates dominate speed and cost. A faster/free candidate with an authority or security violation loses automatically.

## Ordering after hard gates

Among candidates that pass all hard gates, v0.1 prefers:
1. fewer human corrections;
2. lower elapsed time;
3. lower measured cost;
4. deterministic candidate ID tie-break.

No synthetic weighted business score is used. Raw measurements remain inspectable.

## Promotion boundary

Arena success is MEASUREMENT, not production authority. `promotable` is intentionally always false in v0.1. A winning model/runner still requires separate NEXUS evidence review and exact approval for any consequential integration, merge, deployment, permission expansion, spend, or sensitive-data route.

## First intended vertical

Use a sanitized coding/review task from NEXUS with no credentials, private commercial data, supplier pricing, customer identities or production state. Compare the current NEXUS coding path against the OpenCode shadow runner on the exact same repository snapshot.

## Required evidence record

At minimum preserve:
- candidate/runtime/model/provider ID and version;
- task ID;
- repository snapshot SHA;
- acceptance contract version;
- completion result;
- test result;
- regressions;
- authority/spec violations;
- cross-project contamination;
- security findings;
- human corrections;
- elapsed time;
- measured/estimated cost;
- raw source locator for the run output.

## Rollback

Remove this module/tests/docs. It owns no production state and performs no provider calls itself.
