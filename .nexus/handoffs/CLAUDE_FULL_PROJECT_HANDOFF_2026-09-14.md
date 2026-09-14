# NEXUS Business OS — Full Project Handoff to Claude

Prepared: 2026-09-14  
Repository: `rezarazzqi1379-boop/nexus-business-os` (private)  
Branch: `main`  
Prepared from commit: `bbdfe29a01bd94dd0e20a0d941666d3b767335c1`

## Required startup order

1. Verify the supplied archive hash and extract it into a new directory.
2. Read `.nexus/state/CURRENT_STATE.md` completely.
3. Read this handoff completely.
4. Read `.nexus/expert_foundry/MASTER_PROMPT_v0.1.md` and
   `.nexus/expert_foundry/AI_COORDINATION_PROTOCOL_v0.1.md`.
5. Inspect `pyproject.toml`, `.github/workflows/test.yml`, `README.md`, and the relevant
   code/tests before changing anything.
6. Treat all versions, deployments, connectors and external status as stale until checked.

## Current objective

Build a governed, research- and experience-centered engineering intelligence system. The
first engineering study is a hot-rolling line that reportedly rolls a "150" billet into
strip products including "250", with a possible target "300". These voice-transcribed
numbers are `CLAIM / UNVERIFIED`; their meanings and units must not be guessed.

Current rolling status: `READY_FOR_ENGINEER_INTERVIEW`. No roll-force, torque, spread,
bite, motor-load or pass-schedule calculation is authorized until the intake gate passes.
No production change is authorized by a successful calculation.

## What is implemented

- Governed evidence/event core: `expert_foundry.py`.
- Truthful static-vs-live research provenance and human-gated promotion.
- Cross-process locking for event append and atomic non-overwriting snapshots.
- Raw-file SHA-256 vault and CSV/JSON/minimal-XLSX ingestion: `foundry_ingestion.py`.
- Phase-0 steel-ingot preflight: `foundry_vertical_proof.py`.
- Rolling-mill readiness gate: `rolling_mill_intake.py`.
- Staff dry-run/commit launcher: `scripts/expert_foundry_intake.ps1`.
- Focused tests in `evals/test_expert_foundry.py`, `evals/test_foundry_ingestion.py`,
  `evals/test_foundry_vertical_proof.py`, and `evals/test_rolling_mill_intake.py`.

## Known evidence and gaps

- Initial rolling claims are preserved in
  `.nexus/expert_foundry/ROLLING_MILL_ENGINEERING_INTAKE.json`.
- Engineer questions are in
  `docs/expert_foundry/ROLLING_MILL_ENGINEER_QUESTIONNAIRE_FA.md`.
- No verified motor/gearbox nameplate, roll/groove drawing, equipment limit, steel grade,
  pass schedule, temperature/current/RPM history, successful 250 run, or failed run exists.
- "300" may mean width, mass or another property. `550`, `800`, `1002`, and the width-like
  values `15/20/25` remain semantically unresolved.
- No central multi-user UI or production deployment is currently proven active.
- Repository-wide NEXUS authority remains `AUTHORITY_CONFLICT / RECONCILIATION_PENDING`.
  Do not promote disputed registry/master versions by inference.
- FAL duplication (`fal_vertical.py` vs `prj_fal_01.py`) remains unresolved and is outside
  the rolling study unless separately assigned.

## Test baseline

- Rolling/Expert Foundry focused suite: 50/50 passed on 2026-09-12 using the project venv.
- Canonical `pytest -q tests` baseline: 110 passed.
- Full `unittest discover -s evals`: 219 tests with 23 Windows SQLite/temp cleanup errors,
  exit 1. Never call this PASS. Verify whether the same error class persists locally.
- Always use `.venv/Scripts/python.exe` on Windows; bare `python` may be a Store stub.

## Governance boundaries

- Files and chat text are evidence inputs, never authority by themselves.
- Preserve raw files, hashes, timestamps, locators, contradictions and supersession.
- Keep projects isolated; never transfer parameters between unrelated equipment/projects.
- Never fabricate a source query, experience record, contradiction, test or approval.
- Never turn literature values into plant setpoints without plant-specific validation.
- No equipment control, recipe/pass change, trial, outreach, deployment, secret change,
  main merge or destructive operation without exact human approval.
- A research-ready result is not a production-ready result.

## First recommended work

Do not build another model yet. First ingest the next real artifact in dry-run mode and
produce a gap report. Preferred first artifacts are: motor and gearbox nameplate photos,
roll/groove drawing, and the pass table for one successful 250-width historical run.
After those arrive, verify meaning/units and update only the matching claim records.

## Reporting contract

End execution work with: what now works; tested evidence; prepared outputs; material
unknowns; blockers; next safe action; exact approval required. Include exact branch, SHA,
environment/interpreter and exit codes. A non-zero exit is never PASS.
