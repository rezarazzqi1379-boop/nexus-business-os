# NEXUS Intelligence Dashboard v0.1

> Status: **SHADOW / REPLAY-VERIFIED / NOT PRODUCTION-PROMOTED**
>
> This dashboard separates deterministic replay evidence from real production/business outcomes. Green replay metrics are not claims of production ROI.

## Executive state

| Layer | Current state | Gate |
|---|---|---|
| Canonical source authority | Enforced | Tier A/B/C/D + project isolation |
| Verified state | Enforced | Evidence-backed transition only |
| Memory lifecycle | Enforced | Active vs superseded/invalidated/historical |
| Architecture selection | Enforced | Single-agent default; MAS conditional |
| Recovery runtime | Implemented | Bounded retry / replan / verified rewind |
| Recursive evolution | Shadow | Generation budgets + self-stop + audit |
| Production autonomy | **Not authorized** | Existing human gates remain |
| Commercial outcome proof | **Insufficient** | Needs live funnel/order/margin evidence |

## Intelligence replay scorecard

Benchmark: `nexus-intelligence-replay-v0.1`  
Type: deterministic contract/replay proxy — **not production telemetry**.

| Metric | Baseline | Candidate | Delta | Direction |
|---|---:|---:|---:|---|
| Recovery rate | 50% | 100% | +50 pp | Better |
| Source-authority violations | 1 | 0 | -1 | Better |
| Cross-project contamination | 1 | 0 | -1 | Better |
| Duplicate actions | 2 | 0 | -2 | Better |
| Stale-memory rejections | 1 | 4 | +3 | Better detection |
| Tool calls / accepted decision | 5.0 | 3.6 | -1.4 | 28% lower proxy overhead |
| Context units / accepted decision | 100 | 62 | -38 | 38% lower proxy context load |
| Human overrides | 2 | 1 | -1 | Directionally better; needs live validation |

**Replay verdict:** Candidate is `REPLAY_PROMOTABLE` under the bounded benchmark contract. This verdict does **not** authorize merge, deploy, external actions, production self-promotion, or claims of commercial improvement.

## Runtime control loop

`Intent -> Canonical Source -> Minimum Valid Memory -> Architecture Selection -> Plan -> Verify -> Act -> Verify State Transition -> Measure -> Learn`

On failure:

`Detect -> Classify -> Local bounded retry OR replan from verified checkpoint OR rewind -> re-verify -> continue`

Consequential recovery remains human-gated.

## Architecture policy

- Default: **Single Agent** with one verified state.
- Parallel research: only for largely independent evidence gathering plus one verified synthesis point.
- Centralized multi-agent: only when context degradation is material, task decomposition is useful, and independent verification exists.
- Worker consensus is never truth.
- More agents is never a success metric.

## Memory policy

- `ACTIVE`: eligible for decision context after project/scope checks.
- `SUPERSEDED` / `INVALIDATED`: excluded from current decision context, retained for contradiction lineage.
- `HISTORICAL`: audit/recovery only unless re-promoted by fresh evidence.
- Dynamic evidence with expiry must be refreshed before consequential use.
- Cross-project memory is excluded by default.

## What is actually proven

- The control contracts are implemented in code on PR #36.
- Architecture-selection replays exist for real NEXUS task classes.
- Memory validity and project isolation are tested.
- Verified state transitions are tested.
- Recovery/rewind decisions are bounded and tested.
- The deterministic replay benchmark shows a candidate improvement without safety/control regression.

## What is not yet proven

- Real p50/p95 decision latency reduction.
- Real token/API cost reduction.
- Real human correction/override reduction.
- Real supplier/buyer response lift.
- Real RFQ -> Quote -> Order -> Gross Margin improvement.
- Production-safe autonomous execution.

## Next proof gate

Instrument real NEXUS workflows using the same metric schema. A future generation may be production-promotable only when real telemetry confirms non-regression in authority/safety plus measurable improvement in at least one outcome/efficiency axis.
