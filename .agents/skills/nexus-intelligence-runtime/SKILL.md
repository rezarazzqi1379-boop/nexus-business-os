---
name: nexus-intelligence-runtime
description: Recover and verify the installed NEXUS incremental intelligence sandbox, its project-scoped extraction probes and daily heartbeat. Use for NEXUS Intelligence Platform installation, activation, restart checks or bounded evidence ingestion.
---

# NEXUS intelligence runtime

Locate the registered nexus-business-os checkout and read its current AGENTS.md,
.nexus/state/CURRENT_STATE.md and project operator skill before substantial work.
Installed checkout locator on the owner's Windows machine:
C:/Users/AvallPc/.codex/.chatgpt-projects/g-p-6a8492b077348191a541806c6ff52d75/nexus-business-os.
Treat this as a locator, not proof that this checkout or its branch is current.

Read docs/research/NEXUS_INTELLIGENCE_RUNTIME_2026-10-08.md for acceptance evidence,
commands, dependency lock, limits and rollback. Inspect git HEAD and local changes;
never silently switch branches or replace an existing environment.

The isolated interpreter is .venv-intelligence/Scripts/python.exe relative to the
verified checkout. Runtime probes check config/intelligence-runtime.lock.txt before
work. This lock targets Windows x64/Python 3.14. Do not apply it on another platform
or auto-upgrade dependencies. Missing installation is UNKNOWN until verified.

For an authorized local check, execute tools/probe_intelligence_runtime.py from the
checkout root. It tests persistent cursor recovery, duplicate suppression, changed
records and cross-project rejection without external data. For required public-source
freshness, tools/probe_intelligence_source.py performs one bounded PyPI metadata read
and records CLAIM evidence in the existing graph and UnifiedDataHub. Disable dlt
telemetry before import as these scripts do. No paid model integration is implied.

Existing heartbeat ID: nexus-daily-control-plane. Inspect its saved prompt/status
before changing it; preserve the existing target, schedule and notification settings.
Saved ACTIVE does not prove a completed scheduled run. Do not create a duplicate.

Canonical Registry/Master conflicts must remain unresolved until the actual source
binaries, hashes and version-bound decision are recovered. Sandbox package metadata
does not establish commercial demand, sales readiness or another project's facts.
Persist only distilled evidence references and actual measurements. Source files
and original business stores remain authoritative. Reuse existing control plane,
memory, hub and self-improvement/adoption gates; no parallel orchestration layer.

Report installed, tested, authenticated, scheduled and active separately. This skill
provides discovery and procedure, not authority to publish, send, pay, merge, deploy,
create credentials or change production. It does not modify the underlying model or
ChatGPT account settings. New sessions must independently verify their environment.
