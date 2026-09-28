# PRJ-STEEL-REROLL-01: economics and decision rule [PC]

Generated 2026-09-28 by `reroll_economics.py`. All values are concept estimates, not quotes. The Toman prices are a one-week snapshot. The conclusions rest on **ratios and break-even tonnages**, which move far less than absolute prices.

## 1. Price inputs

| Input | Low | Nominal | High | Unit | Evidence | Source |
|---|---|---|---|---|---|---|
| Heavy scrap buy price (dealer, >=2 t lots) | 52,000.00 | 54,000.00 | 56,500.00 | Toman/kg | DAILY-MARKET-LIST (buyer posting) | mesterahan.com scrap table read 2026-09-28: Isfahan super-special 565,000 / heavy 550,000 Rial; Khorasan heavy 520,000; Shiraz super-special <1 m 520,000 Rial |
| Usable plate offcut (ته‌ورق) sale to fabricators | 60,000.00 | 75,000.00 | 90,000.00 | Toman/kg | ESTIMATE (no current published quote found) | bracketed between scrap (floor) and ~75 % of new 12-20 mm plate; market research s1d: no listing retrievable |
| New HR plate 6 mm ST37 (mill sheet) | 124,500.00 | 128,200.00 | 130,900.00 | Toman/kg | DAILY-MARKET-LIST | ahanmelal 2026-09-27 (Mobarakeh 124,545); pivan 2026-09-25 128,200-130,900; fooladsell 2026-09-25 125,091 |
| New HR plate 8 mm ST37 | 101,200.00 | 124,500.00 | 129,100.00 | Toman/kg | DAILY-MARKET-LIST | shahrahan 2026-09-28 low end 101,200 (8 mm fabric); ahanmelal 2026-09-27 Mobarakeh 124,545, Oxin 129,091 |
| New HR plate 10 mm ST37 | 120,000.00 | 123,600.00 | 136,000.00 | Toman/kg | DAILY-MARKET-LIST | ahanmelal 2026-09-27 (Mobarakeh 120,000, Oxin 123,636); smtnews 2026-09-28 136,000 |
| Rerolled small pieces vs new mill plate (value ratio) | 0.70 | 0.82 | 0.92 | - | ESTIMATE | non-standard sizes (200-300 wide, 0.6-1.75 m), no mill certificate; buyers are small fabricators. HP-03 |
| Toll rolling charge (اجرت نورد), small batch | 10,000.00 | 20,000.00 | 35,000.00 | Toman/kg | ESTIMATE (UNKNOWN: no workshop publishes a rate) | market research s3; bracket only - the model reports the break-even rate instead |
| Toll campaign fixed cost (setup, furnace heat-up, transport, 1 trip) | 30,000,000.00 | 60,000,000.00 | 120,000,000.00 | Toman/campaign | ESTIMATE | no published figure; bracket |
| Free-market USD | 166,000.00 | 228,000.00 | 241,000.00 | Toman/USD | DAILY-MARKET-LIST (conflicting channels) | nournews 2026-09-19: 228,000 free market; 166,000 'tavafoghi' channel |
| Own small line CAPEX (mill S1 + batch furnace + tables + leveller + shear + install + import) | 150,000.00 | 250,000.00 | 400,000.00 | USD | ESTIMATE | Chinese small hot-mill listings USD 20-128k (ADVERTISED, 2026-09-28, not an exact spec match) + furnace, auxiliaries, foundation, freight, duties |
| Operator cost incl. overheads | 26,000,000.00 | 35,000,000.00 | 45,000,000.00 | Toman/person-month | ESTIMATE | 1405 statutory package ~26.15M Toman/month (married, 2 children); skilled premium UNKNOWN |
| Energy (gas reheat + mill electricity) per kg input | 300.00 | 800.00 | 2,000.00 | Toman/kg | ESTIMATE (tariffs not retrieved) | ~1.5-3 GJ/t batch-furnace gas + 30-60 kWh/t; Iranian industrial tariffs UNKNOWN this session; bracket is wide on purpose and still small vs the margin |
| Pilot testing (chemistry/PMI, 3 tensile, 3 bend, hardness, metallography) | 15,000,000.00 | 30,000,000.00 | 60,000,000.00 | Toman | ESTIMATE | lab price list not retrieved |

