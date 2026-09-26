# NEXUS CURRENT STATE
Last updated: 2026-09-26 by Claude Code (branch `feat/state-freshness-v0.1`, worktree off
`integ/2026-09-26`) -- full rewrite (RULE below: overwrite stale sections, don't just append).
Previous version (2026-09-19) is in git history at this same path if any old wording is needed.

RULE: Read this file FIRST in any new session before doing anything else. Overwrite stale
sections when updating -- do not just append. This file governs `docs/procurement/`,
`docs/expert_foundry/`, `docs/authority/`, `docs/system/`, `.nexus/steel/`,
`.nexus/expert_foundry/`, `AGENTS.md` and `nexus_checks/` (see
`.nexus/state/STATE_GOVERNANCE.json`) -- `python -m nexus_checks --state --repo .` fails loud
if any of those move without this file being touched in the same window (tolerance 2 days).

## ⚠️ ENVIRONMENT WARNING — TWO INDEPENDENT CLONES EXIST (still true, unchanged since 2026-09-07)
- Clone A (Claude Code): `C:/Users/AvallPc/nexus-business-os`
- Clone B (Codex/ChatGPT): `C:\Users\AvallPc\.codex\.chatgpt-projects\g-p-6a8492b077348191a541806c6ff52d75\nexus-business-os`

Separate `.git` object stores, same GitHub remote. A commit pushed from one is invisible in the
other until that clone runs `git fetch`. Any cross-AI comparison MUST fetch first, or SHAs will
look "missing" when they're only unfetched (FM-011 is this exact class of error, just applied to
a single ref instead of a whole clone).

## ⚠️ PYTHON ENVIRONMENT WARNING (unchanged)
`python` on PATH is a Windows Store stub with no project dependencies. Use `.venv/Scripts/python.exe`
in each clone; always say so explicitly in any instruction to any AI/agent.

## ⚠️ NEVER `git stash` ON THIS REPO (new rule, 2026-09-26, FM-012)
A `git stash` / `git stash pop` cycle on 2026-09-24 left one file staged while the commit
message claimed 15; the reported test counts (682/501) were read from the working tree, not
the commit. CI was green because it only tests what's actually there. Rule now: never stash to
set work aside; use a WIP commit or a separate worktree. Before reporting any commit, run
`git show --stat <sha>` and check it against the message; get test counts from a **fresh
worktree of the final SHA**, never the working tree that produced it. This is why this session
used `git worktree add` instead of working in place.

## AUTHORITY STATUS — RECONCILED (PARTIAL), corrected in this update
**Finding while doing this rewrite:** the 2026-09-19 version of this file still said
`AUTHORITY_CONFLICT / RECONCILIATION_PENDING since 2026-08-28`, but `docs/authority/AUTHORITY_STATUS.md`
was updated on **2026-09-17** -- two days *before* that CURRENT_STATE.md revision -- to
`RECONCILED (PARTIAL)`. This file simply never got the update; a live example of the class of
staleness `nexus_checks.state_freshness` (added this session, see below) now catches
mechanically for governed docs, though this particular miss predates that check and was found
by reading `AUTHORITY_STATUS.md` directly, not by the tool.

Current state, per `docs/authority/AUTHORITY_STATUS.md` (dated 2026-09-17, Reza's explicit
promotion decision):
- **Canonical, promoted:** NEXUS Master Context v1.4 + Source Registry v1.1 (both 2026-08-24).
- **NOT promoted, still RECONCILIATION_PENDING:** the v1.6/v1.8/v1.9/v2.1 draft lineage (v2.1 is
  also internally self-contradictory -- its own Authority section names v1.8/v2.1 as governing
  while its Activation section names v1.9/v1.6 as active).
- `docs/expert_foundry/PROJECT_CONTROL_PRJ-STEEL-ROLLING-LINE-01.md` and `.nexus/steel/CHECKPOINT.md`
  already had this right (`Master Context v1.4 + Source Registry v1.1, commit 68c0832`); this
  file was the one out of sync.
- Do not cite `PRJ-FAL-01-EV-001` ("Pars Damghan") as a registered CLAIM anywhere until the
  draft lineage reconciles. Generic FAL-A/FAL-B lane structure is fine to use regardless.

