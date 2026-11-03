# NEXUS steel buyer gate — evidence-based audit (2026-10-13)

Status: DRAFT / REVIEW REQUIRED. Project: PRJ-STEEL-SALES. No external outreach, paid enrichment, CRM write, deployment or merge.

## Reproducible GitHub state observed
- Main: `59f5fb386c023b1f04deaae15709c371e9bfd6d7`.
- PR #111 draft head before this documentation-only commit: `f40ec527abb88c63106d9c213a0c13f72e43d45d`.
- GitHub Actions run 38387610281: SUCCESS for exact head `f40ec527...`. Job `test` steps report canonical unittest, FM-005..FM-008, synthetic cloud health smoke and pytest regression success. **This does not test this new commit.**
- Source Registry v1.8 and Master Context v2.1 are user-supplied 2026-09-01 baselines; no newer authoritative canonical version verified in this audit. SOURCE_UNVERIFIED for any superseding source.

## Existing record reconciliation (no duplicate signal created)
- RU-STEEL-001 / notice 32616452647: B2B-Center page evidence recorded in `docs/STEEL_TENDER_PRIMARY_SOURCE_VALIDATION_2026-10-13.md`. Two contradictory deadline statements (Oct 16 vs Oct 19 12:00 Moscow). Treat as DEADLINE_CONFLICT, not verified open. Aggregate RUB 5,959,636.27 is not a unit price. Legal buyer AO Norilsktransgaz, INN 2457081355. No eligibility proof.
- OM-STEEL-002 / GT ref 147792321: GlobalTenders aggregator only; original OQ E&P procurement document and participation terms unverified. Deadline Oct 15 is a CLAIM.
- KZ-STEEL-006 / official notice 17721136-1: closed unsuccessful galvanized-tin lot, not active hot-rolled strip buyer.
- BY-STEEL-002: galvanized air duct is a fabricated finished good, not direct raw sheet demand.
- RU-STEEL-003: price monitoring is not equivalent to a buy tender.
- All other previously recorded signals remain in the existing register. This audit adds **zero** buyer signals and makes **zero** active-buyer claims.

## Static code/test audit — observed, not executed locally
Reviewed `nexus_steel_buyer_signal_gate.py` and `tests/test_nexus_steel_buyer_signal_gate.py` at PR #111.

1. `BuyerSignal` only carries project_id, buyer_name, source_url, evidence_type and one deadline. The intake protocol's legal ID, notice ID, original source, grade, dimensions, eligibility, contradictions and supersession fields are not enforced by the code. Maturity: DESIGNED in protocol, NOT IMPLEMENTED in classifier.
2. `classify_signal` validates URL prefix but not host/scheme parsing; `https://` alone would pass. Test coverage for malformed host and deceptive URLs is absent.
3. `date.fromisoformat` loses closing time and timezone. A same-day deadline is correctly left unverified, but conflicting dates cannot be represented; deadline conflict requires explicit fail-closed state.
4. The code accepts arbitrary non-empty project_id and buyer_name. It does not enforce project isolation or legal identity verification. No deduplication key or duplicate detection exists in the classifier.
5. `CLOSED_UNKNOWN` is documented in the intake protocol but is not accepted in the current evidence_type set. This is a schema contradiction, not proof of a failing CI test.
6. The tests cover expired, same-day, future-unverified, missing deadline, sale-side, award and a handful of invalid fields. No test covers duplicate notice IDs, conflicting deadlines, product mismatch, official-source verification, contact authorization or procurement eligibility.

## Next acceptance tests (proposed; not yet implemented)
- Same notice/legal buyer/product/date ingested twice -> one canonical record and one linked duplicate observation; never silently overwrite.
- Two conflicting authoritative/aggregator deadlines -> DEADLINE_CONFLICT and no VERIFIED_ACTIVE_BUYER promotion.
- Wrong project ID, finished goods, mismatched grade/width or unverified original notice -> fail-closed qualification.
- Invalid URL with no hostname or credentials/spoofed host -> reject.
- Explicit source hierarchy, UTC retrieval timestamp and supersession history preserved.
- Run local tests and GitHub CI on the exact new HEAD before marking TESTED.

## Material unknowns and approval boundary
- Latest superseding Source Registry/master, original Russian EIS notice documents, Oman OQ primary notice, buyer legal eligibility and named procurement decision-makers: UNKNOWN.
- No live CRM installation, production Windows service, active sale, verified active buyer, or export participation eligibility is proved.
- Next safe action: implement isolated tests and minimal fail-closed classifier change on this Draft PR; obtain source-level procurement documents. No merge, deploy, outbound message or paid action without exact approval.

Source locators: [PR #111](https://github.com/rezarazzqi1379-boop/nexus-business-os/pull/111), [CI 38387610281](https://github.com/rezarazzqi1379-boop/nexus-business-os/actions/runs/38387610281), [B2B-Center 32616452647](https://www.b2b-center.ru/search/number/l32616452647-1/), [OQ aggregator GT 147792321](https://www.globaltenders.com/tender-detail/structural-steel-materials-ms-special-stee-4uPOFVlwTg1dbTB3).
