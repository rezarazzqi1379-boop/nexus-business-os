# NEXUS cloud-to-Windows proof ledger

Status: DRAFT, synthetic-only. No persistent service or vendor CRM installed.

## Verified cloud evidence
- PR #105 head before this document: a1cbbd7f127a0d3f25c53ebc951c2cc289223fdf
- GitHub Actions run 38377583089: SUCCESS.
- Its job `test` passed checkout, Python setup, compileall, unittest, pytest evals, nexus checks and pytest regressions.
- This is **not** proof that the separate `nexus-synthetic-health.yml` workflow has executed.

## Acceptance gates before calling it permanent
1. A workflow run of the exact synthetic-health workflow succeeds on the intended active branch; record run ID, ref and SHA.
2. A second scheduled run succeeds without manual intervention; record schedule trigger and timestamp.
3. Failure injection demonstrates a nonzero exit and visible failed check.
4. Restart, stop and rollback tested on the chosen host.
5. For Windows, verify local repository origin spelling, dirty worktree inventory, permissions and isolated runtime before installation.
6. Only then consider attaching external adapters or real data with separate exact approval.

## Evidence classifications
- FACT: main test workflow passed at the SHA and run above.
- UNKNOWN: whether synthetic-health schedule is enabled, dispatched or executed.
- UNKNOWN: local Windows install, service restart and rollback.
- DESIGN: health gate is synthetic-only and must never claim live CRM connectivity.

## Next safe actions
- Keep Draft PR and existing protected branches unchanged.
- Inspect GitHub workflow-specific runs when permissions permit.
- Prepare a single isolated Windows pilot only after live machine access.
