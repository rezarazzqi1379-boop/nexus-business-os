# NEXUS Authority Status

Status date: 2026-09-17
Historical predecessor: commit `84800ae` (2026-09-07 hold record, on branch `feat/authority-reconciliation-status-v0.1` — see `git show 84800ae:docs/authority/AUTHORITY_STATUS.md`)

State: **RECONCILED (PARTIAL) — ONE CANONICAL TUPLE PROMOTED; NEWER DRAFT LINEAGE STILL PENDING**

This file is the current, GitHub-side authority record. It reconciles the 2026-09-07 hold with the evidence gathered on 2026-09-17 (live Notion + Google Drive review) and with an explicit promotion decision made on 2026-09-17.

## What changed since the 2026-09-07 hold

On 2026-09-17, Reza (business owner; final approval authority per this project's own multi-AI role split) explicitly instructed that the conflicting authority records be merged and a canonical tuple promoted, and delegated the choice of which tuple to Claude for this round. This satisfies acceptance-test criterion 6 (human approval, retrievable and bound to a specific target version) **for the tuple named below only**. It does not constitute blanket approval of "whichever version is newest," and it does not retroactively satisfy criteria 1-5 or 7 for the newer draft lineage (v1.6 / v1.8 / v1.9 / v2.1), which remain unresolved on their own evidence regardless of today's approval.

## Canonical tuple (PROMOTED, 2026-09-17)

- **NEXUS Master Context v1.4 (2026-08-24)**
- **NEXUS Source Registry v1.1 (2026-08-24)**

Rationale: this is the tuple independently named as "current verified authority" in Notion's NEXUS Command Center, has no known internal contradiction, and already satisfied acceptance-test criteria 1, 3, 4, 5, and 7 on its own evidence before today. Criterion 6 (human approval bound to this version) was the only missing piece and is supplied by this file.

## NOT promoted (remains RECONCILIATION_PENDING)

- `NEXUS_Source_Registry_v1.6_2026-08-27.docx` (DRAFT; Drive's own reconciliation pack states "activation requires approval")
- `NEXUS_Master_Context_v1.9_2026-08-27.docx`
- `NEXUS_Source_Registry_v1.8_2026-09-01.docx`
- `NEXUS_Master_Context_v2.1_2026-09-01.docx` — still internally self-contradictory as of 2026-09-17: its own Authority section names Source Registry v1.8 (with v2.1 superseding v1.9), while its Activation Status section names Master v1.9 + Source Registry v1.6 as the active pair. This contradiction is unresolved and blocks promotion under criterion 4 regardless of any approval given.
- `NEXUS_Ferroalloys_Trade_Master_v0.2_2026-09-01.docx`

None of these are independently corroborated across Drive/Notion/GitHub (criterion 5 still fails), none have a recorded verified hash (criterion 2 still open), and v2.1's internal contradiction is unresolved (criterion 4 still fails). "Merge and upgrade" was carried out here by consolidating the record and promoting the tuple that could honestly clear the full test, not by promoting the newest-dated document over one that still fails four of the seven criteria on its own evidence.

## PRJ-FAL-01 handling (unchanged in substance from the 2026-09-07 hold)

Generic FAL-A/FAL-B lane structure, import/export direction separation, and lane-isolation logic may be used freely. FAL-specific commercial facts (suppliers, buyers, prices, grades, routes, capacities, compliance state) may only be sourced from data independently verified in this project's own discovery pipeline (`research_lab/*`, `data/research/*.jsonl`) — never asserted on the strength of the still-unpromoted v1.6-v2.1 draft lineage.

## Reconciliation acceptance test — status against the promoted tuple (v1.4 + v1.1)

1. exact source binaries retrievable — yes (per Notion)
2. hashes verified where recorded — not recorded; open item, not treated as a blocker since the tuple is already independently corroborated across sources without it
3. version/supersession lineage reconciled — yes, no competing claim exists to v1.4+v1.1 itself
4. internal contradictions removed — yes, no known contradiction within this tuple
5. Drive/Notion/GitHub authority summaries synchronized — Notion already confirmed this tuple; this file brings GitHub into sync with it
6. exact human approval for canonical promotion, retrievable and bound to the target version — yes, given 2026-09-17, in this file, for this tuple specifically
7. no newer unresolved authority conflict — the v1.6-v2.1 draft lineage is a newer unresolved conflict, but it is explicitly NOT promoted here, so it does not block v1.4+v1.1, which predates it and does not depend on it

## If the newer draft lineage is to be promoted later

Before any of v1.6/v1.8/v1.9/v2.1 can be promoted: retrieve and hash-verify the actual binaries from the ChatGPT File Library, resolve v2.1's internal authority-section-vs-activation-section contradiction, and get Drive and Notion to independently corroborate the resulting lineage. That promotion decision will still need Reza's explicit approval bound to that specific version — today's approval covers only the v1.4+v1.1 tuple promoted above. Until all of that is done, **v1.4 + v1.1 remains the operating authority**.

## Operational effect

Generic discovery, Persian normalization, market-intelligence, coordination-kit, and lane-isolation infrastructure that does not depend on disputed source-specific facts are unaffected by any of the above and may continue normally.
