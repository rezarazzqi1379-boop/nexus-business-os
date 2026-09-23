> **INTERNAL ONLY. Never send this file, and never copy any part of it into a vendor-facing document.**

# RFI Dispatch Sheet: PRJ-STEEL-ROLLING-LINE-01 procurement (v5, 2026-09-23)

This one sheet replaces three v4 files: `RFQ_BILINGUAL_PARITY_MATRIX_2026-09-22.md`, `RELEASE_BLOCKER_CHECKLIST_2026-09-22.md`, and the recipient lists that v1 to v4 carried inside the vendor-facing RFQs. Those three v4 files are kept in the repo as audit trail only.

**Status of every item: DRAFT. Nothing has been sent. No vendor has been contacted.**

## 1. Items

| Item | Vendor-facing files (v5) | Candidate recipients | Legal identity verified? | Owner approval to send | Sent |
|---|---|---|---|---|---|
| Furnace | `RFQ-FURNACE_EN_v5_2026-09-23.md` · `RFQ-FURNACE_ZH_v5_2026-09-23.md` | 南京年达炉业科技有限公司 (Nianda): PARTIAL; sister company 年达智能装备 exists, so confirm which entity signs · Wuxi Yushun (isunsteel): **RED FLAG**, no legal name found, main products EAF/LRF · Shanghai Prime Metallurgy: **RED FLAG**, self-declared trading company, conflicting founding years | No (public-web check only; gsxt blocked) | No | No |
| DC motor and drive | `RFQ-DC-MOTOR-DRIVE_EN_v5_2026-09-23.md` · `…_ZH_v5_…` | 杭州新恒力电机制造有限公司: PARTIAL; near-identical name 杭州恒力电机制造有限公司 exists · Shanghai Fortune / China Electric (Shanghai): **RED FLAG**, three company names on one site, HK-style suffix, one source says Beijing (see `QA_LOG_INTERNAL_ONLY_2026-09-22.md`) · 江苏航天动力机电有限公司: PARTIAL, strongest; 51% subsidiary of listed 600343 (FACT); catalogue up to 2200 kW | No (public-web check only) | No | No |
| Reversing stand | `RFQ-REVERSING-STAND_EN_v5_2026-09-23.md` · `…_ZH_v5_…` | Candidates, not yet checked: 无锡市伟盛机械有限公司 (φ650 two-high reversing, 800 t, built for copper strip) · Wuxi Lixing Metallurgy Machinery (Φ650×600 two-high hot reversible, DC; Chinese name UNKNOWN). Rejected: 无锡兴祥 (300 t at Φ500–600). | Not checked | No | No |
| Main gearbox | `RFQ-MAIN-GEARBOX_EN_v5_2026-09-23.md` · `…_ZH_v5_…` | Candidates, not yet checked: 南京高速齿轮 NGC (hot-mill gearboxes to 4200 kN·m; patent for combined reducer and pinion stand) · 重庆齿轮箱 (hot-mill main reducers and pinion stands) · optional: 宁波东力 (reversing plate-mill gearbox, but catalogue i ≤5.95) | Not checked | No | No |

**Open scope question before the stand RFI is sent at all (owner decision):** is the Ø600 two-high stand in the 2026-09-21 design basis existing plant equipment, or the stand the broker is offering? If it is existing plant equipment, a new stand may not be needed and this RFI may be dropped. Status: UNKNOWN.

## 2. Release procedure: every box must be ticked, per file, per recipient

**Gate A: before any RFI goes to anyone**

- [ ] Recipient's legal identity checked on 国家企业信用信息公示系统 (legal name, unified social credit code, status active, registered scope covers the item), with a screenshot saved to `docs/procurement/evidence/`
- [ ] Owner (Reza) gives explicit written approval for this file to this recipient
- [ ] `[Recipient full legal name]`, `From`, `Date` and `Ref` placeholders filled in (the `[NN]` sequence number assigned)
- [ ] The first line, `[DRAFT v5 — NOT APPROVED FOR RELEASE…]` / `[草稿第5版…]`, is deleted from the outgoing copy, and only from the outgoing copy
- [ ] Outgoing copy grepped for these strings, with zero hits required: `伟盛` `Lixing` `NGC` `南高齿` `重齿` `东力` `上海东方电气` `南京年达` `无锡宇顺` `上海臻工` `杭州新恒力` `江苏航天` `Nianda` `Yushun` `isunsteel` `Prime Metallurgy` `Hengli` `Fortune` `Aerospace` `Package A` `broker` `QA_LOG` `INTERNAL` `internal` `Suggested recipient` `建议收件人` `DRAFT` `草稿` `superseded` `取代`
- [ ] EN and ZH copies sent together, or the recipient's language chosen deliberately
- [ ] "Sent" logged in this sheet with date, channel and exact file hash

