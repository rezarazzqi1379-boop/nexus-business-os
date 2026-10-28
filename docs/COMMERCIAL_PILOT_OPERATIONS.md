# Read-only commercial intelligence pilot

This is an engineering experiment in `PRJ-NEXUS-SANDBOX`, lane
`industrial-tender-pilot`, based on main `5661d5dff60ebb46d0374516212a66cfde089969`.
PR116 and PR117 are merged; neither implementation is duplicated. Main regression
run 40558567902 passed after PR117. Existing free-runtime startup/authentication
and public GitHub research workflow is unchanged.

## Run and evidence

```powershell
$env:PYTHONPATH='src'
python -m pytest -q tests/test_commercial_pilot.py tests/test_router_runtime.py tests/test_public_research_agent.py tests/test_free_research.py
python nexus_commercial_pilot.py --output data/research/commercial-pilot-live --commit-sha <exact-40-character-HEAD>
```

Run on a clean implementation commit. `--commit-sha` labels the execution; the
caller must supply the actual revision. The Actions workflow obtains it from
the checked-out HEAD. Use a new/empty output directory; existing evidence is
never mixed with or overwritten by a later execution. Frozen transport injection exists only in Python tests;
it is explicitly labelled `FROZEN_TEST_FIXTURE`, never live evidence.

The separate `nexus-commercial-pilot.yml` executes on relevant PR changes and
manual dispatch. No recurring commercial schedule is enabled. It checks out
the PR head with no persisted credentials, installs pytest only, runs focused
acceptance, then a real-source task under a 60-second process deadline. Job bound:
six minutes. Exactly one attempted unauthenticated GET, no redirects, 5-second
socket timeout, 8-second acquisition deadline, 64 KiB maximum and three rows.
No model or paid API is called. Actions quota/compute cost is account-dependent
and UNKNOWN; zero paid-API cost is not a claim of unlimited free operation.

Artifacts: `summary.json`, `management-fa.md`, exact `public-source.json` bytes,
retained seven days. The response requests only allowlisted business fields;
strict schema/type/size/text/duplicate-JSON-key checks reject unexpected contact,
HTML, email or credential-like content before artifact creation. No queue DB,
environment, raw exceptions, contacts, credentials or container contents are
exported. Console output contains fixed metrics only. Archive approved public
evidence in the repository for longer-lived reproducibility.

## Reused architecture

`CommercialRuntime` extends `PublicResearchRuntime`: existing `AutonomyStore`,
lease owner/attempt/expiry fencing, atomic completion+checkpoint, retry handling,
reopen/replay protection and supervisor acceptance remain in effect. The
coordination plan selects an explicitly experimental read-only worker.
`deep_search_fabric.run_recursive_search` processes one query/one depth;
`discovery_pipeline.group_duplicates` preserves provenance and conflicting
versions; `research_lab.score_opportunity` supplies its existing baseline score.
No competing queue, scheduler, approval store, CRM or authority system is added.

Deduplication guarantees one execution per submitted task manifest in the same
queue database. Separate Actions runners have separate queues: this does not
promise global exactly-once execution or deduplication across runs. Multiple
procurements by one organization remain separate notice IDs. Conflicting
versions of one ID remain in source evidence and block qualification.

## Pilot choice and interpretation

Candidate D (industrial tenders/buyer discovery) uses the public World Bank
procurement API, with `qterm=steel` and three results. The endpoint returned
usable structured evidence during the bounded probe. Hydrotester and MOP
policy entries still require controlling specifications, current prices,
qualification and payment/compliance evidence. This is a low-complexity
source-adapter choice, not a claim that tenders have the highest market ROI.
Business project authority remains unresolved, so the internal ID stays
`PRJ-NEXUS-SANDBOX`; the World Bank project ID is a separate source field.
Missing source-route config and staged prompt files are revision gaps; no
replacement control plane or fabricated availability is introduced.

