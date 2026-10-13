# Steel Buyer Signal Register — 2026-10-13 — v0.1

**Scope:** public signals for Kazakhstan steel procurement only. Research leads, NOT verified current buyers, NOT permission to contact. Do not merge these signals into other engineering projects.

| ID | Named organization | Evidence | Steel product | Source URL | Dates | Classification | Confidence / blockers |
|---|---|---|---|---|---|---|---|
| KZ-STEEL-001 | Tengri Tyres Kazakhstan LLP | Third-party tender listing, GT ref 147809166 | 09G2S steel sheets and rolled steel pipes; alloyed products | https://www.globaltenders.com/tender-detail/to-request-a-cs-purchase-by-requesting-pric-8JEXBUOT0hBOBt3k | Released 2026-10-07; deadline 2026-10-12 | BUY_TENDER / EXPIRED | CLAIM, medium for historical procurement intent; official tender document and buyer identity not independently verified |
| KZ-STEEL-002 | Kazakhstan Temir Zholy JSC | Third-party tender listing ref 150597852 | Steel profile and steel sheet | https://www.kazakhstantenders.com/tender/commodities-and-materials-steel-profile-steel-sheet-repeat-8f9f0dc.php | Deadline 2026-10-13 | BUY_TENDER / CURRENT_DATE_DEADLINE_UNVERIFIED | CLAIM; official tender, precise closing time, eligibility, outcome unknown |
| KZ-STEEL-003 | Atyrau Oil Refinery LLP | Third-party tender listing GT ref 142961964 | Hot-rolled steel sheet | https://www.globaltenders.com/tender-detail/hot-rolled-sheet-FGoAyEo2gFS7kidE | Released 2026-08-01; deadline 2026-08-07 | BUY_TENDER / EXPIRED | CLAIM, historic signal only |
| KZ-STEEL-004 | Ust-Kamenogorsk Hydroelectric Plant LLP | Third-party tender listing TI ref 532096925 | Hot-rolled steel sheet | https://www.tendersinfo.com/tenders_details/hot-rolled-steel-sheet-532096925 | Tender 2026-04-27; deadline 2026-05-04 | BUY_TENDER / EXPIRED | CLAIM, historic signal only |

## Live platform comparison, one retrieval sample

| Platform | Test | Observed result | Limitation |
|---|---|---|---|
| Exa | Kazakhstan hot-rolled steel procurement tenders | Named buyers, product and dated third-party listings | Needs official-source confirmation; not evidence of live availability |
| ABRAMS Trade Intelligence | Buyer lookup HS 7208, country Kazakhstan | 2024 snapshot, as-of 2026-06-30; returned companies in Denmark, Panama and Puerto Rico | Country filter cannot be treated as verified match; shipmentScope=company_total is NOT HS-specific shipment proof |
| Apollo | Read-only prospecting capability discovery | People API search available via connector catalog | No steel buyer dataset or person record retrieved yet; no enrichment or credit-consuming action |
| Official procurement source | Not yet checked | UNKNOWN | Mandatory before an active tender or direct outreach claim |

## Classification and acceptance policy

- BUY_TENDER = explicitly procuring; SALE_TENDER = selling; RFQ = price inquiry; AWARD = concluded contract; CLOSED_UNKNOWN = historical/unknown result.
- **No steel demand evidence** means UNKNOWN, never 'does not need steel'. Classify a negative only with explicit sourced disqualification and a validity period.
- Match steel product grade, thickness, width, delivery geography, legal buyer identity and eligibility before opportunity qualification.
- Preserve source URL, retrieval date, document date, original quote or reference number, confidence, status, contradiction and supersession.
- HS 7208 covers hot-rolled non-alloy flat products width >=600mm; do NOT silently use it for narrower 400mm strip or alloy grades.
- Never equate a freight forwarder, supplier, or company_total shipment count with a steel-consuming buyer.
- No contacts, emails, outbound messages, paid enrichment, CRM writes, or live deployments authorized by this register.


## Additional discovery batch — 2026-10-13

| ID | Country / organization | Product | Primary or secondary evidence | Date/status | Assessment |
|---|---|---|---|---|---|
| KZ-STEEL-005 | Kazakhstan / Mangistaumunaygas JSC | Hot rolled sheet | https://www.kazakhtenders.com/tender/hot-rolled-sheet-8fa86ba.php ; aggregator ref 150636218 | Deadline 2026-10-13; official time unknown | CLAIM, BUY_TENDER / OPEN_STATUS_UNVERIFIED |
| KZ-STEEL-006 | Kazakhstan / Ulan-C LLP | Galvanized tin sheet, 0.3 mm, 1x2m, 20 sheets | https://old.goszakup.gov.kz/ru/announce/index/17721136?tab=lots ; official notice 17721136-1, lot 87876718-ОИ4 | Published 2026-10-02, ended 2026-10-07, notice completed; lot marked procurement not held | FACT from official portal snippet; BUY_TENDER / CLOSED_UNSUCCESSFUL, not open |
| KZ-STEEL-007 | Kazakhstan / Intergas Central Asia | Steel sheet | https://tenderimpulse.com/government-tenders/kazakhstan/steel-sheet-14590395 ; source notice 4502329 | Published 2026-08-28; expired 2026-09-08 | CLAIM, historic BUY_TENDER |
| OM-STEEL-001 | Oman / OQ Tawreed | Steel plates, insulation, refractory items | https://tenderimpulse.com/government-tenders/oman/6000061380-once-off-procurement-for-supply-of-material-steel-plates-insulation-r-14463801 ; notice 9900048329 | Published/expired 2026-08-20 | CLAIM, historic BUY_TENDER |
| OM-STEEL-002 | Oman / OQ Exploration & Production SAOG | Structural steel materials, mild steel and special steel | https://www.globaltenders.com/tender-detail/structural-steel-materials-ms-special-stee-4uPOFVlwTg1dbTB3 ; GT ref 147792321 | Released 2026-10-07; deadline 2026-10-15 | CLAIM, BUY_TENDER / OPEN_STATUS_UNVERIFIED; original tender/eligibility not checked |
| OM-STEEL-003 | Oman / OQ Tawreed | SS plate ALLEIMA 353 MA UNS S35315 | https://tenderimpulse.com/government-tenders/oman/6000061637-once-off-procurement-for-supply-of-material-ss-plate-alleima-353-ma-u-14597489 ; notice 9900048591 | Aggregator publication 2026-08-31 but deadline 2026-08-30 | CLAIM / DATE_CONTRADICTION / EXPIRED; require original document before using |

## Evidence integrity / tool comparison follow-up

- Official Kazakhstan procurement portal returned named buyer, exact lot, quantity, status and date: **stronger than third-party aggregator snippets**. Official evidence concerns galvanized tin and cannot be silently converted into hot-rolled coil demand.
- Exa retrieved two countries' named procurement signals; sample does not establish exhaustive coverage or reliable active status.
- ABRAMS HS 7214 Kazakhstan-filter query returned Canadian and Aruban companies; combined with the earlier HS 7208 mismatch this is a **reproduced geographic-filter problem**. Do not promote these companies as Kazakh buyers. The tool labels shipments `company_total`, not product-specific. 2024 snapshot is not proof of 2026 purchasing.
- Apollo people-search schema was discovered, but no company/contact prospecting result was verified; availability of tool != verified contacts.
- Source classification: original government notice = FACT about published record, not necessarily current purchase; third-party notices = CLAIM pending official validation.
- 'Does not buy steel' remains UNKNOWN without affirmative, dated and product-scoped exclusion evidence.
