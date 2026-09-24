# Branch Triage — nexus-business-os — 2026-09-24

Repository: `github.com/rezarazzqi1379-boop/nexus-business-os`. `origin/main` is at `49ba5a0`.

Scope: the 71 branches that remain after the 57 already-merged/subset branches were deleted on the remote (per `/home/claude/work/BRANCH_INVENTORY_2026-09-24.md`), excluding `main`, `fix/governance-carryover-v0.1` (open PR #99) and `feat/unified-system-governance-v0.1` (under separate review). This reuses that inventory's ahead/behind, dates and unique-file counts, adds actual unique-file paths, checks each one against main's current module/file layout, and spot-tests the top candidates.

## 1. One-screen summary

| Recommendation | Count |
|---|---|
| MERGE-CANDIDATE | 9 |
| SALVAGE-PARTS | 14 |
| OWNER-CALL | 8 (4 giant forks + 4 mid-size independent forks) |
| ARCHIVE | 40 |
| **Total triaged** | **71** |

**Top 5 actions, in priority order:**

1. **Merge `feat/steel-recovery-v0.1` first.** It is the most current branch in the whole set (only 14 commits behind main, last touched 2026-09-22), contains 5 real engineering-review fixes to the active slab-line design plus updated vendor-ready documentation, and its 70-test eval suite passes cleanly at the branch tip. Everything else can wait behind this one.
2. **Take the 8 other small MERGE-CANDIDATEs as a batch** (see §2): each is a self-contained, pure-addition feature (new file + doc + test, zero deletions from main), so they can be reviewed and merged with minimal risk. `hardening/supplier-collision-gate-v0-1` was spot-tested and its 15 tests pass unmodified against current main — safest of the batch.
3. **Decide the two abandoned-architecture families before touching anything else in them.** (a) The **NEXUS Brain ontology/shadow-execution** line (11 branches, all ARCHIVE) — main's `src/nexus_brain` went a completely different direction (AI provider routing) and none of that line's files exist there. (b) The **`nexus_control_plane` workforce/forge** line (4 branches, all OWNER-CALL) — main has no `nexus_control_plane` package at all; these are a large, real, independent architecture proposal that needs a yes/no product call, not a code review.
4. **Get the owner's OK to delete the 40 ARCHIVE branches** (full tip SHAs recorded in §4) — they are docs/data snapshots superseded by main's later versions, strict content-subsets of a kept branch, or (in two hydrotester cases) would actively regress safety logic main added later.
5. **Route the 14 SALVAGE-PARTS branches to a developer** with the specific file list from §2 — each has a small, real kept-part and a larger superseded/stale part; nothing here needs a product decision, just an hour of code review per branch.

## 2. Branch-by-branch table

Sorted alphabetically. "Uniq files" = files that differ from main's current content, CR-stripped, measured against each branch's merge-base with main (same methodology as the prior inventory; recomputed and re-verified against current main). Full unique-file lists per branch are in `/home/claude/work/scratch/unique_files_by_branch.tsv`.

| Branch | Recommendation | Uniq files | Reason |
|---|---|---|---|
| `architecture/convergence-wave-v0-1` | ARCHIVE | 2 | Planning doc + data snapshot (2026-08-27, 157 behind); "convergence wave" appears nowhere in current main — abandoned plan. |
| `architecture/core-consolidation-v0-1` | ARCHIVE | 2 | Consolidation plan + readiness-critic doc (186 behind); superseded, no trace in main. |
| `architecture/zero-day-deal-desk-v1` | ARCHIVE | 2 | "Global Operating Directive v1.0" + "Zero-Day Deal Desk" pack; neither term appears anywhere in main — abandoned strategy proposal (owner may want a last look before delete). |
| `chore/restore-main-ci-v0-1` | ARCHIVE | 1 | Touches `.github/workflows/test.yml`; main's current workflow is already larger (branch would *remove* 14 lines main has since added) — fully superseded. |
| `experiment/altari-public-patterns-v0-1` | OWNER-CALL | 21 | Sibling of `feature/nexus-forge-loop-v0-1` (identical fork point, byte-identical `workforce.py`/`workforce_orchestrator.py`); builds an unmerged `src/nexus_control_plane` workforce/project-fabric package main never adopted. See §3 family note. |
| `experiment/model-runner-arena-v0-1` | ARCHIVE | 2 | `runner_registry.py` superseded — main's current version is far larger (branch would remove 56 lines main has added since). |
| `experiment/productization-contract-v0-1` | MERGE-CANDIDATE | 3 | `src/nexus_verticals/productization.py` + doc + test — pure new module, no equivalent anywhere on main, self-contained. |
| `experiment/research-data-mesh-v0-1` | ARCHIVE | 2 | Old CI workflow (smaller than current main) + a one-line `nexus_core/__init__.py` import; 196 behind, superseded. |
| `feat/authority-reconciliation-status-v0.1` | ARCHIVE | 1 | `docs/authority/AUTHORITY_STATUS.md` already exists on main at the same path with far more content (main last touched it 2026-09-17, ten days after this branch) — stale snapshot. |
| `feat/dual-ai-task-handoff-v0.1` | ARCHIVE | 1 | Confirmed git ancestor of `feat/nexus-coordination-kit-v0.2` and `feat/public-handoff-mirror-contract-v0.1` — fully contained in the kept branch below. |
| `feat/external-access-broker-v0-1` | MERGE-CANDIDATE | 10 | 4 new root-level modules (`external_access_broker.py`, `account_bootstrap.py`, `capability_mesh.py`, `provider_resolution.py`), all pure additions vs. main, plus 2 docs and 4 dedicated eval tests. Coherent gated feature, zero overlap with main. |
| `feat/fal-vertical-binding-v0.1` | SALVAGE-PARTS | 2 | `fal_vertical.py` diverges from main's current version in both directions (adds 101 lines, is missing 33 main has) — needs a developer diff to separate the real improvement from what main already fixed differently. |
| `feat/meta-orchestrator-control-plane` | ARCHIVE | 4 | Content subset of `feature/nexus-forge-loop-v0-1`'s `control_plane.py` (281 vs. 327 lines, same base). Part of the abandoned control-plane family (§3). |
| `feat/nexus-capability-portfolio` | ARCHIVE | 2 | `runner_registry.py` again superseded (would remove 47 lines main has added); its other file is a stale eval test. |
| `feat/nexus-coordination-kit-v0.2` | ARCHIVE | 3 | Content subset of `feat/public-handoff-mirror-contract-v0.1` (confirmed ancestor); `coordination_kit.py`/`task_handoff.py` were both rewritten by main on 2026-09-17, twelve days after this branch. |
| `feat/nexus-herdr-runtime` | ARCHIVE | 2 | `docs/ADR-003-NEXUS-AGENT-SUPERVISOR.md` already exists on main under the same name; `runner_registry.py` superseded (would remove 87 lines). |
| `feat/posthog-observability-v0-1` | MERGE-CANDIDATE | 3 | `posthog_adapter.py` + doc + test — pure new addition, no overlap with main. |
| `feat/public-handoff-mirror-contract-v0.1` | SALVAGE-PARTS | 7 | Superset of the two branches above. `coordination_kit.py`/`task_handoff.py` edits are superseded by main's later rewrite, but `public_mirror_guard.py`, `schemas/public_handoff_record_v1.schema.json` and their test are new and not superseded — **keep only those 3 files.** |
| `feat/railway-control-layer-v0-1` | MERGE-CANDIDATE | 3 | `railway_control.py` + runbook doc + test — pure new addition, no overlap with main. |
| `feat/steel-recovery-v0.1` | **MERGE-CANDIDATE (top priority)** | 9 | Only 14 commits behind main, last commit 2026-09-22. 5 commits of real engineering-review fixes to `slab_line_design.py` (main already has the file; branch adds 365 lines of vendor-ready design + corrections) plus updated engineering-package docs and a system audit. **Its 70-test eval suite (`evals/test_slab_line_design.py`) passes at the branch tip — verified in a scratch worktree.** |
| `feat/trade-intel-vertical-proof-v0.1` | SALVAGE-PARTS | 2 | `discovery_pipeline.py` diverges from main in both directions (adds 37 lines, missing 55 main has); commit says "harden approval pack and JSONL ingest per review" — needs a developer diff to see if the fix is still needed. |
| `feature/ai-resource-router-v0-1` | ARCHIVE | 6 | `resource_router.py` and `provider_registry.py` already exist on main and are more developed; doc content also superseded. |
| `feature/ai-router-v0-2-hardening` | ARCHIVE | 2 | Same hardening doc already exists on main in a more complete form. |
| `feature/ai-router-v0-5-public-shadow-probe` | ARCHIVE | 2 | `public_shadow_probe.py` superseded by main's larger current version. |
| `feature/audit-event-envelope-v0-1` | SALVAGE-PARTS | 5 | `src/nexus_core/audit_events.py` + test is a genuine gap (not on main) but byte-identical to the copy inside `integration/shadow-pr1-pr2-pr4-pr7-pr8` — pick it up from whichever of the two survives review, not both. Other 3 files are background docs, low value. |
| `feature/business-genome-opportunity-engine-v01` | OWNER-CALL | 25 | Full "Business Genome" opportunity-scoring vertical (pattern mining, procurement friction, pre-RFQ readiness) with its own calibration data — a real, coherent, independent product feature large enough to need a go/no-go decision, not a quick merge. |
| `feature/durable-shadow-queue-v0-1` | ARCHIVE | 2 | Part of the abandoned NEXUS Brain shadow-execution family — see §3. |
| `feature/eval-harness-v0-1` | ARCHIVE | 3 | `src/nexus_core/eval_harness.py` has no main equivalent, but main solved "eval harness" a different way (the `src/nexus_evals` package, already adopted from other branches) — superseded design, oldest branch in the set (2026-08-19). |
| `feature/evidence-classification` | ARCHIVE | 4 | `procurement.py`/tests are byte-identical to content already inside `integration/shadow-pr1-pr2-pr4-pr7-pr8` (kept for review) — fully redundant, oldest branch in the set. |
| `feature/execution-intent-v0-1` | ARCHIVE | 2 | Abandoned NEXUS Brain family (`execution.py` under `nexus_brain` — see §3). |
| `feature/execution-shadow-bridge-v0-1` | ARCHIVE | 2 | Same family (`execution_bridge.py`). |
| `feature/hydrotester-qualification-matrix-v0-1` | ARCHIVE | 2 | Superseded: main independently produced a `_v0_2.json` of the same data file with far more content (521-line diff) under a renamed path. |
| `feature/hydrotester-readiness-engine-v0-1` | ARCHIVE | 2 | **Would regress safety.** Removes the "unresolved-fields fail closed" check and extra `BLOCKING_FIELD_STATUSES` entries that main's current `hydrotester_readiness.py` added later. Do not merge. |
| `feature/nexus-brain-plo-contract-v0-5` | ARCHIVE | 4 | Abandoned NEXUS Brain family (`plo_contract.py`, `shadow_loop.py` — see §3). |
| `feature/nexus-brain-v0-1` | ARCHIVE | 7 | Same family — foundational piece (`model.py`, `graph.py`) of the abandoned ontology design. |
| `feature/nexus-brain-v0-2` | ARCHIVE | 5 | Same family (`projection.py`/`html.py`/`fixtures.py` build on v0-1's `graph.py`, which doesn't exist on main). |
| `feature/nexus-brain-v0-3-live-snapshot` | ARCHIVE | 4 | Same family (`command.py`/`live.py`). Real, unmerged content — but for a Brain design main didn't adopt. Name is misleading (not a repo backup). |
| `feature/nexus-brain-v0-4-command-live` | ARCHIVE | 2 | Same family (`runtime_snapshot.py`). |
| `feature/nexus-forge-loop-v0-1` | OWNER-CALL | 78 | Largest of the control-plane family: forge/generation-ledger/telemetry/recursive-evolution/architecture-selector — an entire alternate "self-improving forge" control plane with its own data snapshots. Content-superset of `feat/meta-orchestrator-control-plane`; shares `workforce.py`/`workforce_orchestrator.py` verbatim with `experiment/altari-public-patterns-v0-1`. Too large and too strategic for a quick merge call — see §3. |
| `feature/nexus-integrated-shadow-loop-v0-4` | ARCHIVE | 2 | Same NEXUS Brain family (`shadow_loop.py`, same file as plo-contract-v0-5). |
| `feature/omniroute-evaluation-v0-1` | SALVAGE-PARTS | 3 | `nexus_core/omniroute_evaluation.py` diverges from main's current version in both directions (small, ~13/10 lines) — needs a quick developer diff. Its data snapshot (2026-08-28) is likely stale. |
| `feature/p0-benchmark-pair-v0-1` | ARCHIVE | 2 | Its hydrotester-matrix data + test are superseded by main's own, far more detailed `_v0_2.json` of the same file. |
| `feature/postgres-shadow-queue-v0-1` | ARCHIVE | 4 | Abandoned NEXUS Brain family (`postgres_shadow_queue.py` — see §3). |
| `feature/requirement-readiness-shadow` | ARCHIVE | 1 | Single old research doc (199 behind), no code; superseded by main's much larger current hydrotester documentation set. |
| `feature/shadow-worker-v0-1` | ARCHIVE | 2 | Abandoned NEXUS Brain family (`shadow_worker.py`). |
| `feature/temporal-evidence-opportunity-radar-v0-1` | SALVAGE-PARTS | 14 | 5 genuinely new `nexus_core` modules (`temporal_evidence.py`, `opportunity_radar.py`, `hydrotester_vertical.py`, `portfolio_alignment.py`, `engineering_fat_generator.py`) with matching tests, no main equivalent — real, reasonably coherent gap. **Keep the 5 src + 5 test files; drop the 4 dated (2026-08-28) research docs/data snapshots.** |
| `feature/trace-envelope-v0-1` | MERGE-CANDIDATE | 4 | Self-contained new `src/nexus_observability` package (`events.py` + `__init__.py`) with test and doc, no main equivalent. Oldest branch in the set but small and easy to review. |
| `feature/vertical-acceptance-observability-v0-1` | SALVAGE-PARTS | 5 | `nexus_core/vertical_acceptance.py` + test is a genuine new gap. **Keep those 2 files; drop the 3 dated (2026-08-28) research data/replay snapshots.** |
| `fix/canonical-authority-v2` | ARCHIVE | 1 | `canonical_sources.py` diff shows the branch *removing* 32 lines relative to current main — it's the older, smaller version; superseded. |
| `fix/harden-openai-live-gate-v0-1` | ARCHIVE | 2 | Small, roughly balanced diff on `openai_api_adapter.py` that main has kept independently editing since (152 behind); second file is a mismatched test name suggesting test drift. Low confidence there's anything left to salvage. |
| `fix/hydrotester-readiness-usable-evidence-v0-1` | ARCHIVE | 2 | Same regression as `feature/hydrotester-readiness-engine-v0-1` above — strips fail-closed safety logic main's current version already has. Do not merge. |
| `fix/mobile-login-session-v1` | SALVAGE-PARTS | 3 | `security.py` change is superseded, but no "mobile session login" concept exists on main at all. Real feature idea; code needs re-implementing against current `security.py` (moved on 2026-09-19), not a direct merge. |
| `fix/owner-login-separation-v1` | SALVAGE-PARTS | 4 | Same situation — "separate owner credentials from API token" doesn't exist on main; worth a look as a security/product feature, but `security.py`/`api.py` have moved on since 2026-08-31. |
| `fix/supervisor-exact-approval-boundary-v0-1` | ARCHIVE | 2 | Superseded — main's *current* `agent_supervisor.py` is already stricter than this branch: it removes the `human_approved` boolean bypass entirely rather than just checking it, which is what this branch still does. |
| `governance/global-cross-chat-directive-v1` | ARCHIVE | 3 | 3 cross-chat governance docs (2026-08-22, 187 behind); "ChatGPT project bootstrap" concept never referenced again; superseded by main's much larger current governance doc set. |
| `hardening/core-exact-external-action-v0-1` | SALVAGE-PARTS | 3 | `nexus_core/exact_external_action.py` + test is a genuine gap (not on main anywhere). **Keep those 2 files; drop the old `nexus_core/__init__.py` edit.** |
| `hardening/exact-external-gate-v0-2` | ARCHIVE | 4 | Confirmed strict content-subset of `hardening/external-ingress-guard-v0-2` (identical 4 files). |
| `hardening/external-ingress-guard-v0-2` | SALVAGE-PARTS | 7 | Content-superset of the branch above. Its own `external_ingress_guard.py` is superseded (main's version is 109 lines more developed), but `exact_external_gate.py` (root + `nexus_security`, absent from main) plus its test are a real, still-open security gap. **Keep those 3 files; drop `external_ingress_guard.py`.** |
| `hardening/supplier-collision-gate-v0-1` | MERGE-CANDIDATE | 1 | Single 238-line **pure-addition** test file for the existing `supplier_identity.py` — zero deletions. **Spot-tested: all 15 tests pass unmodified against current main.** Lowest-risk merge in the whole set. |
| `integration/pr19-pr33-e2e` | ARCHIVE | 19 | Heavily overlaps `feature/business-genome-opportunity-engine-v01` (shares `business_genome*.py`) but is missing several of that branch's files (`pre_rfq_*`, `procurement_friction.py`); its only distinct file is one thin e2e test — better captured by reviewing the business-genome branch directly. |
| `integration/shadow-pr1-pr2-pr4-pr7-pr8` | SALVAGE-PARTS | 26 | Its `nexus_evals/*` content already landed in main under different SHAs (4-line diff, essentially identical). But `audit_events.py`, `autonomy.py`, `autonomy_adapters.py`, `checkpoints.py`, `goal_portfolio.py` are genuine gaps with full dedicated tests (`test_autonomy_fabric.py`, `test_checkpoints.py`, `test_goal_portfolio.py`, etc.). **Keep those 4 src modules + their tests; drop the `nexus_evals` files (redundant) and `procurement.py` (duplicate of `feature/evidence-classification`).** |
| `nexus-vnext-hydrotester-vertical` | SALVAGE-PARTS | 6 | `claim_state.py` (74-line pure addition) and `engineering_sanity.py` are genuinely new, each with a dedicated eval test; `state.py` change is a small compatible addition. Worth a developer's look as one coherent small extension. |
| `nexus/oig-integration-v01` | ARCHIVE | 1 | Single old cross-project integration doc (186 behind), no code; "oig-integration" appears nowhere else in main. |
| `plo-v0.2-linux-runtime` | OWNER-CALL | 20 | Full independent cloud runtime under `runtime/plo_cloud/` (Docker, least-privilege Postgres store, Gmail read-only adapter, control bridge, worker, its own CI workflow, 9 dedicated tests). A real infrastructure/product-direction question — does the owner still want this "PLO Cloud" runtime path — not a code-review-sized decision. |
| `research/agent-catalog-scout-2026-08-31` | SALVAGE-PARTS | 4 | `codex_app_server_adapter.py` + test is a genuine new module. **Keep those 2 files; drop the two dated (2026-08-31) research data snapshots.** |
| `security/exact-send-core-v0-1` | MERGE-CANDIDATE | 2 | `nexus_control_plane/exact_send.py` + test — a genuinely new "exact-send approval binding" primitive, not present anywhere on main. Small and self-contained (would need to land under `nexus_core` instead of the currently-nonexistent `nexus_control_plane` package). |
| `security/policy-threat-model-v0-1` | MERGE-CANDIDATE | 2 | `SECURITY.md` + `docs/security/threat-model-v0-1.md` — **main has neither file at all today.** Pure documentation addition, oldest branch in the set but zero conflict risk. |

## 3. Giant-forks section

Four branches carry 200+ commits each and were characterized, not reviewed commit-by-commit, per instructions.

| Branch | Ahead of main | Fork point | Unique files |
|---|---|---|---|
| `feature/agent-evolution-kernel-v0-1` | 261 commits | `68d61bb` (2026-08-19) | 155 |
| `feature/autonomy-runner-v0-1` | 256 commits | `68d61bb` (2026-08-19) | 155 |
| `hardening/outreach-per-send-approval-v0-1` | 233 commits | `68d61bb` (2026-08-19) | 132 |
| `hardening/prompt-injection-e2e-v0-1` | 220 commits | `68d61bb` (2026-08-19) | 130 |

**All four fork from the exact same commit**, one day into the project. **None is a git ancestor of another** — they are four independent lines that grew out of a single abandoned "rebuild the whole core" attempt.

**What they actually are:** all four carry a huge, near-identical **128-file common core** (mostly under `src/nexus_core/` — 58-60 files each — and `src/nexus_autonomy/` — a package that does not exist on main at all) that is essentially the same in every branch. This is an alternate, from-scratch rewrite of NEXUS's core that was abandoned in favor of main's own (differently-shaped) `src/nexus_core`, which has since grown to 28 files of its own, unrelated to this line.

On top of that shared core, each branch adds a small, distinct capability:
- `feature/agent-evolution-kernel-v0-1`: adds `src/nexus/agent_evolution.py` + doc + test (3 files not shared with any other giant).
- `feature/autonomy-runner-v0-1`: adds `src/nexus_autonomy/contact_health.py` ("contact channel health") + doc + test (3 files not shared with any other giant). It otherwise shares 152/155 files verbatim with `agent-evolution-kernel`, making the two near-twins.
- `hardening/outreach-per-send-approval-v0-1`: adds `src/nexus_core/outreach_execution.py` + 2 tests (the "per-send approval" gate itself).
- `hardening/prompt-injection-e2e-v0-1`: adds only one file not shared with the others (`tests/test_prompt_injection_e2e.py`); it shares 129/130 files with `outreach-per-send-approval`, making it very nearly a strict subset of that branch (missing only `outreach_execution.py` and its 2 tests).

**Superset check:** no single branch is a superset of all others by file content. There are two near-identical pairs — (`agent-evolution-kernel` ≈ `autonomy-runner`) and (`prompt-injection-e2e` ⊂-ish `outreach-per-send-approval`) — but the two pairs only share the common 128-file core with each other, not any distinct capability files.

**Recommendation: OWNER-CALL for all four**, treated as one family decision rather than four separate ones. This is not a mergeable feature branch — it is an abandoned full-repo alternate architecture (128+ shared files reimplementing `nexus_core`/`nexus_autonomy` in a way that has nothing to do with main's current, independently-evolved `nexus_core`). Reviving any of it means either (a) accepting the whole alternate core as a replacement for main's current one — a major rearchitecture decision — or (b) cherry-picking just the small headline capability (agent evolution, contact-channel health, per-send outreach approval, or the prompt-injection e2e test) and re-implementing it against main's actual current core, which is a normal-sized follow-up task once the direction is chosen. Given the size, do not have a developer read these commit-by-commit; have the owner decide whether any of the four capabilities is still wanted, then scope a fresh small branch for just that capability against current main.

## 4. ARCHIVE branches — full tip SHAs (for restore)

| Branch | Tip SHA |
|---|---|
| `architecture/convergence-wave-v0-1` | `830e9c4670893c4c3ad7435f8b84bd5fb3d2f5b8` |
| `architecture/core-consolidation-v0-1` | `a8c386c9e5a4a337391b269eb35dd092c3a64849` |
| `architecture/zero-day-deal-desk-v1` | `4e4a5bc1b6acca0e67239d9012e9eae8d61334d3` |
| `chore/restore-main-ci-v0-1` | `ff0fffe0b1301ea41a1c251931376fdd7a237b3d` |
| `experiment/model-runner-arena-v0-1` | `3e1316ea82d532da3b9d160a4ea14342339789a3` |
| `experiment/research-data-mesh-v0-1` | `57e2e3361662a7a0a94ad213e4346e84a800b5d3` |
| `feat/authority-reconciliation-status-v0.1` | `84800ae91edb8b12bae47666a1d639caf4837625` |
| `feat/dual-ai-task-handoff-v0.1` | `10cabad73ae2822c86d222511aecd98e342cb068` |
| `feat/meta-orchestrator-control-plane` | `fdf3f5040e495df5cc985dac61cd0fc2eff1059a` |
| `feat/nexus-capability-portfolio` | `53be651445c1b02570e37ca0254d17fc9fe9d1b0` |
| `feat/nexus-coordination-kit-v0.2` | `c4387b5ba252ff8a7d5da59b01f35208e0f5a1a4` |
| `feat/nexus-herdr-runtime` | `87e78b43ac8b567191bd1bc11288a675b2775502` |
| `feature/ai-resource-router-v0-1` | `fb1bba7c24877146bd4670ed4c68c158a63d82d6` |
| `feature/ai-router-v0-2-hardening` | `28d4560a1b800d7a2aa0b576b0a94e8e8c3003e8` |
| `feature/ai-router-v0-5-public-shadow-probe` | `c2a219d707a4518bf285cae8f4b21ad3538258d8` |
| `feature/durable-shadow-queue-v0-1` | `3f9b531cb8ccb0d4d0184c69d77112fd594e637c` |
| `feature/eval-harness-v0-1` | `6b48ab06e2268cac906647c035cd0b77d2bfab6f` |
| `feature/evidence-classification` | `9596b15ec62512448bf9d4377b103ece302d7f87` |
| `feature/execution-intent-v0-1` | `659e9ca9214135b1a586aedad2bb0427f7d23b60` |
| `feature/execution-shadow-bridge-v0-1` | `4b1a0569480acf81fd019b6fb065de82bf02ed64` |
| `feature/hydrotester-qualification-matrix-v0-1` | `ba34b45b0ec30844478ae8d303e24551a172cc66` |
| `feature/hydrotester-readiness-engine-v0-1` | `a59d9a86bfac25fcf132c18735b4d0ef9ff32e7b` |
| `feature/nexus-brain-plo-contract-v0-5` | `588d47f54b2b70970701fe1d75ed9c1171ae0e81` |
| `feature/nexus-brain-v0-1` | `033b3385f397c79443a871dea5846ff77bfdc0ca` |
| `feature/nexus-brain-v0-2` | `c463e9eecbec9d90146a9630271fae1803aa40cf` |
| `feature/nexus-brain-v0-3-live-snapshot` | `4dffcf827ffa3e5052d50e39ceb75e2e4680e92b` |
| `feature/nexus-brain-v0-4-command-live` | `1ed04a337afbd5ffe65019df2ecc652ce2985951` |
| `feature/nexus-integrated-shadow-loop-v0-4` | `690c17bf1ed81e75cd82f52fe79f9daba0ab62a7` |
| `feature/p0-benchmark-pair-v0-1` | `2866c367482888edb4df6109c952d21a0a519700` |
| `feature/postgres-shadow-queue-v0-1` | `01204f887018bd1ea6d7f5919478ade561750251` |
| `feature/requirement-readiness-shadow` | `1dbe2546cc3d7acb13f869d6dae8fd55d21e7922` |
| `feature/shadow-worker-v0-1` | `3b3e215cd42384152aea3322e74d4bea6189626c` |
| `fix/canonical-authority-v2` | `2072075775c0021d8c12a1b9f69c43bc04aef8c2` |
| `fix/harden-openai-live-gate-v0-1` | `dff5673906a8175f786eadba018b28001ca457d4` |
| `fix/hydrotester-readiness-usable-evidence-v0-1` | `3046499e228845dc083335936fc720b50f8187df` |
| `fix/supervisor-exact-approval-boundary-v0-1` | `9f300079e3db548a7d7c41d1df047eccc9e4ab82` |
| `governance/global-cross-chat-directive-v1` | `a6933b11c6e79904acf5fa801b5474edc8bf8e7b` |
| `hardening/exact-external-gate-v0-2` | `d3fc1f4e9e477d29f3d0fd43c21e186f1d1a48b9` |
| `integration/pr19-pr33-e2e` | `087559e548e8147ae385125febef5816a92f2810` |
| `nexus/oig-integration-v01` | `77f9dc6e4c7dd79a16e610d307a59a7670ec7485` |

Note: `fix/supervisor-exact-approval-boundary-v0-1` is one of the two branches (with `feature/hydrotester-readiness-engine-v0-1` / `fix/hydrotester-readiness-usable-evidence-v0-1`) where merging would actually be a step backward from main's current safety logic — flagged in §2, safe to delete with confidence.

## 5. Excluded from this triage

- `main` (baseline).
- `fix/governance-carryover-v0.1` — open PR #99, reviewed separately.
- `feat/unified-system-governance-v0.1` — under separate review (holds commit `2451722`, per the prior inventory).
