# EXP-001 — Do failure-derived checks catch the real errors, without noise?

**Date:** 2026-09-24 · **Status:** IMPLEMENTED · TESTED (14 unit tests, also run on the owner's laptop: Python 3.10.12, pytest 9.1.1) · COMMITTED and PUSHED on a branch; CI step added — not merged.

## Hypothesis
Checks derived from recorded failures (FM-005 … FM-008) would have caught the procurement-document defects that three human/AI review rounds missed, without flagging correct internal documents.

## Method
Ran `python -m nexus_checks` unchanged over real historical files. Nothing was reconstructed except `v5-pre`, where the two lines the independent reviewer objected to were restored verbatim from the edit that replaced them.

| Dataset | What it is | Expected | Result |
|---|---|---|---|
| v3 combined RFQ (EN+ZH) | the files round 3 reviewed | parity gap + leaks | **29 errors** (2 parity: the gap a human found by hand; 27 hygiene: the leaks three rounds approved) |
| v4 split RFQs (8 files) | after round-3 fixes | leaks | **41 errors**, all FM-005 |
| v5-pre (2 files) | first v5 draft, before the independent review | the reviewer's I1 and I7 | **3/3 caught** (238 twice, 1000 kW once) |
| v5 final (8 files) | current drafts | clean | **0 errors** |
| v5 final, `--release` | release gate | draft banner must block | **8 errors** (one banner per file) |
| 22 internal documents (audits, reports, control) | history-heavy prose | no false positives | first run **4 false positives** → rule fixed (a line naming old AND current value describes the change) → **0** |

## Live repository run (laptop, 2026-09-24)
`python -m nexus_checks docs/procurement --repo .` → 41 errors, all in the eight v4 RFQs kept as audit history; with `--exclude '*_2026-09-22.md'` → 0 errors, 0 warnings across the remaining documents; git health clean.

## Result
- Every real defect in the four datasets was caught; zero false positives after one iteration.
- Promoted to: `CLAUDE.md` §5 (run before vendor release) and, by owner decision on 2026-09-24, to CI: a dedicated step in `.github/workflows/test.yml`. A dedicated step is needed because the existing `python -m unittest discover -s evals` collects 0 of these pytest-style tests (verified) and the pytest step only covers `tests/`. The document check runs only when `docs/procurement/` exists, i.e. after the procurement branch is merged; archived v4 RFQs are excluded by name.

## Limits (stated, not hidden)
- The checks catch leaks, one-sided edits, reused superseded numbers and git hazards: 4 of the ~20 round-4 finding classes. They do **not** catch meaning errors (the "650 mm is smaller" direction error, the 2000 kW mischaracterisation, FM-009 unstated basis). Those still need an independent reviewer.
- Parity is structural, not semantic.
- The superseded-value rules are a curated list; a new supersession must be added as a rule with its source.

## Rollback
Delete `nexus_checks/`, `evals/test_nexus_checks.py`, this file, and revert `CLAUDE.md` from `docs/system/CLAUDE_md_ruflo_boilerplate_2026-09-14.md`.
