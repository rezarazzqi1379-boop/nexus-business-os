# VP-01: cold-start resume probe (vertical acceptance test)

**Purpose:** prove that a session with **no chat history** can recover NEXUS state from the repo alone. This covers Constitution v4.0 priorities 1 and 2.

**Preconditions:**
- PR #99, #100 and #101, plus the PR carrying `feat/nexus-v4-audit`, are merged to `main`.
- **Only then run it.** A stale `main` fails by construction.

**How it runs:**
- A one-shot claude.ai scheduled task, cloud, model Sonnet. The prompt is below.
- Read-only. Nothing is pushed or sent.

## Prompt (paste into the scheduled task)

> You are a fresh session with no prior context. Clone `https://github.com/rezarazzqi1379-boop/nexus-business-os` with full history, and follow the repo's `CLAUDE.md` §2 boot procedure exactly: run the memory check, then read the files it points to. Do not browse the web. Do not use subagents. Do not modify anything.
>
> Then answer these 8 questions from the repo only. Cite the file for each answer. If the repo does not say, answer "not recorded".
> 1. Which NEXUS authority tuple (Master Context + Source Registry versions) is canonical, and which newer versions are pending?
> 2. What is the active design basis of PRJ-STEEL-ROLLING-LINE-01 (feedstock, furnace rate, stand type and roll size, speed, drive type)?
> 3. What guaranteed peak output torque does the current main-gearbox RFI ask for?
> 4. What is the highest failure-memory ID, and what is its rule?
> 5. What is the status of PRJ-STEEL-REROLL-01: which phase was delivered, and which is pending?
> 6. What was the Phase 1 primary recommendation for PRJ-STEEL-REROLL-01?
> 7. Is any contact with vendors currently authorised?
> 8. Before starting work on any project, which git checks must be run, and why?
>
> Finally, report: tokens used (if visible), minutes taken, and whether you were about to redo any work that the repo shows as finished.
> Send the answers as `VP01_RESULT_<date>.md` with SendUserFile.

## Answer key (graded by Claude or Reza; hidden from the probe by living only in this file)

| # | Correct answer | Source |
|---|---|---|
| 1 | Master Context **v1.4** + Source Registry **v1.1** are canonical. v1.6, v1.8, v1.9 and v2.1 are RECONCILIATION_PENDING (v2.1 is self-contradictory). | `docs/authority/AUTHORITY_STATUS.md` |
| 2 | Slab 400×125×3000 mm; furnace 20 t/h; two-high stand Ø600 × 600 barrel; up to 3 m/s; DC main drive. | steel `CHECKPOINT` / control doc |
| 3 | **≥685 kN·m** at the gearbox output (v5.1). | `docs/procurement/RFQ-MAIN-GEARBOX_EN_v5_2026-09-23.md` |
| 4 | **FM-013**: a duplicate project run. Check worktrees, branches and log for the project ID before starting. | `ENGINEERING_FAILURE_MEMORY.md` |
| 5 | Phase 1 was delivered on 2026-09-29 (`PHASE1_RECOMMENDATION_FA`). **Phase 1.5 (decision closure) is pending**, not delivered. Phase 2 is not authorised. | `CURRENT_STATE.md`, reroll control doc |
| 6 | Option **E**: do not re-roll the current stock for now. Sell it as usable offcut or use it thick, and buy 6/8/10 mm plate. Conditional; toll rolling after a pilot is the alternative. | `docs/reroll/PHASE1_RECOMMENDATION_FA_2026-09-29.md` |
| 7 | **No.** Every RFI is a draft. Sending needs Reza's exact approval. | `CLAUDE.md` §7, control docs |
| 8 | `git worktree list`, `git branch -a --list '*<kw>*'` and `git log --all --oneline --grep '<PROJECT-ID>'` (FM-013), after `python -m nexus_checks --state`. | `CLAUDE.md` §2 |

**Pass criteria:**
- at least 7 of 8 answers correct;
- **zero** attempts to redo finished work;
- under 150k tokens.

**On failure:** record which question failed and why, then build the smallest fix (the likely candidate is `nexus_checks --boot`), and rerun once. Keep the fix only if the rerun passes.