**Gate B: before any response is treated as formal RFQ pricing**

- [ ] Steel grade fixed (currently UNKNOWN; S235JR to S355JR assumed)
- [ ] Reversing or one-way stand confirmed (currently UNKNOWN in the design basis)
- [ ] Pass schedule confirmed (currently preliminary, [RDR], Package A §2)
- [ ] Acceptance criteria defined (FAT/SAT/performance-test basis)

**Gate C: before any order.** Project rule from `ENGINEERING_PACKAGE_A_TECHNICAL_2026-09-21.md` §5.1: "no order before hold points 1–7".

- [ ] Hold points 1 to 7 closed: roll-table length each side · roll material, neck and bearing data · housing and screw-down capacity · mill modulus · reversing or one-way · minimum roll diameter and spindle length · motor GD²
- [ ] Items in Package A §5.3 signed off by the named qualified engineer or manufacturer
- [ ] Owner's standing gate: a binding purchase order needs qualified-engineer sign-off

## 3. Bilingual parity, v5

Method: every requested field in each EN file was matched to its ZH counterpart, and every ZH field to its EN counterpart. The numbering of sections and list items is identical in the two languages, so the check is one-to-one.

| File pair | EN sections / numbered items | ZH sections / numbered items | Basis-table rows EN = ZH | One-directional gaps |
|---|---|---|---|---|
| Furnace | 4 / 15 | 4 / 15 | 5 = 5 | 0 |
| DC motor and drive | 4 / 12 | 4 / 12 | 14 = 14 | 0 |
| Reversing stand | 4 / 8 | 4 / 8 | 9 = 9 | 0 |
| Main gearbox | 5 / 7 | 5 / 7 | 14 = 14, plus duty spectrum 4 = 4 | 0 |

Every field that was in v4 is still present in v5. After the independent review, two v4 requests that the first v5 draft had narrowed were restored: furnace energy consumption for hot charge as well as cold, and the design stock size, now always stated. Two changes from v4 are deliberate. The 1000 rpm point was dropped from the stand's speed list because it is above the ≈700 rpm motor maximum. The stand's reducer and pinion questions now apply only if those items are in the vendor's scope, because the main gearbox has its own RFI. The v4 sentence saying our dimensions and throughput were "not yet finalized" was wrong, and v5 replaces it with the actual design basis (self-audit F8).

## 4. Where each number in the RFIs comes from

| Figure used in the RFIs | Source | Class |
|---|---|---|
| Slab 400×125×3000, 1177.5 kg; 20 t/h; Ø600×600 two-high; 3 m/s; product 400×6–30 | Package A §1.1 | FACT (owner, 2026-09-21) |
| 1250 °C discharge | Package A §1.1, row 7 | CLAIM (target) |
| 5.12 MN (6 mm case; phase-1 max 3.48 MN); ≥6 MN stand capacity | Package A T-A; Exec Summary | ESTIMATE [RDR], S355JR |
| 218.3 / 120.1 kN·m | Package A T-A, §4.4 | ESTIMATE [RDR] |
| 1600 / 2000 kW; 350 / 700 rpm; ≥1.5× for 30 s; S6/S9; 12-pulse regenerative | Package A §3.7 | [RDR] |
| Reversals 85–170/h by thickness (238/h = accelerations plus brakings) | Package A §8.4, T-3 (corrects the 238 in §3.7 and §4.1) | calculated |
| Peak regenerative power ≥650 kW | Package A §8.1 (corrects the 1000 kW in §3.7) | calculated |
| Reversing vs one-way | Package A §1.1, row 8 | UNKNOWN (RFIs say "reversing assumed") |
| 34 kN·m peak at motor shaft; 2040 kW at 647 rpm for 2.9 s | Package A §3.7, T-2 | calculated |
| Ratio ≈7.1, range 6.3–8.0; ≥330 / 405 / ≥655 / 805 kN·m; SF 2.21; ISO 6336/281; L10h 100,000 h | Package A §4.1, §8.2; Exec Summary (T-4 says 325/400/810: a rounding inconsistency inside the source) | [RDR] / ASSUMPTION |
| Two-stage preferred | Package A §8.5, T-5 | [RDR] |
| Duty spectrum | Package A §4.2 | calculated |
| Pinion centre ≈646 mm | Package A §4.4, T-I | [RDR], subject to GA |
| 25:1, "center 600", "35 tons", "3 m × 25 m" furnace | Broker material | SELLER CLAIM, unverified |
