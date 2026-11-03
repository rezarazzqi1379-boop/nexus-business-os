# NEXUS Commercial Portfolio — Acceptance and Operations Gate (2026-11-01)

Status: **REVIEW / NOT YET COMMERCIALLY ACCEPTED**. This is a review proposal, not live execution evidence or authority to contact buyers.

## Scope and authority

- Existing governed NEXUS architecture; no parallel data store, scheduler, or approval system.
- Recover Source Registry, project masters, and current main before importing records.
- Work research and Codex engineering remain separate execution roles, coordinated by existing project/lane identifiers.
- Owner's standing delegation permits bounded read-only research, testing, evidence preparation; external messages, bids, purchases, production deployment require specific approval.
- Keep active procurement cases separate from *new opportunity discovery*; neither may consume the other's evidence or identifiers.

## Historical baseline (not current performance)

2026-10-28 commercial pilot: 3 source notices, 0 independently verified, 0 actionable, 1 INVESTIGATE, 2 REJECT, completeness 33.33%. This is a single small World Bank steel query sample, not a market coverage claim.

## Initial portfolio routing (provisional, subject to source registry/master reconciliation)

| Lane | Subject | Status | Next evidence |
| --- | --- | --- | --- |
| Active procurement | Yaxing OCTG hydrotester, Rev.1.2 | INVESTIGATE | 2026-11-03 visit occurrence; actual machine duty-point/FAT proof; current written quotation |
| Active procurement | Other hydrotester vendors | INVESTIGATE | Comparable guaranteed pressure/throughput matrix, full quotation |
| Existing industrial projects | Steel rolling, forging press, OCTG and other equipment | RECOVER | Current project masters, actual buyer requirements, source-backed leads |
| External tender | MASHZAVOD 1263230 stainless sheet | INVESTIGATE | Original portal, eligibility, payment/guarantees, supply economics |
| External tender | 1264026 steel pipe | INVESTIGATE | Original tender and technical documents |
| New business | Cross-sector industrial opportunity discovery | NOT YET DEMONSTRATED | Bounded live-source batch with provenance, dedup, independent verification |

A reported Work local UnifiedDataHub write and 16 related passing tests are *claims pending read-back against the authoritative NEXUS store*. Do not treat local observations as centrally integrated.

## Smallest acceptance run

1. Pin exact main SHA and current source-registry/project-master digests.
2. Execute existing `.github/workflows/nexus-commercial-pilot.yml` on main, if authorized and available; retain immutable summary, source bytes/hash and management report.
3. Conduct one bounded read-only discovery batch **outside the current World Bank steel sample**, with explicit project/lane, source licences, access budgets, timestamps, original notices and duplicate checks.
4. Verify buyer identity, demand, specifications, deadline, eligibility and feasibility independently. UNKNOWN stays UNKNOWN.
5. Attempt authorized controlled import using existing NEXUS APIs/stores; read back by stable ID after restart or independent session; preserve CLAIM/HOLD and conflicting evidence.
6. Reproduce and diagnose reported `no eligible agent` routing blocker; do not bypass qualification.
7. Compare equivalent baseline/new batch metrics; do not claim uplift from different sample scopes.
8. Record CI/run IDs, exact commit, source hashes, evidence location, blockers, acceptance decision and next owner.

## Acceptance criteria

- Technical: focused and regression CI on immutable head; no safety regressions.
- Operational: real-source run, accepted Supervisor, valid checkpoint, replay/dedup and source provenance.
- Data: independently verified persistence and read-back in authoritative store; project isolation; version/supersession preserved.
- Commercial: at least one **independently verified and decision-ready** current opportunity, or explicit rejection with evidence and further bounded discovery. Zero qualified means commercial HOLD.
- External action: separate exact-scope approval; no outreach implied by acceptance.

## Required management report

Count unique discovered / investigated / independently verified / qualified / actionable; show denominator, sample and source dates. Provide top opportunities with primary evidence, economic assumptions and missing terms. Distinguish prepared drafts, approved outreach, actual responses, contract awards and confirmed revenue. End with PASS / CONDITIONAL / HOLD and exact blockers.

## Deployment

Do not infer persistent operation from ephemeral GitHub Actions. Existing scheduled NEXUS automations are not proof of a running commercial source scheduler. Production deployment remains gated by target, storage, cost and rollback approval.
