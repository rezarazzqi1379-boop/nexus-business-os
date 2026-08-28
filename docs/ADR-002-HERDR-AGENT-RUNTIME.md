# ADR-002: Herdr as an experimental NEXUS agent runtime

Date: 2026-08-28  
Status: Proposed / branch-only

## Decision

Adopt Herdr as an optional local or controlled-host execution substrate for
coding agents. Herdr may manage terminal topology, agent lifecycle state,
session continuity and result collection. It is not a NEXUS decision authority
and cannot receive, create, consume or satisfy a NEXUS approval.

The first integration is plan-only. It converts a validated
`nexus.runner.v1` read packet into an explicit four-step Herdr command plan:
create workspace, start a supported agent, prompt and wait, then read the
result. It does not execute commands.

## Evidence snapshot

Retrieved 2026-08-28 from the official `herdrdev/herdr` repository.

- FACT: current stable release is v0.8.2.
- FACT: the repository is Apache-2.0 licensed and implemented primarily in Rust.
- FACT: Herdr documents Codex and Claude Code detection and native session
  restore.
- FACT: native Windows support is generally available in v0.8.2.
- FACT: Herdr plugins on Windows remain preview.
- CLAIM: Herdr describes itself as an always-running background runtime. NEXUS
  treats that as an upstream product claim until reproduced in our environment.
- UNKNOWN: live compatibility with Reza's Windows machine, installed agents,
  endpoint protection and NEXUS repository has not yet been measured.

## Trust boundary

- Only `CapabilityRisk.READ` packets are accepted during the pilot.
- Secrets and approval identifiers are rejected before planning.
- Workspace paths remain beneath an explicit absolute NEXUS root.
- Pane IDs are captured from Herdr output and are never predicted.
- Herdr lifecycle states are observations, not proof that work is correct.
- `blocked`, `unknown` and detection fallback never authorize input.
- External sends, merges, deployments, payments, permission changes and
  production writes remain behind the existing exact-scope NEXUS gate.
- Pane history stays disabled initially because terminal output can contain
  secrets.
- Automatic remote detection-manifest updates should remain disabled during the
  first reproducibility test; update provenance is reviewed separately.

## Deployment boundary

Do not install Herdr into the Railway web container. The canonical Railway
service remains the durable NEXUS control plane. Herdr belongs on the
owner-managed Windows workstation or a later controlled Linux execution host
where coding-agent processes actually run.

## Admission tests

### Stage 0 — plan-only (implemented)

- valid read packet produces a deterministic plan;
- write, exec and external capabilities fail closed;
- secret-bearing inputs fail closed;
- approval delegation fails closed;
- workspace escape fails closed;
- agent kind and timeout are bounded.

### Stage 1 — supervised local pilot (not authorized yet)

- install the pinned v0.8.2 Windows release after checksum verification;
- create an isolated test workspace with no credentials;
- start one Codex agent and one inert shell pane;
- reproduce `working`, `blocked`, `idle/done` transitions;
- detach and reattach without losing the live process;
- confirm no cross-project path access;
- uninstall cleanly and verify rollback.

### Stage 2 — controlled execution (future)

Promote beyond experimental only after the local pilot passes, provenance and
logs are reviewed, a kill switch exists, and every external capability remains
approval-gated.

## Rollback

The integration is additive. Remove `herdr_adapter.py`, the `HERDR` runner
manifest and its tests. No database migration or production configuration is
introduced by this decision.