## PROJECT PRIORITIES (confirmed 2026-09-05, still not disputed)
- Geography: Iran = Tier 0. Tiers 1-4 are priors, not fixed.
- First commercial vertical: PRJ-FAL-01 (Ferroalloys) — proceeds regardless of the draft-lineage
  dispute above. FAL-A: ferromanganese import. FAL-B: ferrosilicon export. Lanes stay isolated.
- After FAL: KCl/SOP → Hydrotester → Can Forming. Heat Treatment paused.
- No live Iranian source has been contacted (`LIVE_PROVIDER_UNWIRED` in `iran_source_providers.py`,
  all 8 source families). Deliberate hold, not inferrable from "continue autonomously". Get real
  export-control/sanctions legal advice before any live outreach.

## ARCHITECTURE DECISIONS (settled, don't re-litigate)
- REJECTED: live AI-to-AI autonomous bridge / daemon that lets one AI execute the other's
  instructions. ACCEPTED: GitHub-backed Coordination Kit (`task_handoff.py` → `coordination_kit.py`).
- The old `nexus_brain` / `nexus_control_plane` graph-execution architecture was deliberately
  deleted at `c7e5c36` (2026-08-25 release commit) in favor of the current flat module layout.
  `feature/nexus-forge-loop-v0-1` (src/nexus_control_plane/forge.py and siblings, ~7400 lines,
  branch-only -- not a path in any tree that includes main)
  rebuilt a similar idea afterwards on a branch that was **never merged** -- that path does not
  exist on any live branch; it is kept only as an unmerged design-idea reference, not a pointer
  to real code. Same for the `nexus_brain_v0-1..v0-4` cluster -- abandoned, unmerged, superseded.
- `human_authorized_extra_rounds` (bool) → replaced by `extra_round_approval_id` bound to a real
  `ApprovalStore` grant. Known gap: `verify_handoff_package()` doesn't independently re-check this
  against a live store in a separate process.
- `cross_project_touch`: v1=bool, v2=tuple, not unified; adapter maps v1 False→v2 (), v1 True→v2
  fail-closed UNKNOWN sentinel.
- `TestEvidenceV2` distinguishes CALLER_DECLARED vs INDEPENDENTLY_CAPTURED; `capture_test_evidence()`
  structurally cannot accept a caller-supplied head_sha.
- Secret guard is pattern-based only -- "no findings" is not "confirmed secret-free" (documented,
  not solved).
- Review-round budget: 2 automatic, 3rd requires a real human-set approval record.

## REPO STATE (2026-09-26) — main, PR #99, PR #100

