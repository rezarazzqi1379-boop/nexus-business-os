# Risk register: PRJ-STEEL-REROLL-01 (2026-09-28)

| ID | Risk | Likelihood | Impact | Mitigation / hold point | Owner |
|---|---|---|---|---|---|
| R1 | Tonnage too small or one-off, so any rolling route loses money | High (the photo shows 4 pieces) | High | HP-01 before any spend; default to route E | Reza |
| R2 | Rerolled non-standard pieces sell far below new plate (value ratio < 0.8) | Medium | High | HP-03: ask two buyers before the pilot | Reza |
| R3 | Actual grade is alloy or high-carbon, giving edge cracks and hardening | Low–Medium | High | HP-02: PMI before heating | Reza / lab |
| R4 | Heat loss on thin short pieces pushes finishing below Ar3, causing mixed microstructure and flatness problems | Medium | Medium | Reheat loop; finishing-temperature log; tensile and metallography in the pilot | Workshop |
| R5 | Scale and crop losses above the model (yield < 60 %) | Medium | Medium | Descale before charging; feed the square end first; the pilot measures actual loss | Workshop |
| R6 | Toll workshop refuses small or short pieces, or has a high minimum batch | High | Medium | Survey 3 or more workshops (draft RFI, owner sends) | Reza |
| R7 | Unmeasured stand stretch gives a wedge or gauge 0.4–2 mm off target | Medium | Medium | First-piece gap check; micrometer grid | Workshop |
| R8 | Price snapshot stale (rial volatility) | High | Low–Medium | The decision uses break-even ratios; re-run `reroll_economics.py` with fresh prices | Claude |
| R9 | Using the other project's Ø600 stand for these pieces | — | — | Excluded: not available; furnace and tables unsuitable (option C verdict) | — |
| R10 | Safety: manual handling of hot 12–19 kg pieces at a reversing stand | Medium | High | Tongs, guards, no hand feeding near the bite; the workshop's own safety regime | Workshop |
