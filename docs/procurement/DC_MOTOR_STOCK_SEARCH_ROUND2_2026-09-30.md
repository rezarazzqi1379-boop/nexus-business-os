# DC main motor stock search, ROUND 2 (2026-09-30)

Scope: used / stock / surplus / NOS DC main motors for a steel rolling mill, 900-2800 kW, base speed 400-750 rpm. Research only. No seller was contacted, no form filled, no login, no bid, no CAPTCHA solved. Nothing committed to git.
Budget used: about 35 searches (of about 40), 15 page loads (of 15). Round 1 file: `/home/claude/work/DC_MOTOR_STOCK_SEARCH_2026-09-30.md` (unit IDs S1-S2, P1-P10, W1-W7, C1-C7 are Round 1's).

Status words: LIVE = page loaded today and still shows the ad; STALE = page loaded or dated, but old (2 years or more) so availability is doubtful; GONE = removed or sold; UNVERIFIABLE = seen only as a search-index snippet, page not loaded (budget spent or site blocked). "LIVE" never means the motor is confirmed available, only that the ad exists. Nobody was asked.

---

## 1. Bottom line

1. **No LIVE unit is confirmed at 1-2.5 MW with a 500-600 rpm base in a target country (RU / KZ / UZ / BY / TR / CN).** The market for used MW-class DC main motors in these countries is thin; nearly every Chinese ad is 2019-2023 and every Russian MW-class ad is either a placeholder, an archive list (2021 or older) or a catalogue entry.
2. **Closest LIVE unit on spec:** Casey Equipment, GE MCD9844, 1500 HP (1119 kW), 500/1000 rpm, 630 V, 1900 A, 1977, Pittsburgh PA, USA. The spec sheet page loaded. No price shown. It is in the US, so it is not a "target country" unit, and it is 49 years old.
3. **Closest unit in a target country with a live page:** S1 МПЭ-1000 (1120 kW, 600 V, 1980 A, 630/1000 rpm), Vladimir, Russia. Page loaded and unchanged, last updated 11.02.2026. Price shown ₽10,000 is a PLACEHOLDER, not a price. It is a dragline (ЭШ-20/90) hoist motor and its availability is UNVERIFIABLE.
4. **New lead, probably not a fit at 500 rpm:** Siemens 1HS1562-5FG40-Z, Mogilev, Belarus, elec.ru ad dated 24.08.2026. Nameplate text "625-1250кВт, 520-1000В, 1340А, 500-1000об/мин". This is a constant-torque range: my inference is about 625 kW at 500 rpm and about 1250 kW at 1000 rpm. So the 900 kW+ rating is at higher speed than the target. No price, condition "С хранения" (from storage).
5. **Price:** the Round 1 ESTIMATE of US$26-89/kW is **withdrawn** (it mixed sub-900 kW, wrong-rpm, US-rebuilt and new-build points). Under the two-comparable rule there is **no defensible used-unit range** for the target class (only one in-class used priced listing, C1, and it expired). The only range I can support is for NEW Chinese motors, ESTIMATE, low confidence: **about US$35-40/kW** (section 4).
6. Sources that matter but stayed blocked: avito.ru, sahibinden.com, satu.kz, surplusrecord.com (section 6). Russian used MW-class DC stock is most likely on avito, so it is a real gap, not proof of absence.

---

## 2. Verified unit table (sorted by fit)

Fit rule: **Strong** = 1000-2500 kW, base about 500-650 rpm known, target country. **Partial** = kW in band but rpm missing or at the edge, or outside target countries, or page not readable. **Weak** = out of band or self-contradictory.
Dates are as shown on the page. "Price type" per the rules: ADVERTISED, NEGOTIABLE (договорная / 面议), PLACEHOLDER, HISTORICAL, none.

### 2a. Strong

| ID | Unit | Seller, place | Page date | kW | rpm (base/max) | V, A | Price and type | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| S1 | МПЭ-1000, "1120кВт, 600В, 1980А, 630/1000 об/мин ... ЭШ-20/90 как двигатель подъема". ehkskavator.ru/item/926267 | seller site mapkv.tilda.ws, Владимир, RU | updated 11.02.2026 11:06, 90 views | 1120 | 630 / 1000 | 600 V, 1980 A | ₽10,000, PLACEHOLDER (about US$118 at 84.34 RUB/USD, CBR 28.09.2026). VAT wording: none on page. Currency RUB | LIVE (page unchanged since Round 1); availability UNVERIFIABLE | Excavator (dragline) hoist motor, so it is a crane-duty design, not a rolling-mill main drive. 630 rpm base is above the 500-600 target. Real price unknown. |
| S2 | Z710-1B 1000 kW 660 V 600/1200. kmgiq.com 437090 | listing text: 杭州恒力二手直流电机 (Hengli, Hangzhou); location field 河北, text says 山东 | updated 2019-11-19 11:08, 472 views | 1000 | 600 / 1200 | 660 V | 面议, NEGOTIABLE | **STALE** (6.9 years) | Text says "two units, 八成新" but the quantity field says 1 (Round 1 said two). Location contradicts itself. Field "有效期至: 长期有效", "产品状态: 正常使用 / 仓库存放". Poster not registered on site. |

### 2b. Partial (Round 1 units, re-checked)

| ID | Unit | Seller, place | Date | kW | rpm | Price and type | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| P1 | GE 1400 HP CD4789, 500 V, qty 3 (East Coast Motor) | US | index date 2013-10-02 | about 1044 | 500 | request price | UNVERIFIABLE (index only) | 500 rpm on paper; US; 13-year-old index date, so treat as very stale. |
| P2 | GE 2500 HP 600 rpm (Surplus Record) | US | n/a | about 1865 | 600 | n/a | UNVERIFIABLE (surplusrecord blocked) | Best spec fit in Round 1, but cannot be opened. |
| P3, P4 | Gulf Electroquip dealer page: GE 1750 HP 650/1050 rpm CD9662 700 V, and 3000 HP 750 rpm TF4000 750 V (6 available) | Houston TX, US | n/a | 1305 / 2237 | 650/1050; 750 | "Request Price", NEGOTIABLE | UNVERIFIABLE | Index snippet only this round. |
| P5 | Kemsan (Karabük) 1000 kW 750/1200 rpm 440 V 2450 A | Karabük, TR | post 2019-06-17 | 1000 | 750 / 1200 | none | STALE / UNVERIFIABLE | The site's "2.El Motorlar" page (dated 2026-08 / 2026-09) is now full of casino and betting spam, so the site looks hijacked or neglected. Do not trust its contact data. All Kemsan DC entries date from 2013-2019 (CG 630 kW; CG 1000 kW; 800 kW 750-1200 rpm 1955 A 440 V; Reliance 560 kW; ASEA 560 kW). |
| P6 | Z800-6B 1600 kW 750 V, 51chuli.com | 新乡市良鑫机电设备销售有限公司 (宋经理), location 山东 淄博 | no date shown; "此贴长期有效" | 1600 | not stated | 面议, NEGOTIABLE; "9成新以上" | LIVE-UNDATED (page loads, no date) | This seller reposts many ads, mostly AC yKK710-8 1600 kW 6 kV motors, so a "1600 kW" ad from them is not proof the DC unit exists. Its 2020-era shop ads are the same trader as W6. |
| P7 | Z800-8 1800 kW, hs.huanboyun.com show-8311 | 湘潭大中电机 (徐解清), repair firm | updated 2023-03-09 16:36, 188 views | 1800 | not stated | 面议, NEGOTIABLE | STALE | Only kW, no rpm or V. |
| P8 | Z710-4B 1500 kW, kmgiq 437471 | 河北 唐山 (field) | 2019-11-19 | 1500 | not stated | 面议 | STALE (index date, not reloaded) | |
| P9 | Z710-4B 1000 kW 660 V, kmgiq 436044 | conflicting location | 2019-11-09 | 1000 | not stated | 面议 | STALE (index date, not reloaded) | |
| P10 | П2-800 (megasklad 770609) | RU | ad 12.2011 (a 07.2011 duplicate also exists) | n/a | n/a | n/a | STALE (GONE probable) | Still listed on the megasklad lots list, but 14 years old. |

### 2c. Partial (NEW this round)

| ID | Unit | Seller, place | Date | kW | rpm (base/max) | V, A | Price and type | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| N1 | **Siemens 1HS1562-5FG40-Z**, "625-1250кВт, 520-1000В, 1340А, 500-1000об/мин, Рассмотрим все предложения". elec.ru ad 1238350305 | ООО «Техсервопривод» (Петр Никодимович), Mogilev, BY | ad dated 24.08.2026 09:34 | 625-1250 | 500 / 1000 | 520-1000 V, 1340 A | none ("Рассмотрим все предложения" = offers considered) | LIVE (page loaded); availability UNVERIFIABLE | Condition "С хранения". The ad is a long boilerplate list of many small DC motors, so the seller may not hold this exact unit at the moment. My inference: at 500 rpm the rating is about 625 kW (520 V x 1340 A = 0.70 MW electrical, consistent), so it is below 900 kW at the target base speed. Needs a nameplate photo. |
| N2 | **GE MCD9844, 1500 HP (1119 kW)**, inventory ID 12247800000, Casey Equipment | Casey Equipment Corp, 275 Kappa Dr, Pittsburgh PA, US | spec page copyright 2026, no ad date | 1119 | 500 / 1000 | 630 V, 1900 A (630 x 1900 = 1.20 MW, consistent) | not shown | LIVE (page loaded, price not shown) | 1977, shunt, TESV, 34,000 lb, field 17.7 / 8.46 A. Same dealer lists a Reliance 15000T 1000 HP 400/1000 rpm 590 V (746 kW, six available), below band. |
| N3 | GE 1250 HP (932 kW) 600 rpm, frame 4686, 500 V, 1830 A, DPFVBB, "Electrically O.K." Romanoff stock 74115 | Romanoff Industries, US | n/a | 932 | 600 | 500 V, 1830 A | none | UNVERIFIABLE (index only) | Spec is in band; US. Same dealer's 1500 HP 850 rpm, 1500 HP 1000 rpm x3, 2500 HP 850 and 1000 rpm are above 750 rpm, so out of band. |
| N4 | GE 1250 HP (932 kW) 500 rpm, frame 8832, 700 V, 1425 A. Romanoff stock 90246 | Romanoff Industries, US | n/a | 932 | 500 | 700 V, 1425 A | none | UNVERIFIABLE (index only) | Spec matches the 500 rpm target; US. |
| N5 | Hot-mill line main motor "直流710-2A 2x1233KW 530/1000 R/MIN 660V 2000A", overload 2x for 1 min, Siemens DC controller. cnal.com 11108071 | 青岛通用铝业 (Qingdao), plant relocation sale | updated 2020-12-02 | 2 x 1233 | 530 / 1000 | 660 V, 2000 A | none | STALE | Sold inside a whole line ("仅使用半年"), not separately. Coilers Z400-3A 242 kW x2 per side. In band, but not a stand-alone unit. Round 1's "cnal Z560 800/980 kW" line is corrected in section 3. |
| N6 | П2-800-172-8, 1250 kW, 630-1000 rpm. megasklad.ru list 43325 | Леонид, Екатеринбург | 03.2021 | 1250 | 630 / 1000 | not stated | none | STALE | Unclear if sale or wanted ad. Same list also has ВАН 173/39-10 1600 kW 600 rpm and СДЭ2-17-69-8 2250 kW 750 rpm, both AC synchronous, not DC. |
| N7 | Z560-3B 1000 kW, Dongyuan (江苏东元电机). kmgiq 201911/13/436931 | 新乡 (Xinxiang) | 2019-11-13 | 1000 | not stated | not stated | 面议 | STALE | |
| N8 | Xiangtan Z560 group (ypshop.net snippets): "Z560 1000KW/750V 400~11.." ; "Z560 1000KW/660V 500~1.." ; "Z560-4B 1000KW/660V"; "Z560 800KW/660V 300~1000" | 湘潭 (Hunan) | undated | 800-1000 | the "500~" listing is the closest fit | 660 / 750 V | none | UNVERIFIABLE (index snippet only) | The 1000 kW / 660 V / 500~ rpm listing is the nearest match to a 500 rpm base I found in China, but it is undated and unopened. |

### 2d. Weak (unchanged from Round 1)

W1 D'Angelo 2000 HP Westinghouse, 800 rpm (above the 750 ceiling, US). W2 UTB ABB 1000 kW 504 V (rpm not shown, probably about 1000; EU). W3 SHS Grup 1950 kW Siemens SIMOTICS ₺780,000 (not shown to be DC; KDV not stated). W4 Siemens 1.5 MW Traiskirchen (self-contradicting data). W5 Z710-3B 1150 kW inside a whole cold mill. W6 800/1500/1600 kW Xinxiang trader ad (2019, no model). W7 Xiangtan frame-code-only items. No new information changes these.

### 2e. Tally

| Fit | Count | LIVE | LIVE-UNDATED | STALE | UNVERIFIABLE |
|---|---|---|---|---|---|
| Strong | 2 | 1 (S1, page only) | 0 | 1 (S2) | 0 |
| Partial | 18 (10 Round 1 + 8 new) | 2 (N1, N2) | 1 (P6) | 8 (P5, P7, P8, P9, P10, N5, N6, N7) | 7 (P1, P2, P3, P4, N3, N4, N8) |
| Weak | 7 | not re-checked | | | |

No unit is GONE with certainty (P10 is probably gone). None of the four LIVE pages states a firm price.

---

## 3. Corrections to Round 1

1. **S2:** the text says two units ("两台八成新") but the quantity field says 1. Location field says 河北, text says 山东. Ad last updated 2019-11-19 (STALE), not a current ad.
2. **S1:** re-loaded, still up and unchanged (updated 11.02.2026, 90 views). The ₽10,000 is a placeholder (and it is a dragline hoist motor). VAT wording: none.
3. **P5 Kemsan:** the site's DC page now carries casino / betting spam dated 2026-08-12 and 2026-09-21. Treat the site as compromised or abandoned; the DC posts themselves are 2013-2019.
4. **P6:** the page is live but has no date, and the same firm posts many AC yKK710-8 1600 kW 6 kV reposts in several provinces. The DC "Z800-6B 1600 kW" is not corroborated anywhere else.
5. **P7:** confirmed 2023-03-09, 188 views, no rpm or voltage. STALE.
6. **P10:** ad date 12.2011, a duplicate is dated 07.2011.
7. **Casey:** now confirmed as Pittsburgh PA with full nameplate (N2).
8. **cnal:** Round 1's "cnal Z560 800/980 kW" should read: one cnal listing is a Z560-3 575 kW x2 (500 V, 1250 A, 440-1000 rpm, below band); the in-band cnal item is the 2 x 1233 kW 710-2A inside a hot-mill line (N5).
9. **tiu.ru** is no longer a marketplace: it now shows a sports and betting-bonus site and search returns 404.
10. **Price band:** the Round 1 US$26-89/kW ESTIMATE is withdrawn (section 4). Round 1's FX assumption of 7.1 CNY/USD was too high; the checked rate is 6.71 (below), which raises every CNY-derived US$ figure by about 6%.
11. **Blocked sources stay blocked even through the laptop browser** (section 6).

---

## 4. Priced comparables and $/kW

**FX used, checked 2026-09-30 from public rate pages (mid-market, not a bank rate):** 1 USD = 6.71 CNY (28.09.2026; PBOC fix 6.7351 on 30.09.2026), 84.34 RUB (CBR official, 28.09.2026), 48.97-49.00 TRY (28.09.2026), EUR/USD not re-checked (Round 1's 1.10 kept, unverified).

### 4a. Used units in the target class (900-2800 kW, similar rpm, used)

| Listing | kW | Price | Price type | $/kW | Comment |
|---|---|---|---|---|---|
| C1 (Round 1) Tianjin 1250 kW, 七成新, huishoushang | 1250 | ¥230,000 = ¥184/kW | ADVERTISED, expired 2023-11-03 | 27.4 (at 6.71) | The only in-class used priced listing. |

**Result: fewer than two comparable used priced listings, so NO used-motor $/kW range is stated.** Other used prices are not comparable: C2 ABB 850 kW EUR 33,500 excl. VAT (below band, 1000 rpm, EU refurbished); C3 GE 1000 HP $66,640 (746 kW, US rebuilt, about $89/kW); W3 SHS Grup ₺780,000 for 1950 kW (about ₺400/kW, about US$8/kW, but not shown to be DC and KDV not stated, so excluded); a BidSpotter hammer price of US$2,900 for a remanufactured GE 1250 HP 850/1000 rpm CD6885 (Shreveport LA, date unknown; an outlier, out of rpm band, excluded).
Old Russian figures are HISTORICAL only: МПЭ1000 ₽1,150,000 and ₽2,200,000 (Jan 2012, megasklad Chelyabinsk); МПЭ450-900 ₽1,770,000 (2009). Not usable for 2026.

### 4b. New-build Chinese motors (ESTIMATE, low confidence)

| Listing | kW | Price | Price type | Computation | $/kW |
|---|---|---|---|---|---|
| Hengli Z710-2A 660 V 430/1000 rpm (b2b168.org, undated; "裸机价, 不含风机、测速机") | 980 | ¥260,000 "起" | ADVERTISED, "from" price | 260,000 / 980 = ¥265/kW; / 6.71 | 39.5 |
| Jiangsu Wangpai Z560-4 660 V 500 rpm (tuifa.cn, 10 units offered) | 800 | ¥187,000 | ADVERTISED | 187,000 / 800 = ¥234/kW; / 6.71 | 34.8 |
| C5 (Round 1) Z560-4A 750 kW 465/1025 rpm cautop.com | 750 | US$30,000, MOQ 10+ | ADVERTISED | 30,000 / 750 | 40.0 |

**ESTIMATE (new motor, ex-works China, marketplace asking prices, 2026-09-30, FX 6.71): about US$35-40/kW**, so roughly **US$35,000-40,000 per 1000 kW**. Caveats: three advertised prices; two of three are below 900 kW; one is undated; none is a quote. Excluded as placeholders or inconsistent: Wangpai Z560-3B 907 kW at ¥100,000 (about $15/kW, "是否现货: 否", updated 2026-08-20, contradicts the ¥187,000 for a smaller motor); Wangpai Z560 1000 kW at ¥1000 (zezzn.com, 2025-11-22); Hengli 1500 kW at US$1,000 (C6). Round 1 C4 (Harbin Z1000-5 2500 kW, US$194,672, about $78/kW) is a historical quote at 350/700 rpm and is not in the range. **This range is for NEW motors, not used ones, and must not be used as a used price.** For a used motor, a rough ceiling is a fraction of new, but no priced comparable supports a percentage.

VAT and currency notes: the Russian S1 price is RUB with no VAT (НДС) wording. No Turkish KDV wording was found on any price. The Russian AC reference (Русэнерго АОД-1600-4У1 ₽6,578,540 с НДС) is AC and only shows that Russian dealers state "с НДС". Chinese listings carry no VAT statement.

---

## 5. Market signals (context, not units)

- **Wanted / tender signals:** Ningxia wanted 2000 kW DC; 镔鑫 tender 1600 kW DC (2026-07-02, Z710-450 drop-in, 0-650/1200 rpm, 750 V, 4 months); Chelyabinsk MK tender 2014 (550 kW); 深圳华晟拍卖 "直流电机一批" auction 2026-08-05 (past); 大屯锡矿 waste DC motors disposal (awarded 2026-07-28); 云南锡业 auction. None gives a unit in band with specs.
- **Russian tenders and surplus lists** (b2b-center 4537089, 4348602, 4581741; tender.pro 1223833; Златоустовский ЭМЗ unclaimed motors): no MW-class DC motor found. b2b-center 4537089 is a СДМ-15-49-8У3 1250 kW 750 rpm 6 kV, which is AC synchronous.
- **Small Russian DC ads:** Воронеж (stanok-trading, 2026-08-24) Z450-750 750 kW 800 V x3 (2019) and 4ПБ450-750 750 kW x3 (2010), used, no price; Warsaw/Проммонтаж elec.ru (2026-07-31) ПЭ-162-6К 710 kW 1000 rpm new; Metaprom Д-816 150 kW ₽625,000. All below 900 kW.
- **KZ / UZ / BY:** olx.kz, olx.uz, nelikvidi.kz, all.biz Tashkent showed only AC or small DC. A news item says DC motors were supplied new for a Tashkent rebar mill.
- **Turkey:** makinecim and machineseeker show only small DC. No Kardemir or Isdemir DC motor lots found, only scrap-price pages.
- **Manufacturer catalogue (not stock):** ХЭМЗ П2-800 ratings 1250 kW 600 V 630/1000 (П2-800-172-8У3); 1000 kW 315/650; 1250 kW 400/700; 1000 kW 250/500; 1250 kW 315/600; 1250 kW 250/450; 1250 kW 750 V 200/400 (b2b-elektrodvigatel.ru). A new-build Russian route is a possible fallback but was not priced.

---

## 6. Blocked or unusable sources

| Source | Result |
|---|---|
| avito.ru | "Доступ ограничен: проблема с IP", CAPTCHA required. Not attempted further. BLOCKED. Likely the largest Russian used-motor market, so a real gap. |
| sahibinden.com | Cloudflare "Just a moment" verification. BLOCKED. |
| satu.kz | Browser pane approved once but navigation failed or was denied. BLOCKED. |
| tiu.ru | Now a sports and betting-bonus site, search returns 404. Not a marketplace. |
| surplusrecord.com | Blocked in Round 1; only dealer-page snippets reached via search (P2, P3, P4). |
| pulscen.ru | Search for "двигатель постоянного тока П2-800" returned only noise (tool drills, BelAZ ЭДП-600 at ₽4,780,000, Bosch). No MW-class DC unit. |
| torgi.gov.ru, fabrikant.ru, b2b-center | Reached only via search index; no MW-class DC lot found. |
| 1688 / alibaba / 阿里拍卖 / 京东拍卖 | Only 1688 price-page snippets (ZKSL710-2A 820 kW); no relevant DC judicial-auction lots found. |
| Kemsan site | Reachable but its DC page is spam-hijacked; contact data untrustworthy. |
| romanoffindustries.com, eastcoastmotor.com, ypshop.net, b2b168.org, tuifa.cn, gongchang.com, zezzn.com, bidspotter | Seen as snippets only, no page load left. |

The laptop browser pane was used for avito, tiu (x2), pulscen, sahibinden, satu attempt, and the tab was closed afterwards.

---

## 7. Queries run (about 35 searches, grouped, wording approximate)

WebSearch and Exa searches, English / Russian / Chinese / Turkish:
1. Russian marketplace queries: "двигатель постоянного тока 1000 кВт бу", "МПЭ-1000 продам", "П2-800 двигатель постоянного тока склад", "прокатный двигатель постоянного тока 1250 кВт", "двигатель постоянного тока 500 об/мин 1600 кВт", "Siemens 1HS двигатель постоянного тока бу" (elec.ru Mogilev found here), "П2-800-172-8", "ХЭМЗ П2-800 каталог" and related avito / pulscen / promportal / stanki.ru / metaprom / ru.all.biz phrasings.
2. Russian tender and surplus: b2b-center, torgi.gov.ru, fabrikant, tender.pro, Udokan Copper surplus, Златоустовский ЭМЗ, "реализация неликвидов двигатель постоянного тока", Воронеж stanok-trading.
3. KZ / UZ / BY: satu.kz, olx.kz, kupiprodai.kz, deal.by, kufar.by, olx.uz, all.biz Tashkent, nelikvidi.kz, SIMO Tashkent rebar mill.
4. Turkish: "ikinci el DC motor 1000 kW", "doğru akım motoru 1500 kW satılık", sahibinden / makinecim / makinaturkiye / turkishexporter / letgo, Kemsan 2.El Motorlar, Kardemir / Isdemir surplus.
5. Chinese: "二手直流电机 1000KW 1600KW Z710 Z800", "Z560 1000KW 660V 500转", "湘潭 直流电机 出售", 阿里拍卖 / 京东拍卖 "直流电动机 拍卖", "轧钢 主传动 直流电机 转让", cnal.com, 1688 二手直流电机, tender "直流电机 采购 1600kW".
6. US / EU dealers: "GE DC motor 1500 HP 500 rpm rolling mill", Casey Equipment MCD9844, Romanoff Industries GE 1250 HP, East Coast Motor GE 1400 HP, Gulf Electroquip, BidSpotter DC motor.
7. New-build price references: Hengli Z710-2A price, Wangpai Z560 price, Z560-4 800 kW price.
8. FX: USD/CNY September 2026; USD/RUB and USD/TRY 28 September 2026.

Page loads (15): Exa fetch of elec.ru Mogilev, megasklad list, ehkskavator S1; Exa fetch of 51chuli P6, huanboyun P7, kmgiq S2, Kemsan P5; Exa fetch of Casey spec sheet, cnal 11108071, Kemsan "2.El Motorlar"; browser pane avito, tiu.ru x2, pulscen, sahibinden (a satu.kz attempt did not load).
Stopping rule: new units were still arriving slowly (mostly US dealers and one Belarus ad); page-load budget was spent, so remaining leads are marked UNVERIFIABLE rather than chased.

---

## 8. Sources

- ehkskavator.ru/item/926267 (S1)
- kmgiq.com/sell/.../437090 (S2); .../437471 (P8); .../436044 (P9); .../436931 (N7); .../436948 (W6); 485007 (1000 x3 / 1250 x5 for wire-rod, 石家庄, 2020-06-10, not a fit listing)
- 51chuli.com listing 3cp42j11xj3hnwfq5w7 (P6)
- hs.huanboyun.com/sell/show-8311.html (P7); show-9374 (Z560-4B, index only)
- kemsanmotor.com.tr/2019/06/17/... and /2-el-motorlar/ (P5)
- elec.ru ad 1238350305, ООО «Техсервопривод» (N1)
- Casey Equipment spec sheet, inventory 12247800000 (N2)
- romanoffindustries.com stock 74115, 90246 (N3, N4; index snippets)
- cnal.com/equipment/11108071.shtml (N5); alqd.cnal.com detail-273514 (Z560-3 575 kW)
- megasklad.ru list 43325 (N6)
- ypshop.net Xiangtan Z560 listings (N8; index snippets)
- b2b-elektrodvigatel.ru ХЭМЗ П2-800 catalogue
- b2b168.org Hengli Z710-2A; tuifa.cn Wangpai Z560-4; gongchang.com Wangpai Z560-3B; zezzn.com
- FX: fxconverter.ch, valutafx.com, foreignexchange.org.uk (USD/CNY), cvj.ai (PBOC fix 30.09.2026), exchangerates.org.uk and ppt.ru (CBR) for RUB and TRY
- Round 1 file for C1-C7, W1-W7 and P1-P4 details
