# CHANGELOG — Steel Kernel

## v0.1 — ۲۰۲۶-۰۹-۲۱
- ممیزی ساختار موجود؛ Gap Analysis؛ تصمیم «اشاره کن، کپی نکن»
- `steel_kernel.py`: scope، freshness/TTL، routing، token class، ingestion، preflight
- هشت replay test بند ۱۴
- `CONTEXT_ROUTER` · `FRESHNESS_POLICY` · `TOKEN_BUDGET_POLICY` · `KERNEL` · `CHECKPOINT` · `GAP_ANALYSIS`
- **ساخته نشد:** رجیسترهای jsonl تکراری، knowledge map، lessons register جدا، skill/agent registry — دلیل هرکدام در Gap Analysis
- **وضعیت:** IMPLEMENTED · TESTED · COMMITTED. نه MERGED، نه ACTIVE، نه SCHEDULED.

## 2026-09-22 - project state reconciled with the slab line
- CHECKPOINT.md carried the billet-line state as current while the slab line had
  been the active project since 2026-09-21. A superseded-warning banner and the
  live slab basis are now recorded.
- docs/system/SYSTEM_AUDIT_2026-09-22.md: measured token accounting for this
  session (41.3M effective), connector audit (2 of ~250 MCP tools used),
  agent/skill/command audit (31 skills, 148 commands, 18 agents unused), and
  the cache-invalidation finding: 39% of cache-write cost followed MCP
  connect/disconnect events for connectors that were never called.
