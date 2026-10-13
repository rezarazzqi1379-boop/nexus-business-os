# CHANGELOG — Steel Kernel

## v0.1 — ۲۰۲۶-۰۹-۲۱
- ممیزی ساختار موجود؛ Gap Analysis؛ تصمیم «اشاره کن، کپی نکن»
- `steel_kernel.py`: scope، freshness/TTL، routing، token class، ingestion، preflight
- هشت replay test بند ۱۴
- `CONTEXT_ROUTER` · `FRESHNESS_POLICY` · `TOKEN_BUDGET_POLICY` · `KERNEL` · `CHECKPOINT` · `GAP_ANALYSIS`
- **ساخته نشد:** رجیسترهای jsonl تکراری، knowledge map، lessons register جدا، skill/agent registry — دلیل هرکدام در Gap Analysis
- **وضعیت:** IMPLEMENTED · TESTED · COMMITTED. نه MERGED، نه ACTIVE، نه SCHEDULED.

## 2026-09-22 - project state reconciled with the slab line
- CHECKPOINT.md carried the billet-line state as current while the slab line had
  been the active project since 2026-09-21. A superseded-warning banner and the
  live slab basis are now recorded.
- docs/system/SYSTEM_AUDIT_2026-09-22.md: measured token accounting for this
  session (41.3M effective), connector audit (2 of ~250 MCP tools used),
  agent/skill/command audit (31 skills, 148 commands, 18 agents unused), and
  the cache-invalidation finding: 39% of cache-write cost followed MCP
  connect/disconnect events for connectors that were never called.

## 2026-09-26 - state-freshness check; CURRENT_STATE.md and CHECKPOINT.md brought current
- New `nexus_checks/state_freshness.py` (stdlib-only): a governed state/kernel file is STALE
  when a path it governs has git commits newer than the state file's own last commit by more
  than a configured tolerance (default 2 days); also flags `` `backtick path` `` references in
  those files that don't exist in the tree. Config: `.nexus/state/STATE_GOVERNANCE.json` (JSON,
  not YAML - this repo has no YAML parser dependency anywhere; `steel_kernel.py` already treats
  its own `.yaml` files as a human-readable mirror of hardcoded Python values, not something
  machine-parsed, and this check follows that same pattern). CLI: `python -m nexus_checks
  --state --repo .`. Tests: `evals/test_nexus_checks_state.py` (11 tests: fresh passes, stale
  fails, tolerance absorbs a small gap, re-freshening clears it, missing governed path warns
  without erroring, broken reference fails, a real external machine path / shell command /
  dotted-function-name are correctly not flagged as broken repo pointers).
- Ran it once and fixed what it found: `.nexus/state/CURRENT_STATE.md` was ~7 days stale
  against `docs/procurement/`, `docs/expert_foundry/`, `docs/system/`, `.nexus/steel/` and
  `AGENTS.md` (rewritten for 2026-09-26); this file's own `CHECKPOINT.md` was ~4 days stale
  (new dated entry appended there); `.nexus/steel/GAP_ANALYSIS.md` pointed at `registers/*.md`
  instead of `.nexus/expert_foundry/registers/*.md` (prefix fixed); `CURRENT_STATE.md` and the
  steel control doc each had one path reference to a file that was never actually tracked in
  this repo (an unmerged branch's source file, and an untracked local helper script) - both
  reworded to say so instead of reading as live repo pointers.
- Side finding (not from the new tool - found by reading `AUTHORITY_STATUS.md` directly while
  rewriting `CURRENT_STATE.md`): the authority-status contradiction `CHECKPOINT.md`'s own header
  had flagged as unresolved was actually just staleness - `AUTHORITY_STATUS.md` reconciled to
  RECONCILED (PARTIAL) on 2026-09-17, two days before `CURRENT_STATE.md`'s 2026-09-19 revision,
  which never picked up the change. Corrected in both files.
- CI: recommended addition to `.github/workflows/test.yml` is `python -m nexus_checks --state
  --repo .` alongside the existing `nexus_checks docs/procurement` line; not edited here (out of
  this change's scope, and another agent may be touching CI in parallel).
