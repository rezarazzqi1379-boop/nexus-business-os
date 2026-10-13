# Transmission Audit: PRJ-STEEL-ROLLING-LINE-01 (slab line)

**Date:** 2026-09-26
**Auditor:** independent (Claude, read-only)
**Model audited:** `slab_line_design.py` at `origin/feat/steel-recovery-sync-v0.2` @ `21c51b6` (PR #100). `evals/test_slab_line_design.py`: 70 passed.
**Active basis:** slab 400×125×3000 · 20 t/h furnace · two-high Ø600×600 · ≤3 m/s · S355JR design load basis (Package A §2, T-A).
**Scope:** Package A (with its errata banner), SLAB_LINE_PRELIMINARY_DESIGN (banner and §18), Package B, the Exec Summary, PROJECT_CONTROL, the four v5 EN RFIs with their ZH twins, the RFI dispatch sheet, and ENGINEER_SPEC_AND_STOCK_SEARCH.

This audit is retrospective. It recommends no setpoints, gaps, pass schedules or production changes, and it made no contact with anyone. Every number below is a concept figure **[PC]**, and none is released.

Reproduction: every audit script is in `docs/system/transmission_audit_2026-09-26/`. Each one adds the repo root to `sys.path`, so to re-run them, re-create that worktree at `21c51b6`. The audit removed it at the end.

| Script | What it produces |
|---|---|
| `model_run.py` | Load envelope, cycle, reversals, S235 vs S355 |
| `model_drive.py` | Gearbox trace, loss chain, DC options, T-2, inertia and regen |
| `model_duty.py`, `model_duty2.py` | T-E reproduction (the second confirms the inertia basis the document used) |
| `model_slow.py`, `model_eng_rev.py` | Engineer's 1:25 / 1250 kW / slow-mill recheck |
| `model_misc.py`, `model_interpass.py` | Scenarios, spread, pinion centre, sensitivities |
| `check_tables.py` | Cell-by-cell comparison of the pass tables |
| `extract.py` | Numeric extraction (normalises Persian digits ۰–۹, ٫ and ٬) and EN/ZH parity |

---

## 1. Summary

### Counts per class

**Vendor-facing RFIs** (four EN files; each ZH twin was checked by `extract.py parity`, carries the same numbers on the same lines, and so has the same findings):

| Class | Count |
|---|---|
| MATCH | 27 |
| MISMATCH | 12 (2 in the DC-motor RFI, 10 in the gearbox RFI) |
| NOT-FROM-MODEL, labelled | 24 |
| UNSUPPORTED | 1 (gearbox rated power ≥1800 / ≥2200 kW) |
| **Total consequential statements** | **64** |

**Internal documents** (A, SLAB, B, EXEC, CTRL, ENGSPEC, DISPATCH), counted as consequential statements; the tables in §4 list them:

| Class | Count |
|---|---|
| MATCH | ≈140 statements, plus **1,132 pass-table cells, all MATCH** (Package A T-B30…T-B6: 742 cells; SLAB §5 S235 tables: 390 cells; `check_tables.py`) |
| MISMATCH | 27 |
| UNSUPPORTED | 4 |
| NOT-FROM-MODEL | ≈30 (inputs, vendor and broker claims, engineer claims, gear-geometry assumptions). All are labelled, except "≥6 MN" and "2400 h/yr", which carry no basis. |

In total, the seven internal documents and eight RFIs contain 6,491 numeric tokens, including dates, IDs and section numbers. The counts above cover consequential engineering numbers only.

### Top issues

**P0: wrong number in a vendor-facing RFI (EN and ZH both)**

1. **"accelerations plus brakings up to ≈238 per hour" is wrong.** It appears in DC-MOTOR EN:29 / ZH:29 and MAIN-GEARBOX EN:40 / ZH:40. 238 is the **20 mm case only** (2 × 7 passes × 16.985 slabs/h). The model gives 204/h at 30 mm, **306/h at 12 mm (the phase-1 floor)** and **374/h at 6 mm**. So "up to 238" understates the event count by 29% in phase 1 and 57% for the 6 mm product that the same RFI declares as a later option. The errata banner's item 2 and the dispatch sheet (row 69) both treat 238 as a generic ceiling.
2. **The gearbox torque requirements are computed at the roll station but presented as gearbox *output* torque** (MAIN-GEARBOX EN:34–36 / ZH:34–36).
   - The ≥330, ≈405, ≥655 and 805 kN·m figures derive from peak roll torque 218.3 kN·m.
   - Referred to the gearbox output through the model's own loss chain (227.27 kN·m), the model gives **≥341, ≈419, ≥682 and 839 kN·m**.
   - The same RFI's duty spectrum (EN:54) states bite impact at the output of **455–682 kN·m**, which is *above* the "guaranteed peak ≥655 kN·m" it asks for. The document contradicts itself.
3. **"Peak regenerative power ≥650 kW" is below the model on the basis the errata banner itself states** (DC-MOTOR EN:31 / ZH:31; Package A §8.1 and banner item 3). The stated basis is GD²/4 = 750 kg·m², a 3 s ramp and 678 rpm.
   - That figure uses rotor inertia only. The model's `inertia_at_motor_kgm2(7.1, motor_rotor_j=750)` adds the 50 kg·m² drivetrain and the rolls, giving 802.9 kg·m². On that inertia the model gives **675 kW** at 678 rpm, or **719 kW** from the ≈700 rpm motor maximum.
   - The ramp time is an open Hold Point (Package A §5.1 #9, 2–4 s). At a 2 s ramp the model gives **1012 kW**.
   - The RFI states a hard minimum with no inertia or ramp basis. The banner's claim that "650 governs; 1000 is conservative, not wrong" is therefore itself wrong on the model's inertia definition.
4. **Duty spectrum "11 to 28 kN·m equivalent at motor shaft"** (MAIN-GEARBOX EN:52 / ZH:52). It comes from Package A T-E, which leaves out the model's 50 kg·m² drivetrain inertia. The current model gives **12.3–29.4 kN·m** for the same cases (rotor 450 kg·m² at 3 s, and 750 kg·m² at 2 s). The row also sits in an "Output torque" column while being stated at the motor shaft; at the gearbox output that is ≈82–196 kN·m.

**P1**

5. **The gearbox duty spectrum mixes two cycle bases** (MAIN-GEARBOX EN:51–53). The frequencies (102 and 204 per hour) use 17 slabs/h, which is a 212 s cycle. The time shares (22%, 38%, 40%) use a ≈95 s mill-limited cycle. On the 212 s cycle the shares are **≈10%, 17% and 73%**. The error is conservative for fatigue but internally inconsistent. The loaded-pass range "154 to 227" also omits pass 6 (24.5 kN·m), although the row says six passes.
6. **Gearbox rated power ≥1800 / ≥2200 kW** (MAIN-GEARBOX EN:37; Package A:406, classed there as "calculated"). No model function produces it, and the dispatch-sheet source map (§4) does not list it.
7. **Some RFI numbers are stated more firmly than their evidence.**
   - The stand RFI's 5.12 MN and 218.3 kN·m (STAND EN:26–27) do not say they are the **balanced (μ = 0.30)** scenario. On S355 the aggressive scenario gives **6.02 MN** (above the "≥6 MN" nominal capacity requested) and 334 kN·m.
   - The DC RFI (EN:18–27) gives 34 kN·m and 2040 kW with **no grade or scenario basis** at all.
8. **The capacity margins are on a different basis from the model's cycle function.**
   - The documents give "42–64% (12–30 mm), 31–32% (8–10 mm), 18% (6 mm)": Package A T-6 (lines 781–788) and §9 (line 872), EXEC:56–58, and B:92 and B:111.
   - `cycle_summary` gives **32–57%, 19–21% and 5%**.
   - B:92 puts "29–47 t/h", which is the `cycle_summary` basis, in the same sentence as "42–64%", which is not.
   - Package A carries three cycle definitions for the same schedule. For 10 mm they give 144 s (T-B10 and T-6), 168 s (§2.3, which equals the model) and 177 s (§2.2, which no model function produces).
   - T-B/T-6 use ramp-scaled reversal times (2.6–7.0 s) for capacity, but the same schedule's temperatures were computed with an 8 s interpass.
9. **The spread "400 → 405.8 mm (5.8 mm), margin 2.2 mm" is not what the model gives.** It appears in SLAB:22, SLAB:804, SLAB:1062, B:20, B:24, EXEC:46 and A:567. The model gives **404.8 mm** (every balanced schedule, either grade), so a 4.8 mm spread and a **3.2 mm** margin to +8 mm. SLAB's own pass tables (lines 211–242) show 404.8. The error is conservative.
10. **ENGINEER_SPEC capacity table** (lines 60–63). Its cycle times are understated by 20–28%.
    - At 1.0 m/s: model 110 / 210 / 336 s on the document's reversal-time basis, and 118 / 222 / 351 s on `cycle_summary`, against the document's 86 / 188 / 315 s.
    - At 1.5 m/s: model 94 / 168 / 258 s and 105 / 185 / 278 s, against 70 / 147 / 237 s.
    - At 1.0 m/s the mill, not the furnace, is the bottleneck at 12 mm (210–222 s against 212 s). That contradicts line 63.
11. **ENGINEER_SPEC and CTRL:130 call "1:25 + DC 1250 kW" internally consistent. That holds on power only.** The DC commutation reversal check, which is the one that rejected 1:12.5 with 1:3 field weakening in Package A §3.6, **fails at 1.5 m/s** for GD²/4 ≥ 450 at any 2–4 s ramp (130–415%), and passes at ≈1.0 m/s except with the heavy rotor at 2–3 s. See §3.
    - "~1.7 m/s" cannot be reached at 1:25 with a motor of 1200 rpm or less; the ceiling is 1.51 m/s at Ø600.
    - At 1.5 m/s a 12 mm product finishes at **812 °C**, below Ar3.
12. **With the 2000 kW option, the motor can put more torque into the gearbox than the gearbox RFI's guaranteed peak.** 54.6 kN·m × 2.0 (the model's envelope at base speed) × 7.1 × 0.941 = **729 kN·m**, against a guaranteed peak of ≥655. No RFI states a drive torque or current limit. This is a basis gap rather than a transmission error.
13. **Package B:142 says neck stress of 181–213 MPa "is rejected for cast iron"** (برای چدن رد می‌شود). Package A §9 row 4 withdrew exactly that judgement as premature (UNKNOWN / HOLD POINT).

**P2** (internal documents only; listed in §4): inertia basis in T-E, T-F, T-1 and §3.7 · §3.5's 75 kW average double-counts events · T-5 torques at the roll station · the banners are incomplete · a 646 vs 648.5 mm basis note · three different η values inside the model · ENGSPEC spindle angles omit the entry row.

---

## 2. Model output table (what the model computes today, with its basis)

Unless a row says otherwise, the basis is `build_schedule(t, "balanced", grade="S355JR")`: reversing, 8 s interpass, 30 s handling, ratio 7.1, a two-stage gearbox with η_overall 0.8992, and a 350 rpm base speed with 700 rpm maximum.

### Load envelope

| t mm | passes | max F MN | max T kN·m | per spindle kN·m | max P kW | longest piece m | finish °C | `cycle_summary` s | t/h | reversals per slab | reversals/h | accel+brake events/h |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 30 | 6 | 2.99 | 218.3 | 120.1 | 1834 | 11.9 | 1095 | 91.0 | 46.6 | 5 | 84.9 | 203.8 |
| 25 | 6 | 2.99 | 218.3 | 120.1 | 1834 | 14.2 | 1091 | 91.8 | 46.2 | 5 | 84.9 | 203.8 |
| 20 | 7 | 3.04 | 215.2 | 118.3 | 1676 | 17.8 | 1041 | 106.9 | 39.6 | 6 | 101.9 | **237.8** |
| 15 | 8 | 3.19 | 212.8 | 117.0 | 1503 | 23.7 | 975 | 124.8 | 34.0 | 7 | 118.9 | 271.8 |
| 12 | 9 | 3.48 | 210.9 | 116.0 | 1426 | 29.6 | 898 | 144.9 | 29.3 | 8 | 135.9 | **305.7** |
| 10 | 10 | 3.95 | 209.4 | 115.1 | 1371 | 35.6 | 810 | 168.1 | 25.2 | 9 | 152.9 | 339.7 |
| 8 | 10 | 4.08 | 209.4 | 115.1 | 1371 | 44.5 | 789 | 171.0 | 24.8 | 9 | 152.9 | 339.7 |
| 6 | 11 | 5.12 | 208.1 | 114.4 | 1319 | 59.3 | 673 | 201.4 | 21.0 | 10 | 169.9 | **373.7** |

- The S235JR schedule has the same geometry and exactly 1/1.15 of the loads: 189.8 kN·m and 1595 kW at 30 mm, 4.45 MN at 6 mm.
- Scenario range, S355: aggressive gives 3.70 / **6.02** MN and **334** kN·m; conservative gives 5.51 MN at 6 mm (17 passes).
- The final width is 404.8 mm on every balanced schedule, and 404.3–405.3 across scenarios.

### Drive train

| Quantity | Model value | Function / basis |
|---|---|---|
| Mass balance | 1177.5 kg; 16.985 slabs/h; 212.0 s | `mass_balance()` |
| Total service factor | 2.2138 | `total_service_factor()` |
| Gearbox trace, S355 30 mm, i = 7.1 | peak 218.3 (at the rolls); at gearbox output 227.3; RMS 79.1; criterion A 175.1; bite shock 2×/3× 436.6 / 654.9; criterion B **327.4** (governs); ×1.23 **402.8**; guaranteed peak **654.9**; expansion **805.5** kN·m | `gearbox_rating_trace(s, 7.1, cycle_s)`, **computed at the roll station** |
| The same, referred to the gearbox output | 3× bite **681.8**; criterion B **340.9**; ×1.23 **419.3**; 3× × 1.23 **838.6** kN·m | peak / (η_spindle · η_coupling · η_pinion · η_coupling) = /0.9605 |
| Gearbox trace, S235 30 mm | 284.7 / 350.2 / 569.5 / 700.4 | as above |
| Loss chain, 218.3 kN·m at i = 7.1, two-stage | 218.30 → 220.51 → 221.61 → 226.14 → 227.27 → 34.02 → **34.19** kN·m; η 0.8992 | `loss_chain(218.3e3, 7.1, 2)` |
| DC options | 1600 or 2000 kW / 350 rpm / FW 2.0 → ratio **7.1**; base torque 43.65 / 54.57 kN·m; 49.3 roll rpm at base; 3.097 m/s maximum | `build_dc_option(...)` |
| Governing power pass | 30 mm pass 4, 2.86 m/s, 1834 kW at the roll, **2040 kW** at the shaft, **646.9 rpm**, **2.894 s**; torque needed 30.1 kN·m | `motor_at_operating_point(best, kW, 350, 7.1)` |
| — at 1600 kW | continuous torque 23.6 kN·m, so **127.5%** of continuous; envelope 1.661; **76.8%** of envelope | as above |
| — at 2000 kW | continuous torque 29.5 kN·m, so **102.0%**; **61.4%** of envelope | as above |
| Commutation envelope at 350 / 450 / 550 / 650 / 700 rpm | 2.00 / 1.89 / 1.77 / 1.66 / 1.60 | `commutation_overload_limit` |
| Inertia at the motor, i = 7.1 | rotor 250 / 450 / 750 kg·m² gives 302.9 / 502.9 / 802.9 kg·m² (plus 50 drivetrain, plus 2.85 for the rolls) | `inertia_at_motor_kgm2(7.1, motor_rotor_j=…)` |
| Accel torque to 700 rpm, 2 / 3 / 4 s | rotor 250: 11.1 / 7.4 / 5.6 · rotor 450: 18.4 / **12.3** / 9.2 · rotor 750: **29.4** / 19.6 / 14.7 kN·m | `motor_duty(...)` |
| Reversal commutation utilisation, 1600 kW (2000 kW) | rotor 250: 30 / 20 / 15% · rotor 450: 50 / 34 / 25% · rotor 750: 80 / 54 / 40% (2000 kW: 24–64%). Rolling utilisation 76% (2000 kW: 61%) | `commutation_check(...)`, 30 mm |
| Braking per stop from 678 rpm, full-train inertia | rotor 450: 1.267 MJ / 0.352 kWh; 634 / 422 / 317 kW at 2 / 3 / 4 s · rotor 750: 2.024 MJ; **1012 / 675 / 506 kW**; from 700 rpm: 1079 / **719** / 539 kW | `braking_per_stop(J_total, 678, d)` |
| Braking per stop, rotor-only inertia (the documents' basis) | rotor 450: 1.134 MJ / 0.3151 kWh; 567 / 378 / 284 kW · rotor 750: 1.890 MJ; 945 / **630** / 473 kW | `braking_per_stop(450 or 750, 678, d)` |
| Hourly average regenerated power | rotor-only 450: 26.8–53.5 kW · full-train: 29.9–59.8 kW | `braking_hourly_average_kw` |
| Pinion-centre optimum | 12 mm with worn Ø560 rolls: 572–725 mm range, optimum **648.5**; 6 mm with Ø560: 566–725, optimum **645.5**; new rolls only: 668.5 / 665.5. Worst spindle angle at 646 mm: 1.51° (1500 mm spindle), 1.26° (1800 mm) | `optimal_pinion_centre_mm` |
| Stand and roll | neck stress 181.4 MPa at 5.12 MN (213 MPa aggressive); barrel deflection 0.092 mm; stand stretch 0.64–1.71 mm; lateral margin 100 mm | respective functions |
| Interpass 12 / 8 / 5 / 3 s at 10 mm | finish 766 / 810 / 847 / 873 °C; cycle 204 / 168 / 141 / 123 s; 20.8 / 25.2 / 30.0 / 34.4 t/h | `build_schedule(..., interpass_seconds=)` |
| Bearing torque share | ≤2% on the governing passes; 15% only on a 0.2 mm skin pass where rolling torque is 4 kN·m | inline check in `check_tables.py` |

---

## 3. Arithmetic checks

### 3.1 The ENGINEER_SPEC claim: 1:25 with DC 1250 kW gives ≈1–1.5 m/s

Basis: v = π·D·n_max / (60·25), with new rolls of Ø600–620 and no slip, top speed reached at the motor's maximum rpm (the document gives no base or maximum speed; it cites the market Z560 at 400–500 / 1100–1200 rpm, a vendor CLAIM).

| n_max | Ø600 | Ø620 | Document |
|---|---|---|---|
| 700 rpm | 0.880 | 0.909 | 0.88–0.91 ✓ |
| 1000 rpm | 1.257 | 1.299 | 1.26–1.30 ✓ |
| 1200 rpm | 1.508 | 1.558 | 1.51–1.56 ✓ |

- **The arithmetic is correct.** "≈1–1.5 m/s" requires a motor maximum of 796–1194 rpm on Ø600 rolls, which means field weakening of 2.0–3.0 on a 400 rpm base. At the Package A ceiling of 700 rpm the answer is 0.88 m/s. The document's FM-009 note is correct.
- Base speed at 1:25 corresponds to 0.50 m/s (400 rpm) or 0.63 m/s (500 rpm) at the roll surface, so almost every pass runs in the constant-power region.

**Power check.** Linear scaling gives 2040 × 1.5 / 2.86 = 1070 kW, and 1250 kW would then reach 1.75 m/s. The model, re-run with the speed ramp capped (`model_slow.py`; S355, balanced), gives the following peak shaft power:

| Speed cap | Peak shaft power | Share of 1250 kW continuous |
|---|---|---|
| 1.0 m/s | 676 kW | 54% |
| 1.5 m/s | **966 kW** | 77% |
| 1.75 m/s | 1139 kW | 91% |

So the document's 1070 kW is conservative (+11%), and "1250 kW suffices up to ≈1.7 m/s" is **true on power**. At 1:25 with a motor of 1200 rpm or less, however, 1.7 m/s is **not reachable**: the ceiling is 1.51 m/s.

**Commutation check** (not done in the document; `model_eng_rev.py`). This uses the same `commutation_check` that rejected 1:12.5 in Package A §3.6: 1250 kW, i = 25, 30 mm, S355, full-train inertia, rotor 250 / 450 / 750 kg·m², ramps 2 / 3 / 4 s.

| Speed | Motor top speed | Base speed | Reversal utilisation (rotor 250 · 450 · 750; each at 2 / 3 / 4 s ramp) |
|---|---|---|---|
| ≈1.5 m/s | 1194 rpm (envelope 1.21) | 400 rpm | 156 / 104 / 78% · 259 / 173 / 130% · 415 / 276 / 207% |
| ≈1.5 m/s | 1194 rpm | 500 rpm | 130 / 87 / 65% · 216 / 144 / 108% · 346 / 231 / 173% |
| ≈1.0 m/s | 796 rpm | 400 rpm | 52 / 35 / 26% · 87 / 58 / 43% · 139 / 92 / 69% |
| Package A reference: 1600 kW / 7.1 at 3 m/s | 700 rpm | 350 rpm | 30 / 20 / 15% · 50 / 34 / 25% · 80 / 54 / 40% |

The rotor inertia of a 1250 kW machine is UNKNOWN. The rows are a sensitivity using Package A's inertia scenarios.

**Thermal check** (`model_slow.py`). Finish temperatures:

| Speed cap | 20 mm | 15 mm | 12 mm | 10 mm |
|---|---|---|---|---|
| 1.5 m/s | 996 °C | 910 °C | **812 °C** | 704 °C |
| 1.0 m/s | 957 °C | 855 °C | 744 °C | — |

Taking Ar3 as ≈820–850 °C (an ESTIMATE), the product floor moves from 12 mm to about 15 mm at 1.5 m/s, and to about 15–20 mm at 1.0 m/s. The document's wording "~12 or 15 to 30 mm" holds only at the 15 mm end.

**Torque statement "560–700 kN·m on the roll".** That range is 1250 kW base torque × 25 × 0.941, which is the torque at the *gearbox output*. At the rolls (× 0.899) it is **537–671 kN·m**. With a 2× overload it is 1074–1342 kN·m, which supports the document's own warning.

### 3.2 238 vs 85–170

238 = 16.985 slabs/h × 2 events × 7 passes (20 mm). Reversals (passes − 1) × 16.985 give 85–170. Both formulas are right, but "up to 238" is not a maximum: accelerations plus brakings reach 306/h at 12 mm and 374/h at 6 mm. The annual figure checks: 85 × 2400 = 204,000 and 170 × 2400 = 408,000, matching T-3.

### 3.3 650 vs 1000 kW regeneration

| Case | Result | Note |
|---|---|---|
| Rotor-only inertia, 750 kg·m², 3 s | 630 kW | Package A's basis. 650 covers it. |
| Model inertia (802.9 kg·m²), 3 s | 675 kW | 650 does **not** cover it. |
| Model inertia, 2 s | 1012 kW | |

1000 kW therefore corresponds to the 2 s ramp, not to extra conservatism. The minimum an RFI should state depends on Hold Point 9 (ramp time) and Hold Point 7 (GD²). Neither is closed.

### 3.4 7.1 vs 12.5

`build_dc_option` gives 350 × 2.0 / 95.49 = 7.33, snapped down to the standard 7.1, which gives 3.097 m/s at 700 rpm ✓. The 12.5 in SLAB §8 was 1200 / 95.49 = 12.57, snapped to 12.5 (3.02 m/s) ✓. The SLAB banner already supersedes 12.5.

### 3.5 618 vs ≈646 mm pinion centre

Taking the full centre range (entry at 725 mm) with worn Ø560 rolls, the midpoint is 645.5 mm for the 6 mm schedule and 648.5 mm for the 12 mm schedule. 646 is within 2.5 mm of both. Worst spindle angle on a 1500 mm spindle: 1.51° at 646, 1.46° at 648.5, and 2.04° at 618 ✓.

The engineer's 600 mm centre gives 1.92° (Ø600) and 2.30° (Ø620) at the pass-1 exit gap, but **2.39° / 2.77° at the entry row**, which is the row Package A T-I treats as governing. ENGSPEC:50 omits that row.

### 3.6 1600 vs 2000 kW

T-2 is reproduced exactly: 127.5% vs 102.0% of continuous torque, and 76.8% vs 61.4% of the commutation envelope. Banner item 1 is consistent with the model.

### 3.7 Unit and magnitude sanity

- Bearing torque is ≤2% of rolling torque on the governing passes, so the N·mm → N·m fix is intact.
- Power = T·ω checks: 192.2 kN·m × 2π × 91.1 / 60 = 1834 kW ✓.
- Energy and power are separated correctly in T-1 (MJ / kWh / kW).
- mm and m are consistent in the deflection, neck stress, stretch and spindle-angle functions.
- **Package A §3.5 (A:339):** "238 × 1.1 MJ = 269 MJ/h = 75 kW average" counts accelerations as braking events. On T-1's basis the 20 mm figure is 32.1 kW. The error is a count, not a unit.
- **Model-internal inconsistency (P2).** The model uses three drivetrain efficiencies: `motor_duty` and `dc_motor_feasibility` use 0.941 (one gearbox stage, no couplings), `commutation_check` uses 0.904, and `loss_chain` / `motor_at_operating_point` use 0.899.
- **Model-internal inconsistency (P2).** `reversals_per_slab` counts n − 1 stops per slab, but `motor_duty` counts n decelerations.
- **Model-internal inconsistency (P2).** The docstring says μ²R overstates the bite limit by "about 4%" at μ = 0.25; the actual figure is 4.66%.

---

## 4. Mismatch table

Model commands refer to the scripts in `docs/system/transmission_audit_2026-09-26/`. The shorthand `s30 = build_schedule(30.0, "balanced", grade="S355JR")` and `mb = mass_balance()` are used throughout.

| # | File:line | Document value | Model value | Basis difference | Command | Prio |
|---|---|---|---|---|---|---|
| M1 | RFQ-DC-MOTOR EN:29 / ZH:29; RFQ-MAIN-GEARBOX EN:40 / ZH:40; DISPATCH:69; A:3 (banner item 2) | accel+brake "up to ≈238/h" | 204 (30 mm) · 238 (20 mm) · **306 (12 mm)** · **374 (6 mm)** | 238 is one thickness, not a ceiling | `2*len(build_schedule(t,…))*mb.slabs_per_hour` (`model_run.py`) | **P0** |
| M2 | RFQ-MAIN-GEARBOX EN:34–36 / ZH:34–36; A:403–405, A:686–689; EXEC:28; B:87, B:183 | rated output ≥330, ≈405; guaranteed peak ≥655; expansion 805 kN·m | at the output: **340.9 / 419.3 / 681.8 / 838.6** (at the rolls: 327.4 / 402.8 / 654.9 / 805.5) | roll-station torque labelled as gearbox output; the same RFI's EN:54 gives 682 | `gearbox_rating_trace(s30, 7.1, cycle_summary(s30)["cycle_s"])` ÷ 0.9605 (`model_drive.py`) | **P0** |
| M3 | RFQ-DC-MOTOR EN:31 / ZH:31; A:641 (§8.1); A:5 (banner item 3); DISPATCH:70 | ≥650 kW peak regeneration | **675 kW** (750 kg·m², 3 s, 678 rpm); 719 (700 rpm); 1012 (2 s) | rotor-only inertia vs `inertia_at_motor_kgm2`; ramp is a Hold Point | `braking_per_stop(inertia_at_motor_kgm2(7.1, motor_rotor_j=750), 678, 3)` | **P0** |
| M4 | RFQ-MAIN-GEARBOX EN:52 / ZH:52; A:428 | accel/brake 11–28 kN·m at the motor | **12.3–29.4** | drivetrain inertia (50 kg·m²) omitted | `motor_duty(s, 1600, 350, 7.1, c, mb.slabs_per_hour, accel_time_s=3 or 2, max_rpm=700, motor_rotor_j=450 or 750).accel_torque_nm` (`model_duty.py`) | **P0** (small) |
| M5 | RFQ-MAIN-GEARBOX EN:51–53 / ZH:51–53; A:427–429 | shares 22% / 38% / 40% at 17 slabs/h | at 212 s: **≈10% / 17% / 73%** (at `cycle_summary` 91 s: 23 / 40 / 37%) | frequency and share on different cycles | rolling 21.0 s, 12 × 3 s ramps, cycle 212 s (`model_run.py`) | P1 |
| M6 | RFQ-MAIN-GEARBOX EN:51 | "6 passes: 154 to 227 kN·m" | output-referred 24.5 … 227.3 | pass 6 omitted | `[p.torque_roll_nm/0.9605 for p in s30]` | P2 |
| M7 | A:108, 123, 140, 158, 176, 195 (T-B totals); A:781–788 (T-6); A:872; EXEC:56–58; B:92, B:111 | cycles 77 / 90 / 123 / 144 / 147 / 174 s; margins 42–64% / 31–32% / 18% | `cycle_summary`: 91 / 107 / 145 / 168 / 171 / 201 s; margins **57–32% / 21–19% / 5%** | Σ ramp-scaled reversal times vs the model's 8 s interpass (the one the temperatures use) | `cycle_summary(build_schedule(t,…))` | P1 |
| M8 | A:203–210 (§2.2 cycle column) | 95 / 97 / 113 / 132 / 153 / 177 / 180 / 211 s; "6 mm margin 1 s" (A:214) | no function gives these (91…201) | stale values | as M7 | P1 (UNSUPPORTED) |
| M9 | SLAB:22, 804, 1062; B:20, 24; EXEC:46; A:567 | 405.8 mm, 5.8 mm spread, 2.2 mm margin | **404.8 mm, 4.8 mm, 3.2 mm** (4.3–5.3 across scenarios) | contradicts SLAB's own tables (lines 211–242) | `build_schedule(t, sc, grade)[-1].exit_b` (`model_misc.py`) | P1 |
| M10 | ENGSPEC:60–61, 63 | cycles 86 / 188 / 315 s (1.0 m/s) and 70 / 147 / 237 s (1.5 m/s); "furnace remains bottleneck to ~10–12 mm" | 110 / 210 / 336 (118 / 222 / 351) and 94 / 168 / 258 (105 / 185 / 278); at 1.0 m/s, 12 mm is **mill-limited** | hand estimate vs model | `model_slow.py` (speed ramp capped at v_max) | P1 |
| M11 | ENGSPEC:42, 67; CTRL:48, 130 | "1250 kW internally consistent", "up to ~1.7 m/s" | power OK (966 kW at 1.5 m/s), but reversal commutation 130–415% at 1.5 m/s (rotor ≥450); 1.51 m/s maximum at 1:25 / 1200 rpm; 12 mm finishes at 812 °C | power-only check | `model_eng_rev.py`, `model_slow.py` | P1 |
| M12 | RFQ-MAIN-GEARBOX EN:37 / ZH:37; A:406 | rated power ≥1800 / ≥2200 kW ("calculated") | no function; 330 / 405 kN·m at 49.3 rpm correspond to 1704 / 2091 kW | — | — | P1 (UNSUPPORTED) |
| M13 | RFQ-REVERSING-STAND EN:26–27; RFQ-DC-MOTOR EN:18–27 | 5.12 MN, 218.3 kN·m (scenario not stated); 34 kN·m, 2040 kW (no grade stated) | balanced S355; aggressive **6.02 MN / 334 kN·m** | firmness | `worst_cases(build_schedule(6.0, "aggressive", grade="S355JR"))` | P1 |
| M14 | B:142 | "181–213 MPa … rejected for cast iron" | judgement withdrawn in A §9 row 4 (A:865) | text, not a number | — | P1 |
| M15 | A:301–318 (T-E); A:375; A:386; EXEC:37–38 | accel 9.2…27.6; 11.0 kN·m; RMS 34–44%; reversal 13 (or 17)–75% | 11.1…29.4; 12.3; 34–46% (6 mm); 15–80% (2000 kW: 12–64%) | inertia = rotor + rolls (drivetrain omitted), reproduced exactly by `model_duty2.py`; RMS on the unstated 6 mm schedule | `motor_duty` / `commutation_check` (`model_duty.py`) | P2 |
| M16 | A:326–328 (T-F); A:622–638 (T-1); B:119 | 0.63 / 1.13 / 1.89 MJ; hourly 26.8–53.5 kW | full-train 0.76 / 1.27 / 2.02 MJ; hourly 29.9–59.8 kW | rotor-only inertia; n − 1 stops | `braking_per_stop`, `braking_hourly_average_kw` | P2 |
| M17 | A:339 (§3.5) | 238 × 1.1 MJ = 269 MJ/h = 75 kW | 32.1 kW at 20 mm (T-1 basis) | accelerations counted as braking | `braking_hourly_average_kw(450, 678, 6*mb.slabs_per_hour)` | P2 |
| M18 | A:759–760 (T-5); B:190–194 | input 31.7 / 33.1 kN·m, intermediate 90.0 kN·m | 33.0 (single stage) / 34.5 (two-stage, 7.0) / 93.7 | roll station used as gearbox output | `loss_chain(218.3e3, 7.0, 2)` | P2 |
| M19 | ENGSPEC:44 | 560–700 kN·m "on the roll" | 537–671 at the rolls (562–702 at the gearbox output) | station label | inline, §3.1 | P2 |
| M20 | ENGSPEC:42 | 1070 kW at 1.5 m/s; 1280 kW at 1.8 m/s | 966 kW (1.5 m/s cap); 1139 kW (1.75 m/s cap) | linear scaling; conservative | `model_slow.py` | P2 |
| M21 | ENGSPEC:50 | first-pass angle at centre 600: 1.92° / 2.30° | entry row 2.39° / 2.77° | governing row omitted | `spindle_angle_deg(600, D+125, 1500)` | P2 |
| M22 | A:3–7 (banner) | lists 238 only in §3.7 and §4.1 | 238 also at A:339, A:544, A:571 | banner incomplete | `extract.py find 238` | P2 |
| M23 | SLAB:1–7 (banner) | covers ratio, weight, 618, and S235 in §5–6 | not covered: motor B 1600 / 400 / 1200 rpm / FW 1:3 (SLAB:41, 491–516, 889); 100–190/h (445, 915); 570 kN·m (801, 833, 920); "<1°" (447) | banner incomplete | `extract.py` | P2 |
| M24 | DISPATCH:66 | ≥6 MN sourced to "Package A T-A" | not in Package A; it is in EXEC:25 and SLAB:1078 (no stated basis) | mis-sourced | `grep "6 MN"` | P2 |
| M25 | SLAB:414 (§7.2) | gearbox output 195.7 kN·m (S235) | 197.6 | old η chain (no couplings) | `gearbox_rating_trace(S235 …)["at_gearbox_output_nm"]` | P2 (superseded document) |
| M26 | A:46, A:356; B:203 | "±40% in μ → ±9% force" | span 0.25 → 0.35 gives +8.7% (2.98 → 3.24 MN) | a span, not ± | `model_interpass.py` | P2 (wording) |
| M27 | A:450, A:492–498, A:840–846; RFQ-REVERSING-STAND EN:29 | 646 "lowest max angle" | model optimum 648.5 (phase-1 basis) / 645.5 (6 mm + Ø560 basis) | basis not stated; within rounding | `optimal_pinion_centre_mm(s, diameter_worn_mm=560)` | P2 |

---

## 5. What is clean

- **All 1,132 pass-table cells** (Package A T-B30…T-B6 on S355; SLAB §5 on S235) match the current model within display rounding. T-A (8 thicknesses × 8 quantities), SLAB §4.1, §6.4, §6.5 (friction and emissivity), §6.6 and §2.3 (interpass) all match.
- **RFI basis numbers that match exactly:**
  - Stand RFI: 5.12 MN, 3.48 → 3.5 MN, 218.3 and 120.1 kN·m (10% imbalance).
  - DC RFI: 34 kN·m (loss chain 34.19), 2040 kW, 647 rpm, 2.9 s.
  - Gearbox RFI: ratio 7.1 (snap-down rule), 49–99 rpm output, service factor 2.21, 85–170 reversals/h with 204,000–408,000/yr, and the bite impact 455–682 kN·m.
  - Furnace RFI: 1178 kg, ≈17 slabs/h, ≈212 s.
- **Banner item 1 (T-2 verdict)** and **banner item 4 (325 / 400 / 810 is a rounding difference)** are correct as stated. On the roll-station basis the values are 327.4 / 402.8 / 654.9 / 805.5.
- **T-C loss chain, T-D, T-G, T-2, T-3, T-4 and T-7 spot angles** (646 → 1.51° / 1.26°; 630 → 1.81°; 618 → 2.04°) and the §5.1 values (181–213 MPa, 0.64–1.71 mm, 0.09 mm) are reproduced.
- **The S355 vs S235 transmission is clean.** No S235 number sits under an S355 label in Package A, B, EXEC or the RFIs. The S235 numbers appear only in SLAB §5–7, which the banner covers, and in the explicitly labelled S235 rows (A T-4; B:184).
- **EN/ZH parity:** after digit and CJK normalisation, all four ZH twins carry identical numbers on the same lines. The only differences are the draft-line "5" and enumerator glyphs.
- **Labelling is correct** for every broker or seller CLAIM in the RFIs: 25:1, "center 600", "35 tons" and "3 m × 25 m" are each marked unverified.
- **The ENGINEER_SPEC speed arithmetic** for 1:25 (§3.1) is correct on its stated basis.
