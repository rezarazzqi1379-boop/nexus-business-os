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
5. **Outcome Ledger** — append-only shadow outcome events separated by alignment, stage success, final success, false positive, safety failure and open state.
6. **Pattern Miner** — cross-project repeated failure/success detection; single anecdotes cannot create improvement proposals.

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

Weak evidence or decision-critical unknowns force RESEARCH even when the commercial story is attractive.

## Learning loop

1. Run shadow recommendations against real procurement observations.
2. Capture human decisions only when supported by executed actions or explicit positions.
3. Separate stage outcomes (reply/RFQ/quote) from final outcomes (contract/order).
4. Convert validated observations into Outcome Ledger entries.
5. Generate Negative Knowledge only for observed unsuccessful PURSUE outcomes or safety failures; open cases are not failures.
6. Mine repeated patterns only after minimum occurrence and cross-project-diversity gates are met.
7. Pattern eligibility is evidence for an improvement proposal, not authorization to change production.
8. Any eventual agent/tool change remains governed by the separate bounded evolution mechanism and human approval.

## Pattern Miner gates

- `min_occurrences >= 2`; a single anecdote is never generalizable.
- default `min_distinct_projects = 2`; repetition inside one project does not establish a reusable cross-project pattern.
- conflicting duplicate event or ledger IDs fail closed.
- success patterns are mined only from observed stage/final successes; alignment/open states are excluded.
- no pattern miner output can tune scoring weights or alter an agent directly.

## Initial benchmark vertical

Industrial procurement remains the first benchmark because NEXUS already has real evidence, specifications, supplier conversations and observable outcomes. Business Genome is additive to the existing `Evidence -> Relationship -> Signal -> Opportunity -> Outcome` chain, not a replacement.

## Hard gates

- No automatic email/send/contract/payment/deployment authority.
- No uncontrolled self-modifying code.
- No web/email/document instruction may grant itself permissions.
- No cross-project requirement contamination.
- No uncalibrated score may be represented as a probability.
- No missing outcome may be interpreted as failure.
- No single case may become a reusable failure/success pattern.
- No new registry/database merely to increase activity.
