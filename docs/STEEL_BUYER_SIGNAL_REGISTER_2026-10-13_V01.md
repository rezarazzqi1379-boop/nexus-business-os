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