Primary source references:
[official supplier page](https://www.worldbank.org/ext/en/what-we-do/project-procurement/for-suppliers),
[public dataset and licence](https://datacatalog.worldbank.org/search/dataset/0037795/world-bank-procurement-notices).
Publication by this portal is a source CLAIM, not independent corroboration.
Search hits and discovery totals are not verified commercial opportunities.

All candidates remain `REJECTED_INSUFFICIENT_EVIDENCE`: no independent entity,
technical qualification, eligibility or commercial-feasibility verification is
implemented. Source retrieval/integrity, execution and assessments can be
VERIFIED while commercial opportunities verified/actionable/review-ready stay
zero. The next action is read-only primary-document and independent verification.
No customer/supplier contact, email, bid, purchase or commercial commitment occurs.

The first live sample contained OP00476469, a Micronesia roads/steel-composite-
bridge invitation, plus two contract awards. This is works procurement, not
confirmed direct steel demand. The source title differs from its full notice
about one road length (1.5 km versus 2.4 km observed during initial discovery);
technical specs and quantities therefore remain UNKNOWN. Full documents were
not ingested by the production pilot. No demand, stock, margin or revenue is
inferred. An expired/irrelevant/award record receives explicit rejection reasons.
The API deadline's local timezone is unconfirmed; its timestamp is used only
for conservative screening, never deadline-sensitive action.

## KPI and scoring contract

Summary records execution timestamp, exact commit label, project/lane, unique
notice count, rejected/verified/actionable/review-ready counts, duplicates,
duration, CPU seconds, response bytes, attempted requests, API cost, model tokens,
relevance count, publication freshness, completeness and failure categories.
Duration is time to an assessment report. Time to an actionable report is UNKNOWN
when there is no actionable result. Empty samples do not prove market absence.

Completeness measures populated identity, country, description, specifications,
quantity, terms, price and deadline (eight equally weighted fields); it measures
field coverage, not truth. Retrieval time is never substituted for publication
time. Missing publication/price remains UNKNOWN; prices are never treated as zero.

`research-priority-v2` dimensions/weights: official source credibility .20,
entity verification .15, lexical technical relevance .20, feasibility .10,
completeness .10, time sensitivity .10, economic value .10 and operational
complexity .05. Unknown dimensions
are excluded from the denominator and shown with `known_weight`. The score is
research priority only, not a verification gate, fit certification or probability
of winning. Current pilot knows source provenance/lexical fit/coverage/deadline
screening only. Unknown entity/feasibility/value cannot qualify a candidate.
Raw source and retrieval time reproduce every derived metric and score offline.

Weights can be supplied with `--weights-json <reviewed-local-file>`; all eight
positive finite weights must sum to one. The weight digest is part of the
existing queue manifest, so a replay with changed weights is a conflict, not a
second execution. Scoring configuration is never accepted from a public source.
The score and baseline Research Lab score do not authorize any action.

Each assessment also has `INVESTIGATE` or `REJECT`, with a Persian explanation of
the request/counterparty, unknown company capacity, technical/commercial gaps,
risk and next read-only action. Source text is escaped before Markdown output.
`PROCEED` is supported by the recommendation function only when independent FACT,
entity/technical/commercial verification, admitted authority and no missing
required information all exist. The live adapter cannot produce these states;
its HOLD/CLAIM result cannot proceed regardless of score. This is a recommendation
function, not an action executor. No management-ready commercial offer is claimed.

## Security, rollback and next operation

Only fixed HTTPS GET is reachable. Provider text is data, never shell, markup or
agent instructions. No secret inputs or approval mutation is used. Inherited
submission refuses alternate projects/actions/approval IDs. Authority preflight
remains BLOCK and Source Registry/Master HOLD remains unchanged. Safe independent
read/draft/test work does not confer commercial authority.

Rollback: revert the scoped PR or disable the separate pilot workflow. Existing
runtime/smoke workflow, Docker/Railway deployment, business stores and production
settings are unchanged. Temporary queues are discarded; safe public artifacts
and committed evidence remain for audit. No migration or paid host is involved.

Next operation after review: rerun the bounded workflow on an approved revision;
then investigate OP00476469's controlling documents/independent buyer evidence in
a separately bounded read-only lane. Do not contact or submit to the buyer.

Acceptance results and exact run IDs are retained in
`data/research/commercial-pilot-acceptance-20261027.json` when verified.
