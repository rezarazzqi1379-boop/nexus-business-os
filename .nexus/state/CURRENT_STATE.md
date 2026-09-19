# NEXUS CURRENT STATE
Last updated: 2026-09-19 by Claude Code (via Reza) -- reconciled the second main/feat divergence (see MAIN/FEAT MERGE #2 section at the end); rest unchanged
RULE: Read this file FIRST in any new session before doing anything
else. Overwrite stale sections when updating — do not just append.

## ⚠️ ENVIRONMENT WARNING — TWO INDEPENDENT CLONES EXIST
Confirmed 2026-09-07 (git cat-file -t cross-check, definitive):

- Clone A (Claude Code): C:/Users/AvallPc/nexus-business-os
- Clone B (Codex/ChatGPT): C:\Users\AvallPc\.codex\.chatgpt-projects\
  g-p-6a8492b077348191a541806c6ff52d75\nexus-business-os

These have SEPARATE .git object stores pointing to the same GitHub
remote. A commit pushed from one is NOT visible in the other until
that clone does `git fetch`. Any cross-AI comparison/reconciliation
work MUST start with an explicit fetch on both sides, or SHAs will
appear to "not exist" when they actually do (just not fetched yet).

## ⚠️ PYTHON ENVIRONMENT WARNING
`python` on PATH is a Windows Store stub with NO project dependencies
installed (no fastapi/uvicorn/pytest/httpx). The real environment is
`.venv/Scripts/python.exe` in each clone. ALWAYS specify this
explicitly in any test-running instruction to any AI/agent — do not
assume `python`/`pytest` bare commands use the right interpreter.

## AUTHORITY STATUS — ⚠️ UNRESOLVED, BLOCKING
Status: AUTHORITY_CONFLICT / RECONCILIATION_PENDING since 2026-08-28

- Notion Cross-AI Handoff Log recorded an OPEN HOLD on 2026-08-28:
  GitHub main allegedly declared "Master v1.9 / Registry v1.6" but
  artifacts were not retrievable. Never closed. Zero follow-up for
  10 days until rediscovered on 2026-09-07.
- Two files (NEXUS_Source_Registry_v1.8_2026-09-01.docx,
  NEXUS_Master_Context_v2.1_2026-09-01.docx) are REAL (exist in
  File Library) but NOT independently confirmed in Drive or Notion
  as the canonical store. Master_Context_v2.1 also has an internal
  self-contradiction: its own authority section says v1.8/v2.1
  govern; its own activation section says v1.9/v1.6 are active.
- Only versions independently verified as actually stored in
  Drive/Notion: Source Registry v1.1, Master Context v1.4
  (dated 2026-08-24).
- A docs/authority/AUTHORITY_STATUS.md exists on branch
  feat/authority-reconciliation-status-v0.1 (based on main),
  independently corroborated by two separate AI sessions. NOT yet
  merged to main — deliberately held until reconciliation completes.
- DO NOT cite PRJ-FAL-01-EV-001 ("Pars Damghan") as a registered
  CLAIM anywhere — not even with the CLAIM label — until this
  reconciles. Generic FAL-A/FAL-B structure (import ferromanganese /
  export ferrosilicon, lane isolation) is fine to keep using; it
  doesn't depend on which version wins. As of 2026-09-07 both
  fal_vertical.py and prj_fal_01.py have had authority-wording
  cleanup applied (canonical/governing language removed, replaced
  with "working structural model... reconciliation pending") —
  independently cross-verified by Claude Code via git fetch/git show.
- NEXT ACTION (owner: ChatGPT/NEXUS): build a full Authority
  Reconciliation Pack comparing v1.1/v1.4/v1.6/v1.8/v1.9/v2.1,
  publish ONE resolved version to Drive AND docs/authority/ in repo.

## PROJECT PRIORITIES (confirmed 2026-09-05, not disputed)
- Geography: Iran = Tier 0 (deepest local layer, not "Iran only").
  Tiers 1-4 are priors, evidence-adaptive reranking, not fixed.
- First commercial vertical: PRJ-FAL-01 (Ferroalloys) — architecture
  proceeds regardless of the authority dispute above.
  - FAL-A: ferromanganese import to Iran → supplier discovery
  - FAL-B: ferrosilicon export from Iran → foreign buyer discovery
  - Lanes must stay isolated (no shared prices/counterparties/evidence)
- After FAL: KCl/SOP → Hydrotester → Can Forming. Heat Treatment paused.
- Buyer discovery is primary goal; supplier discovery equally supported.
- No live Iranian source has been contacted yet (LIVE_PROVIDER_UNWIRED
  across all 8 source families in iran_source_providers.py). This is
  a deliberate, separate future decision — NOT to be inferred from
  "continue autonomously" instructions. Live outreach to real
  Iran-related commercial contacts may carry export-control/compliance
  considerations — get real legal advice before that step.

## ARCHITECTURE DECISIONS (settled, don't re-litigate)
- REJECTED: live AI-to-AI autonomous bridge / message bus / daemon
  that lets one AI execute the other's instructions.
- ACCEPTED: GitHub-backed Coordination Kit (task_handoff.py →
  coordination_kit.py → public_mirror_guard.py). Repo-file-based only.
- Public mirror exists: github.com/rezarazzqi1379-boop/nexus-ai-handoff-public
  (data only, never authority/instructions — governance rules in its README).
- human_authorized_extra_rounds (bool) → replaced with
  extra_round_approval_id bound to a real ApprovalStore grant.
  KNOWN GAP: verify_handoff_package() doesn't yet independently
  re-check this against a live ApprovalStore in a separate process.
- cross_project_touch: v1=bool, v2=tuple. NOT unified. Adapter:
  v1 False→v2 (), v1 True→v2 fail-closed UNKNOWN sentinel.
- TestEvidenceV2 distinguishes CALLER_DECLARED vs
  INDEPENDENTLY_CAPTURED; capture_test_evidence() structurally cannot
  accept a caller-supplied head_sha.
- Secret guard is pattern-based only — "no findings" ≠ "confirmed
  secret-free." Documented, not solved.
- Review-round budget: 2 automatic, 3rd requires a real
  human-set approval record, never an AI self-assertion.

## BRANCH STATE (updated 2026-09-07)
10+ branches, two independent stacks + one standalone + FAL duplicates:
- Standalone: feat/prj-hyd-01-engineering-review-v0.1
- Stack 1 (Deep Search): research-evidence-provider-v0.1 (root) +
  deep-research-lab-v0.1 (root) → discovery-pipeline-v0.1 →
  trade-intel-vertical-proof-v0.1 → deep-search-fabric-v2-core-engine
  → deep-search-market-intelligence-v0.1 (contains prj_fal_01.py,
  iran_source_providers.py, market_intelligence.py, persian_text.py)
- Stack 2 (Coordination): dual-ai-task-handoff-v0.1 (root) →
  nexus-coordination-kit-v0.2 → public-handoff-mirror-contract-v0.1
- feat/fal-vertical-binding-v0.1: independently real (was mistakenly
  thought to be a ghost reference — confirmed real 2026-09-07, 13/13
  tests pass, pushed by ChatGPT via a SEPARATE Codex clone — see
  environment warning above). Contains fal_vertical.py. Authority
  wording cleaned up 2026-09-07 (commit 6474519), independently
  verified via git fetch/git show by Claude Code.
- feat/authority-reconciliation-status-v0.1: docs/authority/
  AUTHORITY_STATUS.md, based on main, not yet merged.
- feat/nexus-state-tracking-v0.1: MERGED to main 2026-09-07
  (fast-forward, e1d01fa...→e07869d...). This file now lives directly
  on main.
- DUPLICATION UNRESOLVED: fal_vertical.py vs prj_fal_01.py — both
  real, both tested, comparison table exists (fal_vertical.py has
  better state enforcement/lexicon/isolation API; prj_fal_01.py has
  a unique buyer-classification bug fix). NOT yet reconciled into one
  canonical file — pending a neutral comparison harness AND a
  semantic decision on END_USER vs IMPORTER for FAL-A's home role.
- Verified mergeable in dependency order with 0 conflicts (disposable
  local test, nothing pushed/merged). No real GitHub PRs opened yet
  for any of these (no gh CLI in Claude Code's environment).
- No PR has been created. No merge to main. Nothing deployed.

## OTHER REAL ASSETS DISCOVERED (2026-09-07, exist but disconnected from GitHub)
- Google Drive: NEXUS_CANONICAL_CONFLICT_REGISTER_v1 (stale since
  23 Aug — different conflict-tracking doc than the Notion HOLD above)
- Google Drive: ATF_Asset_Registry_CURRENT_v1.0 — ALREADY BUILT,
  well-designed: SHA-256-locked golden masters for logo/stamp/
  signature, fail-closed release gate, 6/6 tests passed. Open gap:
  EN/FA letterheads still REVIEW_ONLY_PRINT_RELEASE_BLOCKED (not true
  vector/300dpi masters yet). Linking into docs/authority/ deferred —
  kept as a separate lane from NEXUS/FAL authority reconciliation.
- Notion: "Cross-AI Handoff Log" — 63 entries, ChatGPT-only (no Claude
  entries ever), last activity 2026-08-28. Effectively superseded by
  GitHub .nexus/handoffs/ going forward but its history was never
  migrated — this is where the authority HOLD was found.

## OPEN / NEXT ACTIONS
1. [ChatGPT] Close the authority reconciliation (see above) — blocking.
2. [Either AI] Build a neutral comparison harness for fal_vertical.py
   vs prj_fal_01.py; resolve END_USER vs IMPORTER via semantic
   review, not just code-convention matching. Both clones must fetch
   first and use their own .venv/Scripts/python.exe.
3. [Reza] Decide: merge docs/authority/AUTHORITY_STATUS.md to main
   once reconciliation completes (currently deliberately held on a
   separate branch).
4. [Reza] Decide: proceed with live Iran-source integration (first
   real attempt at ONE source) or hold for legal/compliance check first.
5. [DONE, 2026-09-14, commit 7e7c96f, on main — corrected 2026-09-17]
   Opportunity Suggestion Engine (Track E) is BUILT, not just designed:
   opportunity_suggestion_engine.py (251 lines) + evals/test_opportunity_suggestion_engine.py
   (16/16 tests passing, verified 2026-09-17). Draft-only queue, human
   review required, compliance gate (UNREVIEWED/CLEARED/BLOCKED) blocks
   any next-step ApprovalRequest until a named human clears sanctions/
   export-control review — no send/execute/outreach method exists in
   the module. Surfaced via nexus_status_brief.py's pending-opportunity
   count. This line was stale for 3 days (built the same week it was
   still listed here as "not yet built") — a reminder to check the
   actual file/git history before trusting this section, not just the
   prose.
   REMAINING GAP (not done): no real signal has ever been submitted to
   it — no opportunity_drafts.db exists anywhere in the repo, only
   test runs against tmp paths. submit() currently validates lane scope
   via fal_vertical.assert_lane_scope(), i.e. FAL-A/FAL-B only; it has
   not been checked against/generalized for other verticals (e.g. the
   real evidence-graded Hydrotester data in
   data/entry_map_baku_eastpipes_2026-08-21.json, which is a different
   vertical, currently paused per project priorities above). Next real
   step, if wanted: get one genuine FAL-A/FAL-B signal and run it
   through OpportunityQueue.submit() end-to-end — not fabricated test
   data standing in for a real signal.

6. [Reza] Get real sanctions/export-control legal advice for FAL-A/FAL-B --
   the compliance gate above only records a human decision, it doesn't
   determine legality itself.
7. [Not started] fal_trade_economics.py exists (landed cost, margin,
   breakeven, spec-adjusted price) but has never been run against a real
   quote -- needs real FX/freight/duty numbers before it means anything.

## EXPERT FOUNDRY ACTIVATION (2026-09-08)
- Expert Foundry v0.1 merged to main as a governed research-memory scaffold.
- Phase-0 steel-ingot preflight exists and passes focused tests; it is not the
  architecture's full acceptance proof.
- Current runtime state: READY_FOR_FACTORY_DATA, not production/process control.
- The preflight stores curated sources (not a claimed live search), gaps, a falsifiable hypothesis, hash chain
  and snapshot; it refuses to invent a recipe while plant inputs are missing.
- Next evidence required: one acceptable and one defective historical heat of the same
  grade/route, with chemistry, process timeline, equipment context and quality results.
- Governed CSV/JSON/XLSX ingestion is merged to main. Raw inputs are SHA-256 vaulted;
  normalized records remain unverified and bind back to the raw-file digest.
- Staff launcher: `scripts/expert_foundry_intake.ps1`; default is dry-run and `-Commit`
  is required for storage. No web UI or central production deployment exists yet.

## ROLLING MILL STUDY (2026-09-12, updated 2026-09-16)
- Initial equipment description received by voice transcription and preserved as eight
  `UNVERIFIED` claims; no units or meanings were inferred.
- Dedicated contract: `.nexus/expert_foundry/ROLLING_MILL_ENGINEERING_INTAKE.json`.
- Readiness gate: `rolling_mill_intake.py`. Current state is still
  `READY_FOR_ENGINEER_INTERVIEW`; calculations and operation changes remain blocked.
- Engineer questionnaire: `docs/expert_foundry/ROLLING_MILL_ENGINEER_QUESTIONNAIRE_FA.md`.
- **2026-09-16: engineer (Sanami) answered 8 of 34 questionnaire items via WhatsApp** +
  a handwritten ST1-ST4 stand sketch + a CAD drawing for ST1 (roll dia. 518mm) + an
  unlabeled ST1-ST4/P1-P10 number table (units not stated -- NOT treated as pass-schedule
  data). Evidence archived under `docs/expert_foundry/evidence/2026-09-16-engineer-answers/`;
  recorded as an `EXPERT_INTERVIEW`-sourced CLAIM in the Expert Foundry ledger
  (`claim-rolling-mill-engineer-answers-20260916`).
  - Resolved: billet 150x150mm square / 3150mm max length / St37 grade; target width
    300mm (separate from a 8-10-12-15-20-25mm thickness set, min 8 max 25); the
    800/125kW/1002 reading turned out to be TWO motors (ST1=1250kW/999rpm/420V/2300A AC
    w/ starting resistor, ST2=800kW only); the 15/20/25 figures are thickness options,
    not widths.
  - Still open / genuinely unresolved (not papered over): safety (guards/E-stop/LOTO)
    entirely unaddressed; no torque/force limits; no actual nameplate photos (numbers
    were typed, not photographed); no reheating temp, pass-schedule, or target
    standard; 4 of 8 original ambiguous claims remain unresolved -- notably barrel
    length was given as 1280mm (matches the CAD drawing) which does NOT match the
    previously-logged 1350mm claim, and the original "450" in "roll 450 to 480" is
    still unaccounted for (480 turned out to be ST2's diameter, not a range on one
    roll). Full per-stand detail (ST1-ST4 motor/gearbox/roll) lives in the intake
    JSON's `mill_stands_detail` key since the schema's flat fields only fit one stand.

## DEEP SEARCH / FAL-A LIVE RESEARCH (2026-09-17, new)

- Fixed a real cross-branch integrity gap found while doing this: this branch
  (feat/unified-system-governance-v0.1) never actually had fal_vertical.py in its
  own git history, even though opportunity_suggestion_engine.py (already committed
  here as 7e7c96f) hard-depends on it. It "worked" only because an untracked,
  uncommitted copy happened to sit in the working directory, content-identical to
  main's already-committed version. Fixed by committing that same file here too
  (commit e34c62b) -- a clean clone of this branch before that fix would have
  failed to import opportunity_suggestion_engine.py.
- First real (non-synthetic) discovery run for FAL-A (ferromanganese import,
  foreign SUPPLIER role): 7 candidate entities gathered via live public web search
  (Georgia/CIS, Turkey, Gulf directories/companies -- China search returned no
  in-corridor hits worth including) and run through the existing
  discovery_pipeline.py machinery (ingest_external_discoveries + process_discovery_batch),
  persisted under research_lab/. Driver: scripts/run_fal_a_discovery.py. Raw data:
  data/research/fal_a_ferromanganese_discoveries_2026-09-17.jsonl.
- Result: plausible_buyer_count=0, verified_buyer_count=0 -- correctly declined
  to promote any single-source, unclassified-category hit. This is the scoring
  working as designed, not a failure. Next real step to get a non-zero result:
  either find a second independent source per candidate entity, or manually
  classify each entity's category (steel_mill/trader/distributor/etc.) rather
  than leaving all seven as "unknown".
- Explicitly NOT done and not automatable: contacting any of these entities,
  creating an account anywhere, or any outreach. outreach_authorized stays
  hardcoded False in need_radar.py; nothing here reaches OpportunityQueue
  without further corroboration, and nothing in OpportunityQueue can reach a
  human-approved next step without a separate, explicit compliance_status=CLEARED
  review (see opportunity_suggestion_engine.py's compliance gate, and the
  project-priorities section above on Iran-related sourcing needing real legal
  advice before live outreach).

## ROLE SPLIT (still true)
- Claude Code: engineering executor (code/tests/branches)
- ChatGPT/NEXUS (via both a Drive/Notion-connected session AND a
  separate Codex clone — see environment warning above): orchestrator,
  business context, live connectors, authority recovery
- Claude Chat (this): independent reviewer — verifies claims against
  raw evidence when given file/link access, challenges both other
  AIs, never assumes access it doesn't have
- Reza: final approval on all protected actions, tie-breaker on any
  cross-AI disagreement, sole human-in-the-loop for compliance-
  sensitive decisions

## MAIN/FEAT MERGE (2026-09-14)
- feat/unified-system-governance-v0.1 merged into main as commit 5686e14
  (parents 98a1d44 on main, 4eb3b45 on feat). Confirms the environment
  warning above with a concrete case, not just a risk: both clones had
  independently rebuilt the SAME Expert Foundry rolling-mill package
  (21 overlapping files). 14 were byte-identical (CRLF-vs-LF noise from a
  file copy); the other 6 (rolling_mill_intake.py + its test,
  ROLLING_MILL_ENGINEERING_INTAKE.json, this file, and the two
  CLAUDE_ROLLING_MILL_*.md handoffs) had genuinely different content --
  main's version won all 6 because it carried the confirmed 2026-09-14
  dimensions (this file's own ROLLING MILL STUDY section is that content);
  feat's copies were a stale pre-2026-09-14-confirmation draft pulled from
  an earlier audit-ZIP reconciliation. fal_vertical.py -- a load-bearing
  dependency of the new FAL modules below -- existed only as an uncommitted
  working-tree file on neither branch and is now committed via this merge.
- New on main from this merge: opportunity_suggestion_engine.py,
  fal_trade_economics.py, nexus_status_brief.py, market_price_snapshot.py,
  rolling_mill_mechanics.py (retrospective hot-rolling geometry/force
  envelope, Sims-style, no material-property assumptions), plus this
  branch's earlier (pre-2026-09-14) governance-layer work (collaboration
  growth, continuous research, owner-decision runtime, portfolio watchdog,
  project control plane, self-improvement runtime, unified data
  environment, external account orchestrator, learning media pipeline) --
  none of that governance-layer work has been read/audited as part of this
  merge; it was carried through unchanged because it never conflicted.
- NOT pushed to origin yet -- pending Reza's go-ahead, since the remote is
  what the Codex/ChatGPT clone reads from next.
- Sandbox note for whichever AI touches this repo via a device-bridge-style
  sandboxed shell next: that environment could not unlink files under the
  mounted repo folder (git status/commit/merge all left stale
  index.lock/HEAD.lock/objects/*/tmp_obj_* debris behind, harmless but
  noisy -- `mv` the stale lock aside, don't try to `rm` it). A real
  worktree-based merge failed for the same reason; the fix used here was
  git plumbing (read-tree -m + commit-tree) with a scratch index file
  outside the mounted folder.

## MAIN/FEAT MERGE #2 (2026-09-19)
- Since the first merge (5686e14, above), main and feat/unified-system-governance-v0.1
  diverged again. Surveyed with `git merge-tree` against their merge-base (4eb3b45):
  of the files that differ, the huge majority (13 new modules/tests, including
  self_improvement_runtime.py and unified_data_environment.py) are BYTE-IDENTICAL on
  both sides -- another instance of the two clones independently rebuilding the same
  content from a shared source, not a real conflict. Checked by content hash before
  trusting the file list, per the CRLF-lesson above.
- 2 of 3 real conflicts resolved by evidence recency (not by which clone produced
  them), same principle as the first merge; the 3rd is FLAGGED, not resolved:
  1. `.nexus/expert_foundry/ROLLING_MILL_ENGINEERING_INTAKE.json`, `rolling_mill_intake.py`,
     `evals/test_rolling_mill_intake.py`, and this file's ROLLING MILL STUDY section --
     RESOLVED by Reza on 2026-09-19 (explicit, not inferred): the mill's existing
     physical-capability study and the 220x220mm question are the same topic, not two
     separate ones. main's schema wins (220x220x3000mm billet, width_options_mm
     [300,400,600], thickness_range_mm, reported_diameter_around / barrel_length,
     dated "conversation:2026-09-14"). feat's 150x150mm / ST1-ST4 draft (from the
     2026-09-16 engineer (Sanami) WhatsApp answers) is superseded for this contract --
     not deleted from git history, just no longer the live schema. Applied in a
     follow-up commit on top of the pushed merge (13c7760) rather than amending it,
     so the record of the original open question and how it got closed stays intact.
     This is the kind of factual/schema call this project's evidence-discipline rules
     say Claude must never make silently -- it was made by Reza, on request, which is
     exactly the required human tie-breaker.
  2. `.nexus/runtime/expert_foundry/events.jsonl` (append-only, hash-chained ledger)
     -- feat's copy is a strict superset (one additional CORROBORATED claim record
     for the same 2026-09-16 engineer answers, appended after 3 records both sides
     already shared identically). Took feat's full file.
  3. This file (CURRENT_STATE.md) -- manually synthesized rather than picking one
     side: kept feat's corrected Track E (Opportunity Suggestion Engine) item 5 and
     its DEEP SEARCH / FAL-A LIVE RESEARCH and ROLLING MILL STUDY sections (newer,
     more accurate), added main's items 6-7 (real, non-conflicting facts feat's
     numbered list didn't have), and kept main's MAIN/FEAT MERGE (2026-09-14)
     section immediately above this one as unmodified history.
- Also new on feat since the first merge (not previously on main, no conflict,
  carried through as-is): FAL-B (ferrosilicon export) live discovery + a second,
  genuinely multi-provider (claude-web-search-manual + exa-agent-run) pass on both
  FAL-A and FAL-B; a fix to discovery_pipeline.group_duplicates() so a shared
  listing/directory-page URL no longer forces distinct named companies into one
  false "ambiguous" entity (opt-in `source_is_multi_entity_listing` flag, default
  False, existing fail-closed behavior for an unflagged URL is unchanged and still
  tested); a reconciled `docs/authority/AUTHORITY_STATUS.md` promoting Master
  Context v1.4 + Source Registry v1.1 as canonical (the newer v1.6-v2.1 draft
  lineage stays unpromoted -- still internally self-contradictory); a factual,
  sourced EO 13871 / Iran-sanctions brief and a 3-tier action-risk policy Reza
  dictated on 2026-09-17 (`docs/compliance/`) governing which actions run
  automatically vs. need his approval vs. stop outright for this project going
  forward; new subagents (branch-integrity-auditor, fal-discovery-batch-runner,
  rolling-mill-evidence-reviewer).
- Full evals/ suite run against feat's tip (af20da5) before this merge: 1 unrelated
  pre-existing failure (test_rolling_mill_intake.py::test_current_voice_claims_fail_closed,
  no import dependency on anything touched here) -- left untouched, out of scope.
- Merge commit 13c7760 (parents bb2acae + origin/main's 258be46) built via git
  plumbing, verified (904 passed, 1 known pre-existing unrelated failure), and pushed
  to origin main by Reza on 2026-09-19. The rolling-mill flag above was resolved and
  applied in a follow-up commit on the same day, also pushed to main.
