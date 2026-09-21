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
