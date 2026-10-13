# NEXUS × Claude — Constitution v4.0 implementation audit (read-only)

- **Date:** 2026-09-30.
- **Scope:** a read-only comparison of the constitution with the real environment. Nothing was installed, deployed, merged, sent or purchased during this audit.
- **Evidence class:** each statement below is labelled FACT (checked in this session with a command or a tool call), ASSUMPTION or UNKNOWN.

## 0. Headline findings

1. **Authority contradiction (FACT).**
   - The activation text says the active reference is *Source Registry v1.8 + Master Context v2.1*.
   - The repo's authority record `docs/authority/AUTHORITY_STATUS.md` (2026-09-17) promotes **Master Context v1.4 + Source Registry v1.1**. It lists v1.8 and v2.1 as **RECONCILIATION_PENDING** and states that v2.1 is internally self-contradictory.
   - Per the constitution's own §II ("filename recency alone does not establish authority"), this stays **OPEN**, and v1.4 + v1.1 remain the working tuple until Reza promotes a newer one explicitly.
2. **Most of the constitution's mechanisms already exist as code, but they are not wired into the real workflow (FACT).**
   - On `main` today: `nexus_core.project_memory`, `nexus_chat_bootstrap`, `conversation_control`, `src/nexus_brain/resource_router.py`, `owner_decision_runtime`, `continuous_research`, `self_improvement_runtime` and `src/nexus_core/adoption_gate.py`.
   - Their maturity is IMPLEMENTED + TESTED (CI green).
   - Claude sessions have not been calling them. Their maturity *as operating practice* is DESIGNED, not ACTIVE.
   - **The gap is adoption, not construction.** Building more infrastructure would be theatre (§XLII, §XLIII).
3. **The biggest real threat to memory is the merge backlog, not a missing mechanism (FACT).**
   - `main` is still `49ba5a0` (2026-09-24).
   - Three PRs are open: #99, #100 and #101.
   - Four more branches exist:
     - `feat/project-memory-and-checks-v0.1` (pushed, no PR);
     - `feat/steel-experiments-v0.1` (pushed, no PR);
     - `feat/steel-reroll-01` (local and laptop only);
     - `feat/reroll-01-v0.1` (local and laptop only).
   - A fresh session boots from `main`, so it sees state that is six days old.
   - That is exactly how FM-013 happened: a finished study was redone because it lived only on an unpushed branch.

## 1. Current architecture

| Layer | What exists | Evidence |
|---|---|---|
| Governing text | `AGENTS.md` (1,801 words) + `CLAUDE.md` kernel (965 words), loaded every session | FACT |
| Authority | `docs/authority/AUTHORITY_STATUS.md` (tuple v1.4 + v1.1) | FACT |
| Durable state | `.nexus/state/CURRENT_STATE.md`, per-project control docs, `.nexus/steel/{KERNEL,CHECKPOINT}.md`, `.nexus/memory/*.jsonl` (project_memory store), failure register FM-001…FM-013 | FACT |
| Executable checks | `nexus_checks`: hygiene, EN/ZH parity, superseded values, git health, **transmission** (15 RFI numbers recomputed from the model) and **state freshness** (the last two are on unmerged branches); CI runs unittest + `pytest evals` + `pytest tests` | FACT |
| Engineering models | `slab_line_design.py`, `slab_line_experiments.py`, `reroll_study.py`, `reroll_economics.py`, with tests | FACT |
| Background execution | claude.ai scheduled tasks. These are the only real background executor (§XLIV): weekly stock radar (cloud, Sonnet), weekly laptop-browser radar (device-bound), weekly health check (Sonnet), Ops Deck refresh every 6 h (Sonnet) | FACT |
| Workers | Agent tool with per-call model choice (haiku / sonnet / default); Workflow tool (multi-agent, explicit opt-in only) | FACT |
| Cross-session memory | repo files (authoritative); claude.ai project memory (continuity only); synced skills | FACT |

## 2. Capability inventory

Legend: AV = available, CO = connected, AU = authenticated, RV = read-verified in this session, WE = write-enabled, TE = tested, PA = production-approved.

