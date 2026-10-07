# NEXUS Cross-Session Continuity Contract v1

Status: IMPLEMENTED — pending CI at creation.

## Purpose
Make project continuation independent of any single chat transcript. Chat memory is continuity aid, never authority.

## Mandatory session start
1. Recover latest Source Registry.
2. Recover the canonical project master selected by the registry.
3. Read the latest project checkpoint.
4. Refresh repository HEAD and live CI.
5. Read back evidence referenced by the checkpoint when consequential.
6. Resolve contradictions/supersession.
7. Resume from the recorded blocker and next safe action.

## Mandatory session end
Record project_id, registry/master refs, repo HEAD, live CI, stage, maturity, evidence refs, blockers, next safe action, and whether the next action is protected.

## Portability rule
Any chat, agent, desktop/cloud environment or external platform may continue NEXUS only when it can read the canonical registry/master/checkpoint and refresh dynamic evidence. If it cannot, state is UNKNOWN; it must not infer authority from a copied prompt or stale chat summary.

## Permanent invariants
- Never transfer evidence/specifications/decisions between project IDs.
- RED CI stops capability expansion.
- Chat memory cannot promote maturity.
- Protected actions remain protected after handoff/session change.
- Missing evidence is not silently reconstructed.
- Every consequential continuation produces a new versioned checkpoint or explicitly records no state change.

## Current checkpoint at creation
PROJECT=NEXUS-BUSINESS-OS
REGISTRY=NEXUS_Source_Registry_v1.8_2026-09-01
MASTER=NEXUS_Master_Context_v2.1_2026-09-01
REPO_BRANCH=nexus/reconcile-v11-on-103-2026-10-07
LAST_TESTED_HEAD=f9f5d7883ca54c9480e4d7c6f3daca765bc2f4f0
LIVE_CI=GREEN #1229
STAGE=SOURCE_ROI / GROWTH_DISCOVERY
MATURITY=Pre-RFQ + dual-time evidence TESTED
BLOCKER=parallel research fabric not yet implemented/tested
NEXT_SAFE_ACTION=implement and test parallel research routing with dedup, overlap measurement, failover and cost/evidence accounting
PROTECTED_ACTION=false
