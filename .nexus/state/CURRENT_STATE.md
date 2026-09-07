# NEXUS CURRENT STATE
Last updated: 2026-09-07 by Claude Chat (via Reza)
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
5. [Not started] Opportunity Suggestion Engine (Track E) — designed,
   not yet built. Draft-only, never auto-sends, human approval queue.

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
