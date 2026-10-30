# NEXUS Steel Research — Evidence Intake and Deduplication Protocol v1

Recorded 2026-10-13. Draft PR #111 only. This file is an operational procedure, not a claim of automated ingestion or live CRM deployment.

## Evidence fields required for each candidate

- `record_id`: stable country/product/notice identifier
- `country`, `buyer_legal_name`, `buyer_registration_id` if known
- `product_original`, `grade`, `dimensions`, `quantity`, `unit` (unknowns explicit)
- `procurement_role`: BUY_TENDER / SALE_TENDER / RFQ / AWARD / CLOSED_UNKNOWN / UNKNOWN
- `source_url`, `source_type` (OFFICIAL / OPERATOR / AGGREGATOR / TRADE_SNAPSHOT)
- `source_notice_id`, `publication_date`, `deadline_claims`, `retrieved_at`
- `evidence_class`: FACT / MEASUREMENT / CLAIM / ESTIMATE / ASSUMPTION / HYPOTHESIS / UNKNOWN
- `qualification_status`, `original_document_verified`, `product_match_status`
- `contradictions`, `supersedes_record_id`, `follow_up`, `contact_authorized=false`

## Intake algorithm

1. Retrieve Source Registry and project master; preserve project boundaries.
2. Search original procurement portals first, aggregators second, company/industrial capacity evidence third.
3. Deduplicate by normalized legal entity + source notice ID + product line + date; never by company name alone.
4. Keep conflicting deadlines as an array of claims; do not select a later date without authoritative evidence.
5. Historical tender is proof of past sourcing intent, not current open demand.
6. Separate buyer, supplier, broker, freight forwarder and unknown role. Company-total shipments are not HS-specific.
7. Distinguish no record found from explicit negative qualification. Never label a company NON_BUYER from search absence.
8. Do not promote a lead to VERIFIED_ACTIVE_BUYER until official source, live status, product match and participation conditions are established.
9. Do not enrich contacts, message, create live CRM records, bid, price or pay without exact authorization.
10. Store raw source URL and dated observations; rerun tests and update cross-chat recovery pointer after material changes.

## Sample measured discovery observations

- Kazakhstan official procurement notice 17721136-1, Ulan-C: 20 galvanized 0.3mm sheets; completed/unsuccessful lot. It does not establish hot-rolled coil demand.
- Norilsktransgaz notice 32616452647: two conflicting deadline claims 2026-10-16 and 2026-10-19 at 12:00 Moscow; quantities and initial aggregate tender price recorded in `STEEL_TENDER_PRIMARY_SOURCE_VALIDATION_2026-10-13.md`. Deadline unresolved.
- OQ Oman GT ref 147792321: aggregator-only; original notice and eligibility unresolved.
- ABRAMS HS 7208 and 7214: country-filter mismatches; source snapshot 2024 and company-total shipment counts require independent validation.

## Tool selection by acceptance test

| Source | Suitable question | Must pass |
|---|---|---|
| Official tender operator | Who is purchasing what, when and under what terms? | Notice ID, line item, status, original document |
| Exa | Where are relevant notices and company pages? | Repeatable URL + original source follow-up |
| ABRAMS | Which HS markets/companies warrant investigation? | Correct country, product-specific transaction and buyer role |
| Apollo | Who is responsible for procurement? | Verified employer/role and consent/authorization before enrichment or outreach |
| CRM (future) | How are verified opportunities tracked? | Isolated install, project isolation, audit, rollback, cost test |

## Current status

DESIGNED protocol, not production ingestion. Existing Draft PR tests verify tender deadline classification; they do not verify completeness of market coverage, legal eligibility or commercial conversion.