## 2. Value added by rolling, per kg of input (before conversion cost)

Definition: (net yield × new-plate price × value ratio for rerolled pieces) + (crop sold as scrap) − (value of the same kg sold as scrap). Net yield comes from `reroll_study` (low / nominal / high loss cases). Mill capacity is scenario S1 (Ø400 two-high reversing).

| Conversion | Net yield worst/nom/best | Uplift vs scrap: pessimistic | nominal | optimistic | Max toll rate vs scrap | Toll net vs scrap / vs offcut (nom) | Own line break-even t/yr: vs scrap nom / pessimistic / vs offcut nom |
|---|---|---|---|---|---|---|---|
| A 12->10 | 65% / 80% / 92% | 16,076 | 36,185 | 65,654 | 36,185 | 16,185 / -4,815 | 450 / 2,006 / 1,107 |
| A 12->8 | 63% / 78% / 91% | 7,275 | 36,070 | 59,393 | 36,070 | 16,070 / -4,930 | 452 / 5,352 / 1,116 |
| A 12->6 | 62% / 78% / 91% | 17,267 | 38,199 | 60,759 | 38,199 | 18,199 / -2,801 | 426 / 1,850 / 971 |
| C 15->10 | 66% / 81% / 93% | 16,342 | 36,604 | 66,319 | 36,604 | 16,604 / -4,396 | 445 / 1,969 / 1,076 |
| C 15->8 | 65% / 80% / 93% | 7,644 | 37,038 | 60,327 | 37,038 | 17,038 / -3,962 | 440 / 5,003 / 1,045 |
| C 15->6 | 66% / 81% / 93% | 18,526 | 39,789 | 62,044 | 39,789 | 19,789 / -1,211 | 409 / 1,709 / 886 |
| B 20->10 | 60% / 77% / 91% | 14,836 | 34,907 | 65,110 | 34,907 | 14,907 / -6,093 | 467 / 2,200 / 1,215 |
| B 20->8 | 62% / 78% / 92% | 7,155 | 36,014 | 59,642 | 36,014 | 16,014 / -4,986 | 452 / 5,477 / 1,121 |
| B 20->6 | 63% / 79% / 92% | 17,712 | 38,959 | 61,488 | 38,959 | 18,959 / -2,041 | 417 / 1,797 / 928 |

**Option E, no rolling:** selling the pieces as usable offcut (ته‌ورق) instead of scrap is worth 6,000 / 21,000 / 36,000 Toman/kg (L/N/H). This needs no equipment, no energy and no testing.

**Own small line:** fixed cost at nominal is about 15.9 billion Toman/yr for one shift (5-year simple amortisation of CAPEX, maintenance and labour).

**Pilot (about 100 kg, toll + tests):** cost about 92 M Toman against value created of about 3.7 M Toman. The pilot is an **information purchase**. It pays back only if a large recurring tonnage follows.

## 3. Decision rule by tonnage and by what the pieces can be sold as (HP-01, HP-03)

Median across the 9 conversions, nominal case: rolling adds **36,604 Toman/kg** over scrap value. A usable-offcut sale adds **21,000 Toman/kg** over scrap with no rolling.

| If the pieces can only be sold as... | Toll rolling pays when | Own small line pays when |
|---|---|---|
| **scrap** (~54,000 Toman/kg) | the lot exceeds **~5.4 t** per campaign at a 20,000 Toman/kg rate, including one pilot's fixed cost | recurring supply above **~445 t/yr** at nominal prices (~2,006 t/yr pessimistic) |
| **usable offcut** (~75,000 Toman/kg) | only if the toll rate is below **~15,604 Toman/kg**; otherwise selling as offcut wins | recurring supply above **~1,076 t/yr** |

## 4. Sensitivity notes

- The **value ratio of rerolled pieces** (HP-03) is the dominant unknown. At 0.70 several conversions barely beat scrap.

- **Energy** is under 3 % of the margin even at the high bracket. The missing tariff does not change any decision.

- **Toll rate:** no workshop publishes one. The table gives the maximum affordable rate instead of a guessed rate.

- **USD rate:** the free-market and 'tavafoghi' channels differ by about 30 %. This only shifts the own-line break-even (CAPEX is in USD). The ranking of routes does not change.

