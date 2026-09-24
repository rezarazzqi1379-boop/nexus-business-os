# NEXUS Business OS — Claude session kernel

Loaded automatically at the start of every Claude Code session in this repo. It is
short on purpose: it routes to the governing documents instead of copying them.
The previous ruflo-generated file is preserved at
`docs/system/CLAUDE_md_ruflo_boilerplate_2026-09-14.md` (ruflo plugins were disabled
by the owner on 2026-09-22).

## 1. Governing contract

@AGENTS.md

`AGENTS.md` is the NEXUS operating contract and wins over anything below. Reuse the
existing modules it names (supervisor, autonomy store, scheduler, agent catalog, MCP
broker, research lab, deep-search fabric, `project_control_plane`, `continuous_research`,
`self_improvement_runtime`, `src/nexus_core/adoption_gate.py`,
`src/nexus_brain/resource_router.py`). **Do not build a parallel control plane.** Before
creating any register, agent, policy or module, search the repo for an existing one
(`.nexus/steel/GAP_ANALYSIS.md` is the worked example: most "missing" registers already
existed under another name).

## 2. Session boot (cheap first)

1. Identify the project. Steel rolling line: read `.nexus/steel/KERNEL.md` and
   `.nexus/steel/CHECKPOINT.md`, then `docs/expert_foundry/PROJECT_CONTROL_PRJ-STEEL-ROLLING-LINE-01.md`.
   Procurement: `docs/procurement/README.md`. Repo-wide state: `.nexus/state/CURRENT_STATE.md`.
2. Authority: `docs/authority/AUTHORITY_STATUS.md`. A newer file name is not authority;
   match Source ID, status, effective date and supersession rule.
3. Load only what the route needs (`.nexus/steel/CONTEXT_ROUTER.yaml`,
   `.nexus/steel/TOKEN_BUDGET_POLICY.yaml`). Never reload whole chat histories.
4. Then do the work. Do not ask "what next?" when the objective follows from the state
   files; stop only at an approval gate (AGENTS.md §7, §Owner-delegated) or a real blocker.

## 3. Truth and maturity (two vocabularies, never mixed)

- Evidence: FACT · MEASUREMENT · CLAIM · ESTIMATE · ASSUMPTION · HYPOTHESIS · UNKNOWN.
  Procurement prices additionally: TRANSACTION · FORMAL QUOTE · ADVERTISED · AUCTION START.
- Maturity: DESIGNED · IMPLEMENTED · TESTED · COMMITTED · PUSHED · MERGED · DEPLOYED ·
  ACTIVE · PRODUCTION-VERIFIED.
- Contradictory readings are kept side by side and both computed; never silently pick the
  newer one. Every "incompatible / infeasible" verdict must print the basis it assumed
  (FM-009: "1:25 is incompatible" was true only at 3 m/s and a 700 rpm motor ceiling).
- Compare new work against the project's engineering basis, not only against your own
  earlier outputs (FM-010).

## 4. Token economy — concrete levers, not intentions

- Subagents inherit the parent model unless told otherwise. Set the Agent tool `model`:
  `haiku` for classification/extraction/format work, `sonnet` for web search and supplier
  or market research, the default (strongest) model only for architecture, contradiction
  resolution, novel engineering and independent red-team review. Measured: research
  agents cost ~70k–230k tokens per run; the independent reviewer (~63k) was the cheapest
  and highest-yield role (`.nexus/steel/TOKEN_BUDGET_POLICY.yaml`).
- Numbers are computed with code, never with long prose reasoning.
- Parallelise independent research in one message; stop searching when marginal yield is low.
- Unused MCP connectors cost tokens through cache invalidation (`docs/system/SYSTEM_AUDIT_2026-09-22.md`,
  on branch `feat/steel-recovery-v0.1`, not yet on main).

## 5. Failure memory is executable

Register: `.nexus/expert_foundry/registers/ENGINEERING_FAILURE_MEMORY.md` (FM-001…).
A failure that can recur becomes a test or a check, not only a paragraph.

Run before releasing any vendor-facing document, and after any batch of document edits:

```
python -m nexus_checks docs/procurement --repo . --exclude '*_2026-09-22.md'   # drafts (v4 archives excluded)
python -m nexus_checks --release <outgoing copies>          # release gate (banner must be gone)
pytest -q evals/test_nexus_checks.py
```

Checks: vendor-facing hygiene (FM-005), EN/ZH structural parity (FM-006), superseded
values in documents (FM-007; complements `steel_action_gates.detect_obsolete_values`
which guards the intake JSON), git health (FM-008).

## 6. Git on the bridged Windows mount

- Read-only git: always `git --no-optional-locks …` (plain `git status` leaves an
  unremovable `index.lock` that blocks the owner's own git).
- Commits: plumbing with a scratch `GIT_INDEX_FILE` (skill `device-git-plumbing-workflow`).
  If the target branch is checked out, **resync `.git/index` to the new HEAD afterwards**
  (FM-008: 18 finished files once sat staged for deletion).
- Never push, merge or delete remote branches; give the owner the PowerShell command.

## 7. Autonomy boundary (summary of AGENTS.md — AGENTS.md governs)

Autonomous: reading, search, analysis, calculation, code, tests, sandbox experiments,
drafts, reversible local edits, internal branches, proposing and prototyping system
improvements (promotion only through `adoption_gate`).
Exact-scope owner approval: any message to a vendor or third party, publication, payment,
orders, contracts, credentials/accounts/KYC, permission changes, merge/deploy, deleting
consequential data. Never entered by Claude: passwords, card or bank numbers, identity
documents, CAPTCHA.

## 8. End of a work cycle

Report only: what now works (with test evidence), discoveries, failures converted to
checks, open decisions for the owner, next safe action, exact approval required.