| Capability | Status | Note |
|---|---|---|
| Git repo (cloud clone) | AV, RV, WE (local) | Push is **not** possible from cloud or laptop (no credentials, by design). Push, merge and PRs are owner actions |
| Device bridge (laptop shell, file stage/commit) | AV, CO, RV, WE | Connection drops intermittently; recovery is automatic |
| Built-in browser (laptop) | AV, CO, RV | Reads GitHub API, Baidu, 51chuli and others. Not signed in to GitHub. JD, Taobao and Machinio blocked |
| Scheduled tasks (create/update/list) | AV, CO, RV, WE, TE | Hourly minimum. A device-bound task is suspended when the laptop is off, and its model cannot be changed from the cloud |
| Subagents (model routing inside Anthropic models) | AV, TE | Measured costs in `CLAUDE.md` §4 |
| Cross-provider routing (Codex/OpenAI) | **not available** | Needs `codex-plugin-cc` plus Reza's OpenAI account (owner action) |
| WebSearch / WebFetch | AV, TE | US-only search; some sites decline; WebFetch returns summaries, so key numbers must be re-read |
| GitHub REST API from the cloud | **blocked (403)** | `git clone` and `git ls-remote` work; the API works through the laptop browser |
| claude.ai memory (project-scoped) | AV, RV, WE | Continuity only, never authority |
| claude.ai Projects docs | AV | Unused so far |
| MCP connectors: Gmail, Drive, Calendar, HubSpot, Notion, Railway, Canva, Figma, Adobe, Exa, Claude Docs | AV, CO (they reconnect repeatedly during sessions) | Not read-verified this week except through the Ops Deck task. **Adobe (107 tools), Railway (65), Notion (45), Canva (40), Figma (40) and HubSpot (27) have had no use in NEXUS work this month** |
| Ruflo plugins | installed in the container's plugin cache (project path `/home/claude/nexus-ruflo`) | Inactive for this repo, but the container's global `~/.claude/CLAUDE.md` still injects a stale "use ruflo MCP tools" instruction into every session |

## 3. Gap analysis against v4.0

| Constitution area | State | Gap |
|---|---|---|
| II Authority first | record exists; the v1.8/v2.1 claim contradicts it | the contradiction must be resolved by Reza, not by recency |
| III Isolation | enforced in docs; REROLL kept separate | none material |
| IV/V Truth and maturity | in `CLAUDE.md` §3 | none |
| VI/VII Loop and do-the-work | practised | **over-applied on 09-28/29:** the owner had to cut scope. v4 §XII (token governor) and explicit owner scope must win over §VII |
| X Context independence | state files + project_memory exist | **merge backlog** (see §0.3), and no "resume pointer" test |
| XI Model router | used through the Agent `model` option; `resource_router.py` exists but is not called | no cross-provider option |
| XII Token governor | measured in `CLAUDE.md` §4 | `conversation_control.allocate_tokens` is not used; unused MCP servers; stale ruflo instruction |
| XIII–XV ExpertForge, deep search | done ad hoc (literature validation, market research) | no reusable domain-map template |
| XVII Independent calculation | red-team reviews and transmission check (FACT: they caught P0s) | the REROLL cross-check had **limited independence**: same S235 basis, similar μ and flow-stress family |
| XVIII/XIX Shadow scientist, Red team | practised per release | not formalised as a checklist |
| XXI/XXII Experience and failure library | FM-001…FM-013, 5 of them executable | no CASE_ID schema for successes |
| XXIII Expert exam | none | new |
| XXIV–XXVI Adaptive Arena | 1–4 agents used; no voting | fits; **do not** adopt 16–32 by default (see §8) |
| XXIX Tool router states | this table is the first inventory | not kept current automatically |
| XLIV Anti-fake-autonomy | respected | none |

## 4. Keep

- `nexus_checks`: hygiene, parity, superseded values, git health, transmission, state freshness.
- CI running `pytest evals`.
- The independent-reviewer-before-release rule.
- Sonnet for specified builds.
- The weekly health task.
- FM register and its executable checks.
- The per-project control docs.
- Explicit approval gates for any external action.
- The existing core modules listed in §0.2.

