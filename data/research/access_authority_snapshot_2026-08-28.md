# NEXUS Access & Authority Snapshot — 2026-08-28

Purpose: distinguish live connector capability from NEXUS authority. This snapshot is observational evidence, not a permanent grant of permission. Dynamic connector status must be refreshed before consequential use.

## Live-verified reads
- GitHub: connected to `rezarazzqi1379-boop/nexus-business-os`; repository reports admin/maintain/push/pull/triage permissions. Code search indexing is currently false. GitHub write tools exist and branch/file/PR writes have been exercised in the governed workflow, but merge/deploy remain exact-approval actions.
- Gmail: live label/read access verified. Inbox is large and noisy; procurement labels exist. Sending capability exists in the connector, but outbound messages remain exact-approval actions and must pass thread/duplicate/translation checks.
- Google Calendar: primary calendar is visible with owner role. Read and event-write actions are connector-capable; event changes remain governed writes.
- Google Drive: My Drive and NEXUS folders are readable. `NEXUS_Canonical_Sources` is stale relative to current project authority: it contains Master v1.3 / Registry v1.0 and 2026-08-23 project masters, while project governance currently uses newer canonical versions. Do not treat Drive-folder recency as authority until synchronized.
- Notion: current user identity resolved successfully; Notion read/search and page-write tools are available. No NEXUS authority is delegated to Notion itself.
- HubSpot: connector is live. Read/write are AVAILABLE for CONTACT, COMPANY, DEAL, TICKET, TASK, CALL, EMAIL, NOTE, LINE_ITEM, PRODUCT, MEETING_EVENT, MARKETING_EMAIL, LANDING_PAGE and MARKETING_EVENT. Several other types are read-only. TEAMS_AND_ROLES requires reauthorization. Portal reports `onboarded=false`; do not treat HubSpot as an active canonical CRM until onboarding and acceptance tests are complete.
- monday.com: connector is live; account is Pro trial with one active member and currently no relevant boards/favorites. It is therefore capability without demonstrated NEXUS workflow value yet.
- Vercel: live team and project access verified. Project `nexus-business-os` has a production deployment in READY state. This does not prove the Railway production service or NEXUS production behavior. Vercel deployment mutation remains exact-approval gated.
- Supabase: live project access verified; project status ACTIVE_HEALTHY. Security advisor reports many NEXUS tables with RLS enabled but no policy. This may intentionally deny client access, but it also means application data-path behavior must be tested before claiming the database is production-ready.

## Blocked / degraded
- Apollo.io: connector call returned HTTP 401 `Invalid access credentials` on 2026-08-28. Treat Apollo as BLOCKED until credentials/connection are refreshed. Do not substitute it silently with stale Apollo data.
- Railway: no direct Railway connector/shell is currently available in this environment. GitHub deployment status may provide evidence about Railway deploy completion, but it is not equivalent to console/runtime access.
- Some earlier chat-upload attachment handles have expired. If their exact binary content is needed again, the files must be re-uploaded or recovered from a connected canonical store.

## Delegated-operator rule
NEXUS may act as a high-autonomy operator for reversible internal work: recover state, search/read connected sources, research, compare, draft, code, create safe branches/draft PRs, run tests, detect contradictions, prepare decisions, and maintain evidence.

NEXUS does not become the user's legal/financial identity and connector capability does not grant independent authority. Sending messages, publishing, paying, signing, ordering, merging protected changes, deploying production, changing production access, modifying protected business data, or destructive operations require exact approval bound to the concrete target and payload/version.

## Highest-value access improvements
1. Synchronize current canonical Master/Registry/project masters into the governed Drive canonical store with hashes and supersession metadata.
2. Reauthorize HubSpot TEAMS_AND_ROLES only if CRM ownership/team workflows are actually needed; then run one read-only vertical acceptance test before any CRM writes.
3. Repair Apollo credentials only if a measured prospecting experiment justifies credit usage; Apollo remains an adapter, not authority.
4. Define and test Supabase RLS policies on a development branch before allowing browser/client access or calling the database production-ready.
5. Keep one runner-neutral Access Authority Registry so each connector's READ/WRITE/BLOCKED state is refreshed from live evidence instead of assumed from installation.
