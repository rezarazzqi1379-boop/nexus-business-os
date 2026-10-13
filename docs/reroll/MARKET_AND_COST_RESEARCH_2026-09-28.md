# Market and Cost Research — Steel Plate Re-rolling Feasibility (PRJ-STEEL-REROLL-01)
Compiled 2026-09-28. Research only — no contact, no forms, no logins were made. No advertised price is presented as a transaction price; each row is labeled by price type.

**Price type legend:** ADVERTISED (seller asking price) · DAILY-MARKET-LIST (aggregator's daily list, not a confirmed trade) · AUCTION · HISTORICAL (stale/dated, kept only for reference) · ESTIMATE (derived/inferred, not sourced directly).

---

## 1. Iran market prices — hot-rolled black plate (ورق سیاه), ST37

### 1a. Current snapshot — ahanmelal.com, dated **1405/07/05 (2026-09-27)**
Pre-VAT list prices, Toman/kg. This was the only source that returned a genuinely current date; treat as DAILY-MARKET-LIST, medium confidence (price-comparison aggregator, not the mill's own gate price, not an exchange settlement).

| Mill | Thickness (mm) | Form | Price (Toman/kg) | Date | Price type | Source |
|---|---|---|---|---|---|---|
| Mobarakeh (فولاد مبارکه) | 6 | Coil, 1.5m | 124,545 | 2026-09-27 | DAILY-MARKET-LIST | [ahanmelal.com/steel-sheet/steel-black-sheet-price/mobarakeh-black-sheet](https://ahanmelal.com/steel-sheet/steel-black-sheet-price/mobarakeh-black-sheet) |
| Mobarakeh | 8 | Coil, 1.5m | 124,545 | 2026-09-27 | DAILY-MARKET-LIST | same |
| Mobarakeh | 10 | Coil, 1.5m | 120,000 | 2026-09-27 | DAILY-MARKET-LIST | same |
| Mobarakeh | 12 | Coil, 1.5m | 118,182 | 2026-09-27 | DAILY-MARKET-LIST | same |
| Mobarakeh | 15 | Coil, 1.5m | 113,636 | 2026-09-27 | DAILY-MARKET-LIST | same |
| Mobarakeh | 20 | — not listed by this mill — | UNKNOWN | — | — | — |
| Oxin Ahvaz (اکسین اهواز) | 8 | Factory sheet, 6×2/12×2 | 129,091 | 2026-09-27 | DAILY-MARKET-LIST | [ahanmelal.com/.../oxin-black-sheet](https://ahanmelal.com/steel-sheet/steel-black-sheet-price/oxin-black-sheet) |
| Oxin Ahvaz | 10 | Factory sheet | 123,636 | 2026-09-27 | DAILY-MARKET-LIST | same |
| Oxin Ahvaz | 12 | Factory sheet | 113,636 | 2026-09-27 | DAILY-MARKET-LIST | same |
| Oxin Ahvaz | 15 | Factory sheet | 118,182 | 2026-09-27 | DAILY-MARKET-LIST | same |
| Oxin Ahvaz | 20 | Factory sheet | 106,364 | 2026-09-27 | DAILY-MARKET-LIST | same |
| Gilan Steel | 2–15 | Coil, 1.0m | 98,545–99,455 | 2026-09-27 | DAILY-MARKET-LIST | [ahanmelal.com/.../gilan-black-sheet](https://ahanmelal.com/steel-sheet/steel-black-sheet-price/gilan-black-sheet) |

**Conflict flag:** Oxin's own table is non-monotonic (12mm cheaper than 15mm: 113,636 vs 118,182) — likely a listing quirk (spec/grade or delivery-location difference) rather than a real market inversion. Not averaged; reported as-is.

### 1b. Other Iranian sources — all returned stale/cached content, not current
| Source | Page date shown | Status |
|---|---|---|
| [ahanonline.com](https://ahanonline.com/product-category/انواع-ورق/ورق-سیاه/) | 1402/03/17 (≈2023-06-07) | HISTORICAL — cached, unusable for current pricing |
| [ahanprice.com](https://ahanprice.com/Price/ورق-سیاه) | 1403/03/01 (≈2024-05-21) | HISTORICAL — cached, unusable |
| [ahanonline.com تسمه](https://ahanonline.com/product-category/انواع-ورق/تسمه/) | title indicated "18 شهریور" (2026-09-09) but fetch failed (robots/timeout) | BLOCKED |

### 1c. Flat bar (تسمه), 5–10mm thickness — only stale data found
| Type | Thickness (mm) | Width (mm) | Price (Toman/kg) | Date | Price type | Source |
|---|---|---|---|---|---|---|
| تسمه ماشینکاری | 3–10 | 20–120 | 238,540–262,390 | 1401/04/09 (≈2022-04-29) | HISTORICAL | ahan021.com (via search) |
| تسمه فابریک | 3–5 | 20–60 | 180,460–212,120 | 1401/04/09 | HISTORICAL | same |
| تسمه نوردی | 5, 40 | 20–60 | 183,490 | 1401/04/09 | HISTORICAL | same |

**This data is ~4.5 years old and must not be used for current decisions** — see rial-volatility note below. No current (2026) flat-bar 200–300mm-width quote was retrievable this session; direct fetch of ahanonline's تسمه page was blocked. **Gap: current flat-bar price = UNKNOWN.**

### 1d. Plate offcuts / ته‌ورق / ضایعات ورق / ورق دست دوم
No dedicated current listing was found (these trade informally, dealer-to-dealer, rarely published). **UNKNOWN — gap.**

### 1e. Heavy melting scrap (قراضه/ضایعات آهن سنگین)
| Value | Unit | Date | Price type | Source | Confidence |
|---|---|---|---|---|---|
| 2,400–3,100 (avg ~2,700) | Toman/kg | 1398/03 (≈2019-05) | HISTORICAL | iranzayeat.com/prices/category/price-iron-castiron/ | Very low — 7 years stale, pre-dates massive rial depreciation |
| — | — | 2026-09-04 (13 Shahrivar 1405) article exists but was **BLOCKED** on fetch (robots/timeout) | — | [ahanonline.com/212228](https://ahanonline.com/212228/بررسی-نرخ-ضایعات-آهن/) | N/A |

**Gap: current (Sept 2026) Iran heavy scrap price = UNKNOWN.** Titles found via search (zayeatanbarmarkazi.ir, nikanzayeat.com, ahantakhfif.com — all dated Shahrivar 1405) look current but their pages could not be fetched (robots/connect-timeout errors on every Iranian scrap-dealer domain tried).

### 1f. USD/Toman free-market rate
| Value | Date | Price type | Source |
|---|---|---|---|
| ~228,000 Toman/USD (headline: "دلار به ۲۲۸ هزار تومان رسید") | 1405/06/28 (2026-09-19) | DAILY-MARKET-LIST (news-reported free-market/سنا rate) | [nournews.ir/.../346868](https://nournews.ir/fa/news/346868/) |
| ~166,000 Toman/USD ("دلار توافقی" — negotiated/NIMA-type rate) | 1405/06/28 (2026-09-19) | DAILY-MARKET-LIST (different FX channel) | [nournews.ir/.../346803](https://nournews.ir/fa/news/346803/) |
| 241,000 Toman/USD (2,410,000 Rial) | Page metadata showed 2024-09-27 (stale/cached) — order of magnitude plausible for late-2026 but date is wrong | HISTORICAL/unreliable | [tgju.org/profile/price_dollar_rl](https://www.tgju.org/profile/price_dollar_rl) |

**Conflict flagged, not averaged:** Iran runs multiple FX channels (free/street market vs. negotiated/NIMA). The ~228,000–241,000 Toman/USD band looks like the current free-market rate as of mid-to-late September 2026; the 166,000 figure is a separate, lower official/negotiated channel. Do not collapse these into one number.

---

## 2. International reference prices (late September 2026)

| Item | Value | Unit | Date | Price type | Source |
|---|---|---|---|---|---|
| HRC export, China (SS400 3×1250×C) | 498 | USD/tonne | 2026-09-28 | DAILY-MARKET-LIST | [mysteel.net/daily-prices/7163290](https://www.mysteel.net/daily-prices/7163290-hrc-export-prices-fob-china) (summary table; full FOB breakdown paywalled) |
| Plate export, FOB China | UNKNOWN — figures paywalled on every dated Mysteel page found (Apr–Aug 2026 listings, no September figure retrievable) | USD/tonne | — | — | [mysteel.net steel-plate-export-prices series](https://www.mysteel.net/daily-prices/7120572-steel-plate-export-prices-fob-china) |
| HMS 1&2 (80:20), CFR Turkey | UNKNOWN — figures paywalled on Fastmarkets/Kallanish; qualitative reporting only ("Turkish scrap buyers keep raising prices", "Turkish domestic scrap continues rise") | USD/tonne | Articles dated 2026-09-26 | DAILY-MARKET-LIST (qualitative only) | [kallanish.com/.../turkish-scrap-buyers-keep-raising-prices-0926](https://www.kallanish.com/en/news/steel/market-reports/article-details/turkish-scrap-buyers-keep-raising-prices-0926/), [fastmarkets.com MB-STE-0416](https://www.fastmarkets.com/commodity-prices/steel-scrap-hms-1-and-2-8020-mix-north-europe-origin-cfr-turkey-dollar-tonne-mb-ste-0416/) |

**Gap:** could not obtain a numeric Turkey scrap or China plate export figure — both sit behind paywalls (Fastmarkets/Kallanish/Mysteel require subscription for the actual number). Only the China HRC $498/t figure (from a free Mysteel summary table) was retrievable. This is too thin to cross-check the Iran thick/thin plate or plate/scrap spread with confidence — flagged as a research gap, not filled with an estimate.

---

## 3. Toll rolling (نورد کارمزدی) in Iran

No published toll rate (اجرت نورد) per kg was found anywhere in this session. Candidate workshops surfaced by search (**SUPPLIER CLAIM only — not verified, not contacted**):

| Name / site | Claimed location/activity | Source | Status |
|---|---|---|---|
| میلاد نورد یزد (Milad Rolling Yazd) | Yazd; rolling services (product/rate not shown on snippet) | [miladrolling.com](https://miladrolling.com/) | SUPPLIER CLAIM, unverified |
| نورد کار (navardkar.co) | "نورد ورق، نورد تیرآهن، نبشی، ناودانی، تسمه" — sheet/beam/angle/channel/flat-bar rolling | [navardkar.co](https://navardkar.co/product/sheet-rolling-corner-belt/) | SUPPLIER CLAIM; page fetch blocked (robots), content not verified beyond title |
| آسا گروپ اصفهان (Asa Group Isfahan) | "نورد ورق" — Isfahan | [asagroupco.com](https://asagroupco.com/نورد-ورق/) | SUPPLIER CLAIM, unverified |
| ایران سبز (iransabz-cnc.com) | "نورد کاری" — sheet/strip/tube/profile rolling, cold rolling | [iransabz-cnc.com](http://iransabz-cnc.com/نورد-کاری/) | SUPPLIER CLAIM, unverified |
| توسعه صنعت ایرانیان (ts-iranian.com) | "نورد" service listing | [ts-iranian.com](https://ts-iranian.com/دستگاه-های-صنعتی/خم-و-برش-ورق/نورد) | SUPPLIER CLAIM, unverified |
| نورد آذرخش (navardazarakhsh.ir) | Flat-bar (تسمه) sales "direct from factory" — appears to be a flat-bar producer/seller, not a toll-rolling service | [navardazarakhsh.ir](https://navardazarakhsh.ir/) | SUPPLIER CLAIM, unverified; may be product sale not toll service |

No results were found under the specific phrases "نورد مجدد ورق" or "نورد تسمه از ته ورق" as described industry practices — these searches returned only generic hot-vs-cold-rolling explainer articles, not evidence of an active offcut-re-rolling trade. **This suggests the practice may not be commonly advertised/documented online (it may be informal, word-of-mouth, Shamsabad-bazaar-type business), not that it doesn't exist.**

**Gap: toll-rolling rate (اجرت نورد) per kg = UNKNOWN.** No minimum-batch figures found either.

---

## 4. Iran industrial energy tariffs

Both target pages failed to load (robots/timeout on energypardaz.com; the Shana.ir URL exceeded the fetch proxy's length limit). Only page **titles** were confirmed via search, not their content:

| Item | What was found | Status |
|---|---|---|
| Industrial electricity tariff 1405 (peak/off-peak, Rial/kWh) | Page exists: "تعرفه برق صنعتی ۱۴۰۵ | جدول کامل نرخ مشترکان تولید" | [energypardaz.com/tarefe-bargh-sanati-1405](https://energypardaz.com/tarefe-bargh-sanati-1405/) — **fetch BLOCKED**, figures UNKNOWN |
| Industrial natural gas tariff (Rial/m³) | Page exists: "تعرفه نرخ گازبهای مصرفی دربخش های عمومی و صنعتی کشور" | [shana.ir/news/115702](https://www.shana.ir/news/115702/) — **fetch BLOCKED** (URL too long for proxy), figures UNKNOWN |

**Gap: both gas and electricity industrial tariffs = UNKNOWN this session.** Needs a retry with a different fetch method/source (e.g., a shorter Tavanir or NIGC PDF/URL) — flagged for follow-up, not estimated.

---

## 5. Small mill CAPEX bands

### 5a. Chinese small hot rolling mills / furnaces — live listings (fetched 2026-09-28)
| Item | Price (USD) | Capacity/spec | Date | Price type | Source |
|---|---|---|---|---|---|
| Wire-rod hot rolling mill (Luoyang Hongteng) | 38,000–108,000 | 0.5–10 t/h output; motor spec range given was very broad (90 kW–5,800 kW across models, not a single machine) | 2026-09-28 | ADVERTISED (EXW/FOB not specified) | [made-in-china.com Hot_Rolling_Mill listing](https://www.made-in-china.com/products-search/hot-china-products/Hot_Rolling_Mill.html) |
| Wire-rod/bar/rebar hot rolling mill (Xi'an Weikeduo) | 20,000–40,000 | Capacity not detailed | 2026-09-28 | ADVERTISED | same page |
| Hot rolling mill for steel processing (Henan Hongke) | 122,000–128,000 | Not detailed | 2026-09-28 | ADVERTISED | same page |

**Caveat:** these are wire-rod/bar mills, not confirmed as the specific "two-high reversing, roll Ø300–450mm, 55–250kW" plate/flat-bar configuration requested. No listing matched that exact spec closely enough to quote with confidence — treat the $20,000–$128,000 band as a rough order-of-magnitude reference for small Chinese mill packages, not a like-for-like quote. A separate, non-hot-rolling item was also surfaced and should **not** be confused with the target equipment:

| Item | Price (USD) | Spec | Source | Note |
|---|---|---|---|---|
| 3-roll/4-roll plate rolling (bending) machine | from $75,000 base | 2–200mm thickness, 500–12,000mm width | [europemachine.com/product/navard](https://europemachine.com/product/navard/) | This is a **plate-curving/bending** machine (for making cylinders/pipes), not a thickness-reducing hot mill. Listed for completeness only — do not use for CAPEX comparison. |

### 5b. Small batch furnaces (100–500 kg/h, gas or induction)
No listing matching this specific throughput/purpose (billet or plate reheating, not foundry melting) was found with a price. Alibaba induction-furnace results returned were general-purpose melting furnaces (aluminum/scrap melting), a different application. **Gap: UNKNOWN.**

### 5c. Used/stock small mills — Iran (divar.ir, sheypoor.com) and China
Searches returned only generic category/listing pages (e.g., [divar.ir/s/tehran/list/نورد](https://divar.ir/s/tehran/list/نورد)), with no individual listing or price visible in search snippets, and these dynamic marketplace pages were not fetched (would require live browsing, out of scope for this pass). **Gap: UNKNOWN — recommend a manual browse of divar.ir/sheypoor.com "دستگاه نورد" listings if this line is needed.**

---

## 6. Labour cost — Iranian workshop operator (1405)

| Item | Value | Unit | Date | Price type | Source |
|---|---|---|---|---|---|
| Approved minimum daily wage, 1405 | 554,185 | Toman/day | 1405 (year-start decision, reported 2026) | HISTORICAL (fixed statutory rate for the year) | [andishemoaser.ir](https://andishemoaser.ir/حقوق-پایه-وزارت-کار-۱۴۰۵-اعلام-شد؛-حداقل/) |
| Minimum monthly base (30 days) | ~16,625,550 | Toman/month | 1405 | HISTORICAL | same |
| Food/household allowance (بن) | 2,200,000 | Toman/month | 1405 | HISTORICAL | same |
| Spousal allowance | 500,000 | Toman/month | 1405 | HISTORICAL | same |
| Example total package, married worker + 2 children | ~26,150,000 | Toman/month | 1405 | HISTORICAL | same |
| Skilled rolling-mill operator premium over minimum wage | UNKNOWN | — | — | — | No sourced figure found this session |

**Gap: skilled-operator wage = UNKNOWN** (no published figure found; would need a labor-market survey or direct industry contact, which is out of scope here).

---

## Synthesis

**(a) Spread, 6/8/10mm vs 12/15/20mm plate (same-mill, 2026-09-27 snapshot only):**
- Mobarakeh: 10mm (120,000) vs 15mm (113,636) → ~6,400 Toman/kg (~5.6%) premium for thinner.
- Oxin Ahvaz: 10mm (123,636) vs 20mm (106,364) → ~17,300 Toman/kg (~16%) premium for thinner.
- Pattern: thinner plate trades **roughly 5,000–17,000 Toman/kg (≈4–16%) above** thick plate of the same grade/mill, based on a single-day, single-aggregator snapshot. Not cross-checked against a second date or source — treat as indicative, not definitive.

**(b) Spread, plate offcuts/ته‌ورق vs new plate:** **UNKNOWN.** No current offcut or ته‌ورق quote was retrievable this session (see §1d). Cannot be computed without inventing a number, which was avoided.

**(c) Realistic value of the existing pieces if sold:** **UNKNOWN with a defensible number.** No current Iran heavy-scrap price (§1e) or offcut/secondhand-plate price (§1d) could be retrieved — both the ahanonline scrap article and every scrap-dealer site tried returned blocked/timeout errors. Any Toman/kg figure offered here would be an unsourced guess, which the brief asks to avoid. **Recommended next step:** get one live quote from a scrap yard or ahanonline's scrap page (needs a working fetch route) before valuing the offcuts.

**(d) Toll-rolling cost range per kg: UNKNOWN.** No اجرت نورد rate was published or found on any candidate workshop's page (§3).

**Rial volatility note:** the free-market USD/Toman rate itself showed conflicting figures within the same week (~166,000 vs ~228,000+ Toman/USD, §1f), reflecting Iran's multi-channel FX system, and Toman steel prices move with it. **Any Toman price older than ~2 weeks should be treated as unreliable for a go/no-go decision** — the flat-bar data here (§1c, from 1401 / mid-2022) and the scrap data (§1e, from 1398 / 2019) are effectively unusable and are kept only to show that no better figure could be found, not as inputs to the feasibility math. Only the §1a plate table (2026-09-27, one day old) and the §1f FX headlines (2026-09-19, ~9 days old) are within a usable window.

## Key gaps requiring follow-up before the feasibility study can be finalized
1. Current Iran heavy-scrap price (Toman/kg) — every source blocked this session.
2. Current plate-offcut/ته‌ورق dealer price.
3. Toll-rolling rate (اجرت نورد) per kg and minimum batch size — no workshop published a rate.
4. Industrial gas and electricity tariffs (Rial/m³, Rial/kWh) — both target pages failed to fetch.
5. Turkey scrap and China plate export numeric prices — paywalled everywhere tried.
6. Skilled rolling-mill operator wage (vs. statutory minimum).
7. A small two-high reversing mill (Ø300–450mm rolls, 55–250kW) quote that matches the requested spec exactly — what was found (§5a) is wire-rod mills, an adjacent but not identical product.

---

## Addendum, 2026-09-28 (Claude, via the laptop browser): filling gaps 1c/1e

Iranian dealer sites that blocked the cloud fetch opened in the in-app browser on the owner's laptop. All values are read-only snapshots. Nobody was contacted.

| Item | Value | Unit | Date | Price type | Source |
|---|---|---|---|---|---|
| Heavy scrap, Isfahan: super-special / heavy / light (≥2 t) | 565,000 / 550,000 / 505,000 | Rial/kg | read 2026-09-28 | DAILY-MARKET-LIST (dealer buy posting) | mesterahan.com |
| Heavy scrap, Khorasan: super-special / heavy | 525,000 / 520,000 | Rial/kg | read 2026-09-28 | same | mesterahan.com |
| Scrap, Shiraz: super-special black, pieces under 1 m (≥2 t) | 520,000 | Rial/kg | read 2026-09-28 | same | mesterahan.com |
| Lots under 2 t | −3,000 | Rial/kg | read 2026-09-28 | same | mesterahan.com |
| HR plate 6 mm ST37 | 125,091 / 128,200–130,900 | Toman/kg | 1405/07/03 (2026-09-25) | DAILY-MARKET-LIST | fooladsell; pivan (search snippets) |
| HR plate, all sizes, range | 101,200–145,200 | Toman/kg | 1405/07/06 (2026-09-28) | DAILY-MARKET-LIST | shahrahan (snippet; low end is 8 mm fabric, 1200 wide) |
| HR plate 10 mm Mobarakeh 1500×6000 | 136,000 | Toman/kg | 1405/07/06 | DAILY-MARKET-LIST | smtnews (snippet) |

What these numbers mean:
- Scrap sells at about **52,000–56,500 Toman/kg**.
- Measured against new 12–20 mm plate (~106,000–118,000), scrap is worth roughly 45–50 % of plate.
- The plate-offcut (ته‌ورق) price remains UNKNOWN. `reroll_economics.py` brackets it between scrap and ~75 % of new plate, and marks that as an ESTIMATE.
