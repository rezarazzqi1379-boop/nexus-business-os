# OpenWorker and MCP Decision Record

Date: 2026-08-21

## Decision

OpenWorker is registered as an experimental, disabled-by-default local runner. It is not the
NEXUS orchestrator, approval authority, memory system, or secret store. NEXUS may later export
read-only `nexus.runner.v1` work packets to it after a controlled Windows pilot.

## Evidence classification

- FACT: the public repository is MIT licensed and describes macOS Apple Silicon and Windows
  10/11 x64 packages, local agent execution, 25+ connectors, MCP support, and approval prompts.
- FACT: the repository describes the Windows package as not code-signed.
- FACT: the main branch currently declares `xlsx` version `^0.18.5` in the GUI.
- CLAIM: local-first privacy and complete gating are project claims until independently tested
  against the packaged Windows binary and real connectors.
- UNKNOWN: exact latest installer hash, update-channel integrity, live Gmail/HubSpot scopes,
  and compatibility with NEXUS approval fingerprints.

## Gate before installation

1. Windows release must be code-signed and publisher identity must be verifiable.
2. The spreadsheet-preview dependency finding must be closed or mitigated and verified.
3. Installer SHA-256 must be captured from an official release artifact.
4. Pilot in a fresh Windows account or VM with a disposable folder and no production secrets.
5. Connect no Gmail, HubSpot, Notion, GitHub or Calendar account during the first smoke test.
6. Test only local read access, stop/kill behavior, transcript completeness and secret redaction.
7. Add connectors one at a time with minimum read-only scopes and record effective permissions.

## MCP baseline

Only six candidates are relevant to the current MVP: GitHub, Gmail, Notion, HubSpot,
Filesystem and Playwright. All remain disabled in code. Activation is one workflow at a time,
read-only first, with provenance and permission review. The 50-server guide is a discovery
catalog, not an installation plan; installing all servers would enlarge attack surface and
context cost without advancing a measured NEXUS workflow.

## Prompt upgrade adopted

The useful pattern from the 15-prompt guide is incorporated as a contract: inspect the real
repository, state exact scope and non-goals, define acceptance criteria, preserve unknowns,
run tests, and stop at sensitive boundaries. Generic persona language and tool-specific
`CLAUDE.md` dependence are not adopted; NEXUS keeps provider-neutral project instructions.
