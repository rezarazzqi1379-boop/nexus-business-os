# NEXUS Business Genome & Opportunity Engine v0.1

Status: **Implemented as a pure-domain shadow kernel; not deployed; no external writes.**

## Why this exists

NEXUS needs to learn from businesses, agents, non-agent automation, failures and unmet needs without creating agent sprawl. The unit of learning is not a vendor feature. It is:

`Business -> Process -> Friction -> Need -> Existing Solution -> Failure -> Metric -> Lesson -> Reusable Capability`

## Core stores

1. **Business Genome** — process/friction/need/solution/failure/capability observations.
2. **Problem Graph** — problems linked to affected entities, evidence, pain, frequency, urgency and ability-to-pay ordinals.
3. **Negative Knowledge** — rejected suppliers, failed strategies, invalid hypotheses, duplicate actions, unreliable sources and deprecated requirements.
4. **Opportunity Portfolio** — evidence-backed candidates classified PURSUE / RESEARCH / WATCH / REJECT.

## Evidence contract

Every important observation carries a source reference, observed date and epistemic class:

`fact | claim | estimate | inference | hypothesis | assumption | unknown`

Source presence does not prove the underlying claim. Authority remains explicit and ordinal. Predictions never become facts merely because they score highly.

## Research roles (logical roles, not necessarily separate agents)

- Business Scout
- Need Miner
- Failure Miner
- Capability Extractor
- Cross-Industry Transfer
- Future Needs Forecaster
- Red-Team Researcher
- Opportunity Portfolio Manager

Default implementation should be one orchestrator invoking bounded role contracts. A new autonomous agent is justified only by a measured bottleneck.

## Opportunity scoring

v0.1 deliberately uses an explainable ordinal score, not a probability. Positive factors include pain, frequency, ability to pay, urgency, market, access, strategic fit, differentiation and evidence strength. Penalties include capital, complexity, competition, time-to-revenue and risk.

Weak evidence forces RESEARCH even when the commercial story is attractive.

## Activation path

1. Run in shadow mode against real procurement observations.
2. Capture denominators: signals -> problems -> opportunities -> approved actions -> replies -> RFQs -> quotes -> orders.
3. Compare recommendations with human decisions and actual outcomes.
4. Store false positives and failed hypotheses in Negative Knowledge.
5. Adjust scoring only from observed outcomes; do not tune to anecdotes.
6. Promote to a connector-backed service only after repeated loop proof.

## Initial benchmark vertical

Industrial procurement remains the first benchmark because NEXUS already has real evidence, specifications, supplier conversations and observable outcomes. Business Genome is additive to the existing `Evidence -> Relationship -> Signal -> Opportunity -> Outcome` chain, not a replacement.

## Hard gates

- No automatic email/send/contract/payment/deployment authority.
- No uncontrolled self-modifying code.
- No web/email/document instruction may grant itself permissions.
- No cross-project requirement contamination.
- No uncalibrated score may be represented as a probability.
- No new registry/database merely to increase activity.
