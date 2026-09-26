# OPS-08 — Review of commit 2451722 (feat/unified-system-governance-v0.1)

**Commit:** `2451722` "feat(governance): sandbox-only agent lifecycles, FAL reconciliation, capability registry" (author date 2026-09-19)
**Parent:** `bb2acae` (ancestor of `origin/main`, confirmed: `git merge-base --is-ancestor bb2acae origin/main` → true)
**Not on main:** `git merge-base --is-ancestor 2451722 origin/main` → false
**Main at review time:** `origin/main` = `49ba5a0`, 89+ commits ahead of `bb2acae`
**Branch's other 4 commits** (5233d29, 0bc720d, 0dc17b5, 8af87eb): out of scope per task brief — already covered by main (questionnaires byte-identical; intake JSON reconciled in `941c5ee`).

All commands below were run in this repo; a scratch worktree was used for the apply/test experiment and removed at the end (`git worktree remove --force /home/claude/scratch_ops08`).

---

## 1. Per-file verdicts

Legend: **(a)** already on main equivalently · **(b)** absent, still applicable · **(c)** conflicts with how main evolved · **(d)** obsolete/superseded.

| # | File | Verdict | Notes |
|---|------|---------|-------|
| 1 | `.agents/skills/nexus-project-operator/SKILL.md` | (b) | Adds `coordination_kit`/`task_handoff` + FAL/Tavily guidance paragraph. No overlap on main. Applies cleanly as raw diff. |
| 2 | `.gitignore` | (b) | Adds `data/nexus_system/capability_status.json`. Trivial, no conflict. |
| 3 | `AGENTS.md` | (b) | Adds Tavily `EXPERIMENT_ONLY` bullets + new "Cross-agent handoff and FAL reconciliation" section. Confirmed **absent** from main's current `AGENTS.md` by direct read. Applies cleanly raw. |
| 4 | `README.md` | (d) | Documents a "Version 1.10" Ruflo/claude-flow rollout (26–28 plugins, daemon not started, federation relay). Main's actual Ruflo footprint is materially different and further along (`.claude/settings.json`, `.mcp.json`, `package.json`, helper scripts) **and per `CLAUDE.md` was subsequently *disabled* by the owner on 2026-09-22** — after this commit, before the review date. This section is stale narrative overtaken by later real events on main; not worth carrying. Mechanically it applies cleanly once CRLF is stripped (see §3), so this is a content judgment, not a technical blocker. |
| 5 | `api.py` | (b) | Wraps two `sqlite3.connect()` startup-probe calls in `contextlib.closing()`. Main still lacks `closing` in this file (`grep closing api.py` → none). Zero behavioral risk (diagnostics only). |
| 6 | `audit.py` | (b) | Same `closing()` pattern for the audit-log connection (`__init__`/`append`/`verify`). Main still lacks it. Audit-log *logic* (hash chaining) is untouched — only connection lifecycle changes. |
| 7 | `autonomy.py` | (b), needs manual reconciliation | Same `closing()` pattern across `enqueue/claim_next/complete/fail/monthly_spend/record_usage/record_capability_failure`. **Main changed this file independently** since `bb2acae` (+38/−7): it dropped the unused `approval_inbox` table (with an explicit comment that approval authority lives only in `ApprovalStore`) and added a new `defer()` method — which still uses the old *unwrapped* `db = self._connect() … finally: db.close()` pattern. `git apply --3way` merges cleanly (non-overlapping regions), but a faithful port should also wrap the new `defer()` the same way, or main will have re-introduced the exact leak this commit fixes elsewhere. |
| 8 | `canonical_sources.py` | (b) | Same `closing()` pattern for `CanonicalStore.__init__/ingest/_all_rows`. Main independently added hydrostatic-hold-point contradiction rules (+32/−7) in a distant, non-overlapping part of the file (near EOF). 3-way merge clean. |
| 9 | `continuous_research.py` | (b) | Adds one new `ResearchTopic` ("search-provider-benchmark-radar"). Purely additive/declarative — per AGENTS.md, research topics can only ever produce `EXPERIMENT_ONLY` proposals, never execute anything directly. No conflict. |
| 10 | `evals/test_core.py` | (b) | Adds `test_event_store_releases_sqlite_file` and `test_autonomy_store_releases_sqlite_file`, asserting the DB file can be deleted after use (i.e. the connection was actually closed). Regression coverage for items 5–8/14/17. |
| 11 | `evals/test_mvp.py` | (b) | Mechanical `closing()` wrap inside one existing audit test helper. Trivial. |
| 12 | `execution_scheduler.py` | (b) | Adds `"sandbox"` to `_LANES`. Byte-identical to `bb2acae` on main otherwise. Required by #15; without it, the new lifecycle tests in `test_project_control_plane.py` fail with `ValueError: invalid_execution_lane` (reproduced, see §3). |
| 13 | `nexus_system_bootstrap.py` | (b) | Wires `system_capability_registry.activation_payload()` into `activate()`: writes `data/nexus_system/capability_status.json` and registers it as a `UnifiedDataHub` asset. **Confirmed main added `system_capability_registry.py` itself in `0f1cf63`, but never wired it into the bootstrap/activation flow** — on main today the module is unused dead code from the activation path's point of view. This hunk is what actually turns it on. |
| 14 | `ops.py` | (b) | `closing()` around the backup/restore `sqlite3.connect()` pairs. Straightforward resource-hygiene fix, no logic change (integrity-check behavior identical). |
| 15 | `project_control_plane.py` | (b), **safety-relevant, needs owner review** | Adds lifecycle-gated agent eligibility: only `PILOT`/`ADOPTED_ADAPTER` agents are eligible for normal work; `SANDBOX_READY`/`EXPERIMENT` agents are eligible **only** when `lane == "sandbox"` and `risk != "external"`. Confirmed main's `_select_agent` today has **no such filter at all** — any cataloged agent, any lifecycle, can be assigned to any lane/risk. This is a real, currently-missing safety gate. **But**: main's actual `seed_catalog()` (`src/nexus_core/agent_catalog.py`) today contains **zero** agents with lifecycle `PILOT` or `ADOPTED_ADAPTER` — every entry is `DISCOVERED`/`WATCH`/`EXPERIMENT`/`SANDBOX_READY`/`DEFERRED`. Applying this hunk verbatim means `build_coordination_plan`/`build_portfolio_cycle` would never schedule *any* non-sandbox work as "running" against the real catalog — everything falls to `blocked("no_qualified_agent")` or `waiting`. The commit's own test diff quietly accepts this (`test_portfolio_cycle_turns_conversation_need_into_scheduled_idea` assertion changes from `assert cycle.coordination.schedule.running` (truthy) to `== ()` + `assert cycle.coordination.schedule.waiting`) rather than flagging it. Mitigating factor: `grep` found **no production callers** of `build_coordination_plan`/`build_portfolio_cycle` anywhere outside tests today, so this module is not yet load-bearing in a live path — but whoever wires it up next needs to know the catalog has to be populated with `PILOT`/`ADOPTED_ADAPTER` agents first, or all work silently halts (fails closed, which is safe, but is a large behavior change, not a drive-by fix). |
| 16 | `projects.py` | (b) | Adds `PRJ-FAL-01` project-policy entry (research lane, priority 55, `canonical_promotion`/`cross_lane_evidence_transfer`/`live_provider_activation` explicitly blocked). Purely additive registry row, no conflict. |
| 17 | `state.py` | (b) | Same `closing()` pattern for `EventStore`. |
| 18 | `tests/test_nexus_system_bootstrap.py` | (b) | Asserts the new `capabilities`/`live_network_capabilities` keys and `capability_status.json` file from #13. |
| 19 | `tests/test_project_control_plane.py` | (b) | Adds an `AgentCatalogEntry` test factory + 3 new lifecycle-gating tests, and updates the 4 pre-existing tests to pass an explicit `ADOPTED_ADAPTER` test catalog (this is what masks the seed-catalog gap noted in #15 — the updated tests never exercise the real default catalog for non-sandbox work). |
| 20 | `tests/test_system_capability_registry.py` (new) | (b) | New file. Main added the underlying `system_capability_registry.py` module in `0f1cf63` but never got this test. Runs unmodified against main's current module — **3/3 pass**, no code changes needed. |

---

## 2. What the commit does (plain English)

- **`autonomy.py` / `state.py` / `canonical_sources.py` / `ops.py` / `audit.py` / `api.py`**: pure resource-lifecycle hardening. Every ad-hoc `sqlite3.connect(...)` (or `self._connect()`) is wrapped in `contextlib.closing(...)`, on top of the existing `with db:` transaction context manager. In Python, `with sqlite3.Connection() as db:` only commits/rolls back a transaction — it does **not** close the connection/file handle. Every one of these six files currently leaks a connection per call on main; only `approvals.py` (fixed in an earlier, already-merged commit) has this fix today. No query logic, hashing, or audit-chain behavior changes — this is exclusively about deterministic connection release.
- **`project_control_plane.py`**: introduces a hard split between agents that are trusted for real execution (`PILOT`, `ADOPTED_ADAPTER`) and agents still in an experimental/sandbox lifecycle (`SANDBOX_READY`, `EXPERIMENT`). Experimental agents can now only be selected when the work explicitly targets the new `"sandbox"` lane, and never for `risk="external"` work, even in that lane. Everything else (`DISCOVERED`, `WATCH`, `DEFERRED`, etc.) remains permanently ineligible, as before.
- **`ops.py`**: no logic changes beyond the connection-closing fix described above; backup/restore integrity-check behavior is identical.
- **`audit.py`**: same — the hash-chain append/verify logic is untouched; only the connection handling changes.
- **AGENTS.md "Cross-agent handoff and FAL reconciliation" section**: codifies that (1) `decided_by` in the approval store is *caller-claimed* audit metadata, not authenticated identity, and must never be described as proof of human presence; (2) cross-agent handoff packages (from `coordination_kit`/`task_handoff`) must have every field — branch, head, diff, test binding, ownership, approval scope — independently re-verified rather than trusted as prose; (3) for project `PRJ-FAL-01` (reconciling two disputed structural/commercial models, "FAL-A" vs "FAL-B"), both operational (`END_USER`/`PRODUCER`) and economic (`IMPORTER`/`EXPORTER`) role dimensions must be preserved rather than one overwriting the other, and disputed dynamic commercial facts stay `UNKNOWN`/`SOURCE_VERSION_DISPUTED` until their respective gates clear (no live provider activation, no cross-lane evidence transfer, no canonical promotion in the meantime).
- **`continuous_research` topic**: adds one new recurring research topic, "search-provider-benchmark-radar" (credential redaction/timeouts/bounded egress, citation-quality/hallucination benchmarks, rate-limiting/circuit-breaking/provider isolation), feeding the stated rationale for keeping the Tavily search adapter `EXPERIMENT_ONLY` until it clears its own Phase G benchmark gate. Per AGENTS.md's existing governance, this can only ever generate an `EXPERIMENT_ONLY` proposal — it does not execute or promote anything by itself.
- **`system_capability_registry` wiring** (`nexus_system_bootstrap.py`): the registry module itself (which capabilities are `local_use_enabled` vs `live_network_enabled` vs `production_approved`, with a hard invariant that a live-network capability can never self-mark itself production-approved) already exists on main (added in `0f1cf63`) but main never calls it during activation. This commit is what actually invokes it and publishes `data/nexus_system/capability_status.json` as a tracked, hub-registered read-model asset.

---

## 3. Experiment: applying the patch to a scratch worktree at `origin/main`

```
git worktree add /home/claude/scratch_ops08 origin/main
git diff --ignore-cr-at-eol 2451722^ 2451722 > p.diff   # 934 lines, 20 files
git apply --3way p.diff       # first attempt
```

**Result of the raw (`--ignore-cr-at-eol`-generated but not CR-stripped) patch:** `git apply` is all-or-nothing per invocation, and 11 of 20 files failed with `patch does not apply` (`README.md`, `api.py`, `audit.py`, `autonomy.py`, `canonical_sources.py`, `evals/test_core.py`, `evals/test_mvp.py`, `execution_scheduler.py`, `ops.py`, `projects.py`, `state.py`), so nothing was actually written to the tree on that combined attempt.

**Root cause, confirmed directly:**
```
$ git show 2451722^:execution_scheduler.py | file -
/dev/stdin: ASCII text executable          # pure LF
$ git show 2451722:execution_scheduler.py | file -
/dev/stdin: ASCII text executable, with CRLF, LF line terminators   # whole file flipped to CRLF except the one truly-edited line
```
`--ignore-cr-at-eol` only changes which lines `git diff` treats as "truly different" when computing the hunks; it does not strip the literal `\r` bytes it then quotes in the emitted patch text. Since current `main` files are pure LF, `git apply`'s exact-byte context matching fails on every file the commit's author happened to save with CRLF, even where the *only* real change is one line.

**Verification that this is purely mechanical, not semantic**, per file:
```
$ git diff --stat bb2acae origin/main -- README.md api.py audit.py evals/test_core.py \
    evals/test_mvp.py execution_scheduler.py ops.py projects.py state.py
(no output — all 9 files are byte-identical between the commit's parent and current main)
```
Only `autonomy.py` (+38/−7) and `canonical_sources.py` (+32/−7) diverged on main independently since `bb2acae`, and in both cases the diverging main hunks are in non-overlapping regions from the commit's hunks (confirmed by inspection, §1 rows 7–8).

**Re-run with `\r` stripped from the diff text** (`tr -d '\r' < p.diff > p_full.diff`, i.e. a proper CRLF-normalized patch):
```
$ git apply --3way p_full.diff
Applied patch to '.agents/skills/nexus-project-operator/SKILL.md' cleanly.
Applied patch to '.gitignore' cleanly.
Applied patch to 'AGENTS.md' cleanly.
Applied patch to 'README.md' cleanly.
Applied patch to 'api.py' cleanly.
Applied patch to 'audit.py' cleanly.
Applied patch to 'autonomy.py' cleanly.
Applied patch to 'canonical_sources.py' cleanly.
Applied patch to 'continuous_research.py' cleanly.
Applied patch to 'evals/test_core.py' cleanly.
Applied patch to 'evals/test_mvp.py' cleanly.
Applied patch to 'execution_scheduler.py' cleanly.
Applied patch to 'nexus_system_bootstrap.py' cleanly.
Applied patch to 'ops.py' cleanly.
Applied patch to 'project_control_plane.py' cleanly.
Applied patch to 'projects.py' cleanly.
Applied patch to 'state.py' cleanly.
Applied patch to 'tests/test_nexus_system_bootstrap.py' cleanly.
Applied patch to 'tests/test_project_control_plane.py' cleanly.
(tests/test_system_capability_registry.py created as a new file)
```
**All 20 files apply cleanly** once the CRLF artifact is removed — including the two files with independent main-side changes (git's 3-way merge handled both without conflict markers).

### New test file in isolation

```
$ python -m pytest -q tests/test_system_capability_registry.py
...                                                                      [100%]
3 passed in 0.02s
```
Passes immediately, unmodified, against main's existing `system_capability_registry.py` (added in `0f1cf63`).

### `tests/test_project_control_plane.py`

- On clean `origin/main` (before patch): `6 passed`.
- With only `project_control_plane.py` patched but **not** `execution_scheduler.py` (to isolate the coupling): `9 passed, 3 failed` — all three failures are `ValueError: invalid_execution_lane` from `execution_scheduler.py`'s `_validate`, because `"sandbox"` isn't yet in `_LANES`. This confirms the two files are a coupled pair, not independently applicable.
- With the full CR-normalized patch applied (all 20 files): re-run below.

### Full suite, before and after

The repo's own collection failed with `ModuleNotFoundError: No module named 'fastapi'` / `'nexus_core'` on **both** clean main and the patched worktree — a pre-existing local environment gap (`pyproject.toml` sets `pythonpath = ["."]` but not `src/`), unrelated to this commit. After `pip install fastapi` and running with `PYTHONPATH=src`:

```
# origin/main, unpatched
$ PYTHONPATH=src python -m pytest -q tests/ evals/
1574 passed, 11 subtests passed in 9.38s

# origin/main + CR-normalized patch (all 20 files)
$ PYTHONPATH=src python -m pytest -q tests/ evals/
1585 passed, 11 subtests passed in 9.07s
```
**1585 − 1574 = 11**, exactly matching the commit's new tests (3 in `test_system_capability_registry.py` + 6 new/parametrized cases in `test_project_control_plane.py` + 2 in `evals/test_core.py`). **Zero failures, zero regressions**, full suite green both before and after.

---

## 4. Recommendation: **SMALL PR, with one item flagged for explicit owner sign-off**

Reasoning:
- 18 of the 20 files are safe, mechanical, well-tested improvements that are **genuinely absent on main** and apply cleanly (after CRLF normalization) with no regressions: the six-file `contextlib.closing()` resource-leak fix (`api.py`, `audit.py`, `autonomy.py`, `canonical_sources.py`, `ops.py`, `state.py` + their test coverage), the `system_capability_registry` activation wiring (`nexus_system_bootstrap.py`, its test), the AGENTS.md/SKILL.md FAL-handoff governance text, the `PRJ-FAL-01` project entry, the `.gitignore` entry, and the new `continuous_research` topic. These should be carried over largely as-is (re-authored with normal LF line endings — do not carry the CRLF artifact itself). `README.md`'s Ruflo section (item 4) should be **dropped**, since it's already superseded by main's actual (and since-disabled) Ruflo footprint.
- The one item needing owner review before merge is **`project_control_plane.py` + `execution_scheduler.py` together** (§1 row 15): the new `PILOT`/`ADOPTED_ADAPTER`-only execution gate is a real and currently-missing safety improvement — main today lets **any** cataloged agent, regardless of lifecycle (including still-`DISCOVERED`/`WATCH` ones), be selected for external-risk work with zero lifecycle check. But shipping the gate as-is, unaccompanied by any change to `seed_catalog()`, means the real catalog (still 100% `DISCOVERED`/`WATCH`/`EXPERIMENT`/`SANDBOX_READY`/`DEFERRED`, zero `PILOT`/`ADOPTED_ADAPTER` entries today) would never again produce a "running" assignment for non-sandbox work — everything blocks or waits. This is safe (fails closed) but is a large behavior change to a module that, per a repo-wide grep, has **no production callers yet** — so today the blast radius is contained to tests, but it needs the owner to consciously decide whether to (a) accept "no default execution until an agent graduates to PILOT/ADOPTED_ADAPTER" as intended, (b) promote a specific agent first, or (c) hold this hunk until the module is actually wired into a live path. This is exactly the class of change AGENTS.md/CLAUDE.md treat as an approval-gate matter (autonomy/eligibility logic), so it should not be merged silently inside an otherwise-routine cleanup PR.
- `tests/test_system_capability_registry.py` should simply be added to main outright — it runs unmodified against code main already has, 3/3 green, zero cost.

**Suggested PR split:**
1. **PR A (safe, mergeable now):** the `contextlib.closing()` fix across `api.py`/`audit.py`/`autonomy.py`/`canonical_sources.py`/`ops.py`/`state.py` (note: also apply the same wrap to `autonomy.py`'s newer `defer()` method, added on main after this commit, which still uses the unwrapped pattern), their test coverage in `evals/test_core.py` and `evals/test_mvp.py`, the `nexus_system_bootstrap.py` wiring of `system_capability_registry` + its test, `tests/test_system_capability_registry.py` as a new file, the `PRJ-FAL-01` entry in `projects.py`, the AGENTS.md/SKILL.md FAL-handoff text, the new `continuous_research` topic, and the `.gitignore` entry.
2. **PR B (owner decision required):** `project_control_plane.py` + `execution_scheduler.py` + the corresponding `tests/test_project_control_plane.py` changes, gated on an explicit owner call about `seed_catalog()` composition and whether/when this planning module gets a live caller.
3. **Drop:** the `README.md` Ruflo section (superseded).

No FULL REBASE is warranted — the parent is only 89 commits behind and every hunk merges cleanly once CRLF is normalized; this is scoped, low-conflict work, not a stale branch needing a ground-up redo.

---

## 5. Cleanup

```
git worktree remove --force /home/claude/scratch_ops08
git worktree remove --force /home/claude/scratch_ops08_baseline
```
(both removed at the end of this review; no remote refs, branches, or pushes were touched — this was read-only analysis against `origin/main` and local scratch worktrees only.)
