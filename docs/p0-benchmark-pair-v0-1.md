# NEXUS P0 Benchmark Pair v0.1

## Purpose

Prove that one small control contract generalizes across two real commercial failure modes before adding more agents, MCPs, databases, dashboards, or autonomy.

## Benchmark A — Hydrotester

Primary failure modes:
- cross-project engineering parameter contamination;
- lower-authority supplier claims displacing buyer/project requirements;
- premature supplier qualification when blocking buyer requirements remain unknown.

Minimum metrics:
- cross-project contamination events allowed: 0;
- silent lower-authority overwrites allowed: 0;
- premature verified/compliant supplier claims allowed: 0;
- human correction count;
- time from evidence capture to qualification decision.

## Benchmark B — Can Forming

Primary failure modes:
- full-line quotations treated as equivalent to retrofit scope;
- necking-only vs full-forming scope collapsed into one comparison;
- supplier throughput claims compared without reference to required/current-line context;
- quote normalization hiding missing scope or evidence.

Minimum metrics:
- scope-collapsing errors allowed: 0;
- unsupported equivalence claims allowed: 0;
- human correction count;
- time from quote receipt to comparable scope matrix.

## Authority invariant

Authority is ordered from strongest to weakest:

A0 binding/legal/contractual requirement
A1 buyer/end-user confirmed requirement
A2 approved internal master specification
A3 verified project-specific record
A4 independent authoritative technical evidence
A5 supplier proposal/claim
A6 market/research evidence
A7 AI inference/hypothesis
A8 historical value from another project

A lower-authority record must never silently supersede a higher-authority record. A record from another project must never supersede a project-specific record without an explicit verified transfer.

## Maturity invariant

Always distinguish:
DISCOVERED → RESEARCHED → VERIFIED → RECOMMENDED → APPROVED → EXECUTED → MEASURED.

No later maturity state may be claimed without evidence.

## Promotion gate

This contract should be promoted into wider NEXUS core only after both real-case benchmarks are populated with real observations and reviewed. Passing unit/CI tests proves contract behavior only; it does not prove business effectiveness.

## Explicit non-goals

- no autonomous outreach;
- no database migration;
- no agent swarm;
- no MCP expansion;
- no probability scoring;
- no production deployment claim.
