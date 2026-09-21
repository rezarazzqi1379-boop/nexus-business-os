# CHANGELOG — Steel Kernel

## v0.1 — ۲۰۲۶-۰۹-۲۱
- ممیزی ساختار موجود؛ Gap Analysis؛ تصمیم «اشاره کن، کپی نکن»
- `steel_kernel.py`: scope، freshness/TTL، routing، token class، ingestion، preflight
- هشت replay test بند ۱۴
- `CONTEXT_ROUTER` · `FRESHNESS_POLICY` · `TOKEN_BUDGET_POLICY` · `KERNEL` · `CHECKPOINT` · `GAP_ANALYSIS`
- **ساخته نشد:** رجیسترهای jsonl تکراری، knowledge map، lessons register جدا، skill/agent registry — دلیل هرکدام در Gap Analysis
- **وضعیت:** IMPLEMENTED · TESTED · COMMITTED. نه MERGED، نه ACTIVE، نه SCHEDULED.

## 2026-09-21 - Engineer requirement ingested and analysed
- 13 new CLAIMs appended to `initial_claims` (now 30, one append-only array, `_batch` tagged)
- Contradictions C-07 (width set), C-08 (thickness range), C-09 (roll diameter, 4th reading) opened; none of the 6 prior contradictions removed
- `product.target` extended; previous values preserved under `_previous_*` keys
- New intake sections: `layout`, `furnace`, `declared_temperature_profile`
- New module `thermal_and_route_model.py` (+15 tests): transit cooling with Biot validity, feedstock-route mass balance
- `docs/expert_foundry/ENGINEER_REQUIREMENT_ANALYSIS_2026-09-21.md` - 16 deliverables
- KEY FINDING: EN 10058 max nominal width is 200 mm; 300/400/600 mm are outside its scope
- No gate opened. No value silently overwritten. 7 calculations marked STALE.

## 2026-09-21 (2) - Drive-train sizing study
- New module `drive_train_sizing.py` (+31 tests): chain-derived speed/gear/torque/motor sizing
- `docs/expert_foundry/DRIVE_TRAIN_SIZING_STUDY_2026-09-21.md`
- CORRECTION: the 2026-09-19 review called 420 V / 2300 A / 1250 kW impossible. That was
  computed single-phase. Three-phase it implies pf 0.79 and is entirely consistent for a
  wound-rotor machine. Pinned by a regression test. Residual question: 999 rpm is 6-pole
  synchronous speed, so it is likely a no-load/nominal figure, not full-load.
- FINDING: raising the gear ratio 9.8 -> 14 gives +43% torque, zero pass reduction,
  -10% capacity and neck stress 135 -> 206 MPa. Keep 1:9.8 for the 300/400 phase.
- FINDING: 300x8, 300x10 and 400x8 are longer than the 21 m bay and cannot reverse at all.
- FINDING: below ~12 mm the binding speed constraint flips from capacity to thermal.
- FINDING for the 600 mm expansion: D=700 / 800 mm barrel / unchanged 1:9.8 / unchanged
  1250 kW gives the lowest neck stress (119 MPa) and lowest deflection (0.022 mm) of any
  combination tested.
