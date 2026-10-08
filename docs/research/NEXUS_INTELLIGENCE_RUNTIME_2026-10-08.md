# NEXUS Intelligence runtime v1 — persistent local sandbox

Date: 2026-10-08. Scope: SANDBOX/proof and SANDBOX/technology-proof.
Owner authorized installation and persistent activation in this chat.
Installed: dlt 1.31.0 plus 38 dependencies in .venv-intelligence only.
Platform lock: Windows x64 / Python 3.14; not a Linux CI installation lock.
config/intelligence-runtime.lock.txt pins versions and PyPI archive SHA256 hashes.
Installation used --require-hashes; pip check passed. Every probe verifies installed
versions against the lock before work. Archive hashes prove the install inputs,
not continuous attestation of installed files. No automatic upgrade is enabled.

## Security and reuse

Core license Apache-2.0, verified from official repository/PyPI. Commercial Hub
is not installed. OSV querybatch returned no known advisories for all 39 selected
versions at the observation time in data/research/intelligence-dependency-review.json.
This is a bounded database query, not proof of vulnerability absence. Upstream
security policy remains a review gap. Telemetry is disabled before importing dlt.
No new credentials, paid account, database server or agent framework was added.

## Actual acceptance evidence

tools/probe_intelligence_runtime.py uses a local filesystem dlt destination.
Four independent pipeline constructions exercise persistent cursor recovery:
first record -> 1 emitted; repeated record -> 0; changed cursor -> 1; other project
-> 1 in a different scope. Cross-project batch, missing lineage and automatic FACT
promotion each raise before state creation. See intelligence-runtime-proof.json.

tools/probe_intelligence_source.py reads one fixed public PyPI version endpoint,
max 2 MB and 20 second timeout. Observed response: 22,426 bytes. First run emitted
one row; repeat after process restart emitted zero. Hash and observation time
remain explicit. Metadata license declaration is a CLAIM/HYPOTHESIS graph link.
The existing UnifiedDataHub records each observation with an immutable local
snapshot; repeated reads do not overwrite an earlier observation's identity.
No live commercial source, procurement signal, opportunity or sales result is proven.

Measurements are normalizer row counts, not pre-filter callbacks. Initial callback
measurement was wrong and corrected. First repeat exposed a hub identity collision;
fixed with unique observation IDs and immutable snapshot references. These correction
trajectories are not represented as clean learning successes.

## Persistent operation

Existing heartbeat nexus-daily-control-plane was updated, not duplicated. Its
original daily 09:00 schedule, target chat and failed-runs-only policy were retained.
Saved status ACTIVE is confirmed by the app; a future scheduler execution is not
yet observed. Desktop/scheduler availability is required; no 24/7 or global account
activation is claimed. Instructions stay quiet for unchanged/non-actionable state.
Daily extension uses existing control plane/hub and this checkout. It may not
automatically switch branches, install/upgrade packages, invoke paid models, promote
authority, publish or alter other project data. Query cap 3, evidence allocation 3500,
working reserve 5500, output 2000; two low-yield searches stop expansion.

Run locally from repository root:

```powershell
$env:PYTHONUTF8='1'
./.venv-intelligence/Scripts/python.exe tools/probe_intelligence_runtime.py
# One public read, only after confirming the task still requires freshness:
./.venv-intelligence/Scripts/python.exe tools/probe_intelligence_source.py
./.venv-intelligence/Scripts/python.exe -m pip check
```

## Unknowns and rollback

Registry v1.8/Master v2.1 binaries remain missing after bounded Drive searches.
Canonical tuple promotion conflict is preserved. No source-specific commercial
facts are adopted. Cheap/strong model selection remains a tested policy, not an
authenticated active inference route. Provider/session token cost is UNKNOWN.
Only this local checkout has the installation; other chats must read this guide
and independently verify their checkout/runtime. CI on the new commit is pending
remote publication approval. Base PR #105 had exact-head successful CI.

Rollback: pause the existing heartbeat via automation_update, revert this local
runtime commit, retain hub observations as historical evidence and preserve source
stores. Removing the isolated environment is a separate local cleanup action;
existing environments and business project files were not modified.
