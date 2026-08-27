# NEXUS OpenCode Shadow Adapter v0.1

Status: EXPERIMENTAL SHADOW CONTRACT — NOT A LIVE RUNNER, NOT PRODUCTION.

## Purpose

Integrate OpenCode as a bounded coding/review worker under existing NEXUS authority instead of creating a second agent/runtime/orchestration framework.

Sequence:

`NEXUS authority -> ResourceRouter/provider policy -> RunnerManifest -> sandbox WorkPacket -> code/read/test preparation -> NEXUS verification -> human merge/deploy gate`

## Authority boundary

OpenCode is never canonical authority. It cannot receive or consume a NEXUS approval, choose project specifications, widen provider/data policy, access secrets, authorize network use, perform external actions, merge, deploy, publish, purchase, sign, or mutate production.

## v0.1 capabilities

- READ: allowed in a scoped packet.
- WRITE_LOCAL: contractually allowed only under a `SANDBOX/...` workspace path.
- EXEC: contractually allowed only under a `SANDBOX/...` workspace path for local test/build preparation.
- EXTERNAL: forbidden.
- Network: forbidden by this adapter contract.
- Secret material: forbidden.

This contract does not install OpenCode and does not claim that a live OpenCode binary or provider route is verified. It creates the smallest testable interface needed before a live pilot.

## Promotion evidence required

A future live pilot must pin the exact OpenCode/runtime version and selected model/provider route, verify current provider terms and retention for the intended data class, run only sanitized/public tasks first, and compare against the current NEXUS coding path using the same repository snapshot and acceptance criteria.

Measure at minimum:
- task completion;
- test pass rate;
- regression count;
- authority/spec violations;
- cross-project contamination;
- security findings;
- human corrections;
- elapsed time;
- provider/model cost where applicable.

No benchmark or vendor claim can promote this runner by itself. Promotion requires NEXUS-local measured evidence plus explicit approval for any consequential integration.

## Rollback

Remove `OPENCODE_SHADOW` and the associated tests/docs. No production state or external system is changed by v0.1.
