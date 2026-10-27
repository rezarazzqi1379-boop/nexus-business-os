# NEXUS authority admission — fail-closed acceptance gate (DRAFT)

Status: **BLOCKED / NOT CANONICAL**. This branch derives from PR #114 head `4e30ef7251a26a3b845d375e90c120eaf2ab7ef0`. It is not an authority promotion or deployment.

## Independently confirmed defect
- `canonical_sources.parse_source` assigns `CANONICAL` to documents by title alone.
- `CanonicalStore.latest_for_source` selects the highest version regardless of an approval binding.
- `CanonicalStore.status` marks the highest Registry active; when the Registry does not declare the Master, it marks the highest Master active.
- Source Registry v1.8 sections 1/2/5 disagree on governing version (v1.8 versus v1.6); Master Context v2.1 sections 0/15 disagree on governing tuple (v2.1/v1.8 versus v1.9/v1.6). Their claimed 27 Aug approval predates 1 Sep effective date.

## Required implementation
1. Separate *ingested*, *claimed canonical*, and *approved active* states. Title and version are metadata, never approval.
2. Add an authority decision record with exact Registry/Master version, raw-byte SHA-256 for each, project scope, approving human/decision reference, timestamp, evidence location and supersession lineage. Missing or unverifiable evidence => BLOCK.
3. Validate internal authority declarations for contradictions and dates; quarantine disputed versions without deleting them.
4. Make `latest_for_source`, `status`, and `latest_for_project` fail closed for consequential active-source resolution when approved tuple is absent, ambiguous, or mismatched. Keep historical browsing possible via explicit untrusted APIs.
5. Verify the approved tuple across designated authority store, Drive/Notion, and repository, and bind preflight output to the exact digests.
6. Preserve all existing project/lane holds and all human-approval requirements for merge, deployment and outreach.

## Acceptance tests (not yet executed)
- v1.8/v2.1 contradiction fixture is rejected for activation.
- Highest-version-only candidate never becomes active.
- Forged document title cannot create authority.
- Missing, stale, mismatched or reused approval/digest => BLOCK.
- Historical v1.1/v1.4 can be inspected but is not automatically promoted.
- Cross-project authority and project isolation are enforced.
- Existing router, durability, and canonical-source regression suites pass.
- Fresh `nexus_chat_bootstrap.bootstrap_chat` produces verifiable preflight evidence and `ALLOW` before consequential action.
- Two-clone/shared-authoritative-database ownership regression remains green.

## Merge plan
Do **not** merge this draft or PR #114 until code patch, tests and explicit corrected authority tuple pass. Then merge guarded #114 (which contains #113), followed by #111 and #112, with expected head SHA and post-merge CI. No unreviewed production promotion.

Evidence: NEXUS Command Center comments 405b8b40-ace2-8146-bb19-001df9850a9e and 405b8b40-ace2-81ff-865b-001dfdb305be.
