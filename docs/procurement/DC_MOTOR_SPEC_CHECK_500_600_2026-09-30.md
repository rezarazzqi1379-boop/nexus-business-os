# DC motor spec check: 1-2.5 MW at 500-600 rpm vs the slab-line model (2026-09-30)

Owner's spec (CLAIM, from chat): 1, 1.5, 2 or 2.5 MW; 500 or 600 rpm. Checked against
`slab_line_design.build_dc_option` / `dc_motor_feasibility` (roll Ø600 mm, 3 m/s line speed,
all eight targets 30-6 mm, three friction scenarios). Pinned by `evals/test_dc_motor_spec_500_600.py`.

Basis printed, per FM-009: 500/600 rpm read as BASE speed; field weakening 2:1 (ASSUMPTION, typical
mill DC; МПЭ-1000 is 630/1000 = 1.59:1 from its nameplate CLAIM); short-time overload 2.0x
(model default) with a 1.5x sensitivity for older used motors.

## Result

| Motor | Gearbox | Balanced, 2.0x | Aggressive, 2.0x | Balanced, 1.5x | Aggressive, 1.5x |
|---|---|---|---|---|---|
| 1000 kW 600/1200 (Z710-1B) | 12.5 | OK, worst +18% | FAILS 20-30 mm (−22%) | −12% | −41% |
| 1120 kW 630/1000 (МПЭ-1000) | 10.0 | OK, +32% | FAILS 30 mm (−13%) | −1% | −34% |
| 1500 kW 500/1000 | 10.0 | OK, +77% | OK, +17% | +33% | −12% |
| 1600 kW 500/1000 (Z800-6B, rpm ASSUMED) | 10.0 | OK, +89% | OK, +25% | +42% | −6% |
| 2000 kW 500/1000 | 10.0 | OK, +136% | OK, +56% | +77% | +17% |
| 2500 kW 600/1200 | 12.5 | OK, +195% | OK, +95% | +121% | +46% |
| Package A reference 1600 kW 350/700 | 7.1 | OK, +89% | OK, +25% | — | — |

If 600 rpm is the TOP speed (no field weakening), the gearbox drops to 5.6:1 and 1600 kW fails the
aggressive case on every target (−1% to −8%); 2500 kW passes.

## What this means

1. The spec is **compatible** with the line, but it **changes the gearbox**: 10:1 for a 500 rpm base,
   12.5:1 for 600 rpm, instead of 7.1:1 (Package A) or the engineer's 1:25 (FM-009 context). A gearbox
   RFI must be issued with the motor actually bought, never before.
2. **1 MW is marginal**: it passes only the balanced case at the full 2.0x overload. Do not buy a
   1 MW unit unless the pass schedule is limited to ≤15 mm entry or the motor's overload rating is
   documented at 2.0x or better.
3. **1.5-1.6 MW is the sensible floor**; 2 MW is the robust choice: it passes every case,
   including aggressive at 1.5x overload. 2.5 MW adds margin mostly spent on idle losses and price.
4. The hidden constraint most likely to invalidate this (Shadow Scientist): the used motor's real
   overload capability and armature condition. Ask for the nameplate, the overload class and an
   insulation/commutator report before price talks.

Thermal (RMS) duty is not checked here; `torque_chain` does it once a real motor and duty cycle are fixed.