- `origin/main` = `49ba5a0` (merge of PR #98, china-sourcing v0.2), unchanged since 2026-09-19's
  round-2 branch archaeology.
- **PR #99** `fix/governance-carryover-v0.1`, head `7ca442b` (was `9d4244f`, then `724dbe4`):
  intended to carry over the safe part of the abandoned `feat/unified-system-governance-v0.1`
  branch's commit `2451722` -- `closing()` wrapping on sqlite connections across 6 modules,
  `system_capability_registry` wired into `activate()`, PRJ-FAL-01/FAL text in `AGENTS.md`.
  **FM-012:** the first version of this PR (`9d4244f`) contained *only a test file* -- the code
  it claimed (six modules' worth of `closing()` fixes) was never actually staged, because a
  `git stash pop` had put the changes in the working tree but not the index. An independent
  red-team review caught it by diffing `git show --stat` against the commit message
  (`docs/system/REDTEAM_PR99_PR100_2026-09-26.md`, finding P0-1). Fixed in `7ca442b`, which
  actually contains the carry-over code. **Still open (P2-4, same red-team review, not fixed by
  this session -- out of this session's scope):** `nexus_status_brief.py:51,62` still uses
  unwrapped `with sqlite3.connect(...)`, so "main no longer leaks connections" is not fully true
  yet even after `7ca442b`. **Also open (P2-5):** the PRJ-FAL-01 portfolio-priority row has no
  test asserting which project it displaces from `watch_portfolio`'s running set.
- **PR #100** `feat/steel-recovery-sync-v0.2`, head `0940544` (was `21c51b6`, `14407f4`, `b33d42b`):
  slab-line code corrections from the external + owner review rounds, CI switched to run the
  full `pytest evals` tree (previously 18 pytest-style files, 402 tests, never ran in CI --
  FM-011's companion finding), branch triage of the 71 remaining branches
  (`docs/system/BRANCH_TRIAGE_2026-09-24.md`), and (in `583216e`/`0940544`) a v5.1 fix to four
  wrong numbers in the vendor-facing procurement RFIs found by the 2026-09-26 transmission audit
  (`docs/system/TRANSMISSION_AUDIT_STEEL_2026-09-26.md`) plus the same red-team review's
  corrections (FM-012's writeup, ENG-10 in the control doc).
- **Neither PR is merged to `origin/main` yet.** This session's base, local branch
  `integ/2026-09-26` (`68f8d89`), is main + both PRs merged locally for testing -- both merge
  cleanly in either order and both produce the same tree (`REDTEAM_PR99_PR100_2026-09-26.md`,
  "Checked and clean"). Merging the real PRs on GitHub is Reza's action, not automated here.
- Full suite on the combined tree (from the red-team's fresh-worktree run, reproduced by this
  session below): `pytest evals` 1097 passed, `pytest tests` (PYTHONPATH=src) 501 passed,
  `unittest discover -s evals` picks up the TestCase subset, `nexus_checks docs/procurement
  --exclude '*_2026-09-22.md'` 0 errors.

## OPEN OWNER DECISIONS (full detail: `docs/expert_foundry/PROJECT_CONTROL_PRJ-STEEL-ROLLING-LINE-01.md` §3 -- not duplicated here, per this repo's own "point, don't copy" rule in `.nexus/steel/KERNEL.md`)

Blocking, needs Reza:
- **DEC-01** — design basis: engineer's spec (DC 1250 kW, 1:25, pinion centre 600, ~1-1.5 m/s,
  thick product) vs Package A (1600/2000 kW, ~1:7.1, centre 646, 3 m/s, 6-30 mm). Both kept as
  CLAIM/RDR side by side (FM-009: neither "incompatible" verdict held once the hidden assumption
  was named). Opens ENG-08, PRC-15.
- **PRC-01/02/13** — is the Ø600 stand existing-in-hand or broker-sourced; furnace target rate
  (20 t/h only, or also quote higher); approval to add Jinghuanre (南京净环热) as a furnace RFI
  recipient and whether to also RFI non-Chinese makers (NSKO Iran, CTS Turkey, Tenova).
- **ENG-09** — six unresolved questions back to the engineer (photo source, manual adjustment
  screw on a reversing mill, 600 vs 620, motor rpm 1250, target thickness, spindle type) --
  `docs/procurement/ENGINEER_SPEC_AND_STOCK_SEARCH_2026-09-23.md` §5.
- **ENG-10** — number-transmission audit (model → vendor documents), P1 items needing an
  engineering call: cycle-time basis mismatch (~95 s vs 212 s), gearbox nameplate power not
  derived from any model function, one RFI's 5.12 MN doesn't state its scenario basis, no drive
  torque limit requested against a motor that can deliver ~729 kN·m, and Package B still repeats
  a "cast iron rejected" verdict Package A already retracted.
- **OPS-04** — 129 untracked ruflo paths on the owner's laptop clone (not reproduced in this
  worktree, which is clean); `.claude/settings.json` there still enables ruflo plugins the
  owner turned off locally. Needs a decision to delete or `.gitignore`, and a commit only Reza
  can make (Claude cannot write `.claude/`).
- **OPS-05** — ~145 files that only differ by line-ending/permission mount noise; candidate fix
  `core.filemode=false`.
- **OPS-08** — merge PR #99 once Reza reviews the FM-012 fix, plus a separate governance call
  (lock "PILOT/ADOPTED agents only"; PRJ-FAL-01 portfolio row priority, see P2-5 above).
- **OPS-11** — 71 remaining branches: 9 merge candidates, 14 partially extractable, 40 archive,
  8 need Reza's call (`docs/system/BRANCH_TRIAGE_2026-09-24.md`).
- **PARK-01** — PRJ-CAN-01 package review (zip + docx, v1.9/v2.1 version mismatch), parked
  pending explicit go-ahead.

## SCHEDULED WORK
Weekly stock search (manual/PRC-14 style sourcing sweep): cloud run Saturdays 08:00 Tehran time,
laptop run Saturdays 09:00 Tehran time. (Owner-stated 2026-09-26; not yet backed by a committed
schedule file or script in this repo -- if a scheduler config is added for this later, record its
path here so this line doesn't go stale on its own.)

## EXPERT FOUNDRY / ROLLING MILL / STEEL PROJECT
Full detail lives in the steel project's own files, which this file points at rather than copies
(kept in sync via `.nexus/state/STATE_GOVERNANCE.json`'s freshness check):
- `.nexus/steel/KERNEL.md`, `.nexus/steel/CHECKPOINT.md` — kernel design + latest engineering
  checkpoint (active basis: slab 400x125x3000mm, 20 t/h furnace, Ø600 two-high stand, 3 m/s cap,
  DC drive; billet-line data superseded 2026-09-21, kept for history, do not use).
- `docs/expert_foundry/PROJECT_CONTROL_PRJ-STEEL-ROLLING-LINE-01.md` — the living control doc
  (status table, gates G0-G5, full backlog, risk register, decision log). Read this, not this
  section, for anything steel-specific.
- `.nexus/expert_foundry/registers/ENGINEERING_FAILURE_MEMORY.md` (FM-001..FM-012),
  `PRIOR_ART_AND_BENCHMARK_REGISTER.md`, `TECHNOLOGY_RADAR_AND_MARKET_EVIDENCE.md`.
- Gates as of 2026-09-26 (unchanged from CHECKPOINT.md): `concept_calculation_allowed=True`,
  `fabrication_release_allowed=False` (11 blockers), old `calculation_allowed` gate untouched
  at `False`.

## OTHER PROJECTS (unchanged, not touched this session)
- PRJ-HYD-01 (Hydrotester): consolidated onto main 2026-09-19 (commit `1e6d5d5`) from the best of
  10 independent branch attempts. See the 2026-09-19 history further down this file's git log if
  full detail is needed; nothing has changed here since.
- PRJ-KCL-01, PRJ-CAN-01: PRJ-CAN-01 is PARK-01 above; PRJ-KCL-01 not yet started.
- Opportunity Suggestion Engine (`opportunity_suggestion_engine.py`): built, draft-only queue,
  compliance gate blocks any next step until a named human clears sanctions/export-control
  review. No real signal has ever been submitted to it (no `opportunity_drafts.db` exists
  outside test tmp paths).

## ROLE SPLIT (unchanged)
- Claude Code: engineering executor (code/tests/branches).
- ChatGPT/NEXUS: orchestrator, business context, live connectors, authority recovery.
- Claude Chat: independent reviewer -- verifies claims against raw evidence, never assumes access
  it doesn't have.
- Reza: final approval on all protected actions, tie-breaker on cross-AI disagreement, sole
  human-in-the-loop for compliance-sensitive decisions.

## THIS SESSION (2026-09-26): state-freshness check + bringing this file current
- Built `nexus_checks/state_freshness.py` (stdlib-only): a governed state/kernel file is flagged
  STALE when a path it governs (per `.nexus/state/STATE_GOVERNANCE.json`) has git commits newer
  than the state file's own last commit by more than the configured tolerance (2 days default).
  Also scans the same state/kernel files for `` `backtick path` `` references that don't exist
  in the tree. Wired into the CLI as `python -m nexus_checks --state --repo .`. Tests:
  `evals/test_nexus_checks_state.py` (fresh passes, stale fails, missing-governed-path warns,
  broken reference fails, non-path backtick spans like a Windows machine path or a shell command
  are correctly not flagged).
- Before this rewrite, the check found (and this update fixes): this file was ~7 days stale
  against `docs/procurement/`, `docs/expert_foundry/`, `docs/system/`, `.nexus/steel/`, `AGENTS.md`
  and `nexus_checks/`; `.nexus/steel/CHECKPOINT.md` was ~4 days stale against the same procurement
  and expert-foundry work; `.nexus/steel/GAP_ANALYSIS.md` pointed at `registers/*.md` instead of
  `.nexus/expert_foundry/registers/*.md` (missing path prefix, fixed); this file's own branch-
  archaeology section named src/nexus_control_plane/forge.py as if it were a real tracked path
  (it only ever existed on an unmerged branch, reworded above to say so); and the control doc's
  OPS-04 row named .claude/helpers/auto-commit.sh as a tracked path when it was in fact an
  untracked, never-committed local file (reworded in that doc, see its own change note).
- Next: run `python -m nexus_checks --state --repo .` after any future edit to
  `docs/procurement/`, `docs/expert_foundry/`, `.nexus/steel/` or `docs/system/`, and update this
  file (or `.nexus/steel/CHECKPOINT.md` for steel-only changes) in the same sitting, not later.