## 5. Modify

1. **`CLAUDE.md` §2 boot.** Add the FM-013 duplicate-work check: before starting any project, run `git worktree list`, `git branch -a --list '*<kw>*'` and `git log --all --oneline --grep '<ID>'`. **Done in this commit.**
2. **`CLAUDE.md`: owner scope wins.** An explicit owner scope limit ("Phase 1 only", "no new agents") overrides any autonomy default. This matches v4 §XII and §XLVIII. **Done in this commit.**
3. **Adopt v4 as a reference, not as a boot file.** Store the full constitution in `docs/authority/` as DRAFT. Import only a ~15-line delta into `CLAUDE.md`. Pasting it whole would add ~6k tokens to every session. **Not done yet:** this waits for Reza's adoption decision (§0.1).
4. **Label cross-checks honestly.** Call a cross-check "independent" only when inputs, sub-models and methods differ. Otherwise use "computational cross-check, limited independence". This came from the REROLL review.

## 6. Remove or retire (owner actions)

- The ruflo block in the container's global `~/.claude/CLAUDE.md`, plus the ruflo plugin cache (`/root/.claude/plugins`). **Reza's action** (it is his config), or with explicit approval.
- Unused MCP connectors in claude.ai settings: Adobe, Canva, Figma, HubSpot and Railway. Railway only if the Ops Deck task is retired; Notion only if no longer used. **Reza's action.**
- The **Ops Deck refresh task** (every 6 h, about 28 Sonnet runs a week). It should be kept only if Reza still reads the deck. **Reza's decision.**
- After the merges: remote branches superseded by merged PRs, and the 40 ARCHIVE branches from `BRANCH_TRIAGE`. Each needs Reza's yes.

## 7. Missing mechanisms worth building (smallest first)

1. **VP-01 cold-start resume probe** (see §15). It is a prompt plus an answer key; no new code.
2. **A boot script `python -m nexus_checks --boot`.** It would run `--state`, the FM-013 duplicate check for a given project ID, and `project_memory.bootstrap_context()` in one command. It is about 60 lines, and it should be built only after VP-01 shows the manual boot fails.
3. **An expert-exam seed** for rolling-mill mechanics: 10 textbook or published cases, with answer keys and tolerances. The literature-validation doc already lists 10 candidate tests.
4. **Not needed now:** GraphRAG, durable execution engines, a persistent agent swarm, cross-provider routing. Nothing measured asks for them yet (§XXX).

## 8. Token and compute waste (measured or observed)

| Item | Evidence | Fix |
|---|---|---|
| Duplicate REROLL run (FM-013) | about 780k subagent tokens spent on 09-29 redoing 09-28 work | the boot duplicate check |
| Over-scoped fan-outs | the owner stopped a 4-agent reconcile on 09-29 | owner scope wins; ask for explicit scale |
| Stale ruflo instruction in every session | observed in this session's system context | remove it |
| Unused MCP servers | about 320 deferred tool names announced repeatedly | disconnect the unused ones |
| Ops Deck every 6 h | trigger list | confirm or retire |
| Constitution pasted in full | ~4.5k words | reference plus a delta only |
| Where value came from | red-team review 177k → 2 blocking defects; transmission audit 367k → 4 wrong vendor numbers; single reviewers beat fan-outs | keep |

## 9. ExpertForge plan (rolling mill only; the smallest step)

- Turn `MODEL_LITERATURE_VALIDATION_2026-09-26.md` into a **domain map**: disciplines, sources, constants and open gaps. It exists; it needs to be indexed.
- Next knowledge gaps with decision value:
  - flow-stress anchors (UNSOURCED, ±15% on force);
  - Ar3 for the real heat chemistry;
  - DC commutation envelope;
  - neck allowable stress.
- Each is closed by one targeted source or measurement, not a sweep.

## 10. Adaptive Arena plan

