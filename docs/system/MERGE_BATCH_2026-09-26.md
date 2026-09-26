# Merge Batch — 2026-09-26

Base: local `integ/2026-09-26` (main + PR #99/#100), commit `68f8d89`.
Batch branch: `chore/merge-candidates-batch-v0.1`, worktree `(scratch path)`.
Final SHA: `c6bf99ca008e56c73abc8ba6ac4cfe5b1fd7ed47`.

Scope: the 9 MERGE-CANDIDATE branches from `docs/system/BRANCH_TRIAGE_2026-09-24.md`,
recomputed from scratch against current `integ/2026-09-26` (not taken on the
triage doc's word). `feat/steel-recovery-v0.1` skipped per instructions
(already merged via PR #100 — confirmed with
`git merge-base --is-ancestor origin/feat/steel-recovery-v0.1 integ/2026-09-26`).

## Verdicts

### INCLUDED (3)

**`hardening/supplier-collision-gate-v0-1`** — commit `b08c1c6`
Tip SHA `8b2a4b6e6316f73dc9c53a62469338525fc97fcd`.
Recomputing against merge-base showed the branch *also* touching
`src/nexus_verticals/supplier_identity.py` (89 insertions / 13 deletions) —
contradicting the triage's "zero deletions, single file" claim. Investigated
further: that file is **byte-identical** between the branch tip and current
`integ/2026-09-26` (integ independently carries the same hardening via its
own commit `909f5ef`, "Harden supplier collision gate v0.1"). So the only
truly unique file is `tests/test_supplier_identity.py` (238 lines, genuinely
absent from integ). Brought in only that file. Test delta: **+15 tests**,
15/15 pass standalone and as part of the full suite.

**`feature/trace-envelope-v0-1`** — commit `e6635c3`
Tip SHA `963391b55d05c20f4865f45d9cc475f3b0bd238d`.
Pure addition: new `src/nexus_observability` package (`TraceEvent`,
`TraceValidationResult`, `validate_trace`) + test + doc. Despite event-type
names like `approval_requested`/`external_action_requested`, it is a passive,
metadata-only audit-log schema — no network, no credential handling, no
execution — and it actively blocklists secret/credential-shaped attribute
keys. `git grep` for `TraceEvent`/`validate_trace`/`TraceValidationResult` on
integ: no matches, no duplicate. Test delta: **+10 tests**, 10/10 pass.

**`security/policy-threat-model-v0-1`** — commit `c6bf99c`
Tip SHA `61380851437cf7e65ddb7b6239f5b887b1958b22`.
Pure documentation: `SECURITY.md` + `docs/security/threat-model-v0-1.md`.
Neither path exists on integ today. Zero conflict, zero code risk.

### OWNER-REVIEW (5)

**`experiment/productization-contract-v0-1`** (`src/nexus_verticals/productization.py` + doc + test, pure addition, no file overlap). Its entire purpose is defining approval/permission-gating semantics for consequential actions (`CONSEQUENTIAL_ACTIONS = {external_send, contract, purchase_order, payment, signature, permission_change, production_deploy, protected_merge, public_publish, destructive_database_change}`) and enforcing that such actions must be `human_gated`. Squarely in the "touches approval/permissions/external actions" risk category the instructions call out — flagging for owner review even though it is structurally a clean addition with no execution/network/credential code.

**`feat/external-access-broker-v0-1`** — not a pure addition either (modifies `security.py`, `ui/login.html`, `evals/test_auth_session.py`). Adds `external_access_broker.py`, `account_bootstrap.py`, `capability_mesh.py`, `provider_resolution.py` — external-account/credential bootstrap and provider-resolution machinery. Clear "external actions / credentials" risk.

**`feat/posthog-observability-v0-1`** — `posthog_adapter.py` makes real outbound HTTP POST calls (`urllib.request.urlopen`) to a third-party host, carrying an API key read from the environment. Clear "network / credentials" risk despite being a structurally pure addition.

**`feat/railway-control-layer-v0-1`** — `railway_control.py` is a live GraphQL client (`https://backboard.railway.com/graphql/v2`) authenticated with `RAILWAY_PROJECT_TOKEN`/`RAILWAY_TOKEN`. Clear "network / credentials / external actions" risk (the code is deliberately read-only-by-default, but it is still a live external-service client — an owner call, not an automated-batch call).

**`security/exact-send-core-v0-1`** — `src/nexus_control_plane/exact_send.py` defines `ExactSendApproval`/`ExactSendDecision` and content-bound action IDs explicitly for "exactly one external send," with a `requires_human_approval` field. Directly in the "approval / external actions" risk category by design intent, not just incidental naming.

### REJECTED

None — all recomputed branches were either included or routed to owner review; none failed the "pure addition / no deletions / no file main has changed" structural check outright (the one apparent case, `hardening/supplier-collision-gate-v0-1`, turned out to be a false alarm — see above).

### FAILED

None — every commit that was made passed its own tests and the full suite; no reverts were needed.

## Final verification (fresh worktree of `c6bf99c`)

| Check | Baseline (`integ/2026-09-26`, fresh worktree) | Final batch branch |
|---|---|---|
| `python -m compileall -q .` | clean | clean |
| `python -m unittest discover -s evals` | 682 passed | 682 passed |
| `python -m pytest -q -p no:cacheprovider evals` | 1101 passed, 11 subtests | 1101 passed, 11 subtests |
| `PYTHONPATH=src:. python -m pytest -q -p no:cacheprovider tests` | 501 passed | **526 passed (+25)** |
| `python -m nexus_checks docs/procurement --exclude '*_2026-09-22.md'` | 19 files, 0 errors, 0 warnings | 19 files, 0 errors, 0 warnings |

The +25 test delta is exactly the supplier-collision-gate (+15) and
trace-envelope (+10) test files added; evals and nexus_checks are unaffected
since none of the included branches touch those trees.

## Commits on `chore/merge-candidates-batch-v0.1`

1. `b08c1c6` — supplier collision gate tests (hardening/supplier-collision-gate-v0-1 @ 8b2a4b6)
2. `e6635c3` — nexus_observability trace-envelope package (feature/trace-envelope-v0-1 @ 963391b)
3. `c6bf99c` — SECURITY.md + threat model doc (security/policy-threat-model-v0-1 @ 6138085)