- The default is **one worker and one independent reviewer**.
- Escalate to 3–4 only when the reviewer and the author disagree on a consequential number, or when a decision is irreversible.
- More than 4 needs Reza's explicit request (per the Workflow tool rule).
- Disagreement is settled by calculation or test, never by vote (§XXVI).

## 11. Checkpoint and resume plan

1. **Precondition (owner):** merge the stack, so `main` holds current state (§16 step 1).
2. Every cycle ends with `CURRENT_STATE.md`, the project control doc and a `project_memory` record, and `--state` passes (already in `CLAUDE.md` §8).
3. **Nothing important lives only in the container.** Local-only branches are bundled to the laptop in the same cycle; this is already practised.
4. VP-01 proves or disproves the plan.

## 12. Experience and failure library plan

- Keep the FM register as the failure library.
- Add a **CASE** section for successes, with the schema of §XXI: problem → hypothesis → evidence → hidden constraint → lesson → test.
- Seed it with 3 real cases:
  - the transmission audit (roll-referred torques);
  - FM-012 (a stash lost the index);
  - REROLL (the photo showed only group A).
- Rule: a lesson becomes a test or a check when it can recur (FM-005…FM-012 already follow this).

## 13. Capability escalation plan

The order is: existing tool → script → official API/MCP → owner-authorised account → new internal tool.

Current open escalations, each needing an **owner action**:
- GitHub write: a PAT, or merges through the UI (current practice, and it works).
- Codex cross-review: plugin plus OpenAI account.
- Apify: paid account, for blocked Chinese marketplaces.
- JD/Taobao: Reza logs in once in the laptop browser.

## 14. Security and credential architecture

- **FACT:** no credentials are stored in the repo or in prompts. Push and merge stay with Reza. The laptop has no git credential helper.
- **Plan:** read-only by default. Any future token is scoped per task (read vs write), stored only in the provider's secret store, and never pasted into chat or into the repo. Payments and signatures stay RED.

## 15. Smallest end-to-end vertical acceptance test: VP-01 "cold-start resume"

- **Spec and answer key:** `docs/system/VP-01_COLD_START_RESUME.md`.
- **Method:** a fresh scheduled cloud session on Sonnet, with no chat history, clones `main`, runs the boot procedure, and answers 8 questions from state files only.
- **Pass criteria:**
  - at least 7 of 8 answers correct;
  - zero attempts to redo finished work;
  - under 150k tokens.
- **What it tests:** constitution priorities 1 (persistent state and resume) and 2 (authority recovery), with no new infrastructure.

## 16. Implementation sequence

1. **Reza:**
   - merge #99 → #100 → #101;
   - push `feat/nexus-v4-audit`, which contains the memory, experiments, REROLL run-1 and audit commits;
   - open one PR and merge it after CI.
2. **Claude:** create the VP-01 one-shot scheduled task and read its result.
3. **If VP-01 fails**, build `nexus_checks --boot` (§7.2) and rerun. **If it passes**, stop building. Seed the CASE library and the expert-exam cases only when the next engineering task needs them.
4. **Reza:** retire ruflo, the unused connectors and (maybe) Ops Deck (§6), and decide on the authority tuple (§0.1).

## 17. Rollback

Every change here is a doc edit or a `CLAUDE.md` edit on a branch.
- **Before merge:** delete the branch.
- **After merge:** `git revert <sha>`.
- **The VP-01 scheduled task:** delete it with its trigger ID.

No production system, credential or external party is touched.

## 18. Estimated impact

| Step | Tokens / compute |
|---|---|
| This audit | about 60k in the main session, no subagents |
| VP-01 run | expected ≤150k (Sonnet), once |
| `--boot` script, only if needed | about 80k to build and test |
| Savings | avoiding one duplicate run (FM-013) saves about 780k; removing unused MCP names and the ruflo instruction trims every session's context; retiring Ops Deck (if unused) removes about 28 runs a week |

**Open items not done here:** PHASE1_5_DECISION_CLOSURE for PRJ-STEEL-REROLL-01, requested on 2026-09-29, was **not delivered**, because the owner's next message changed the task. It stays pending.
