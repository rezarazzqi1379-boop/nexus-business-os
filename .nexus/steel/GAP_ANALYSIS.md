# Gap Analysis — Kernel در برابر آنچه از قبل وجود داشت
تاریخ ممیزی: ۲۰۲۶-۰۹-۲۱ · پایه: `origin/feat/steel-recovery-v0.1` @ `644f0c7`

## معادل موجود — ساخته نشد (جلوگیری از دو منبع حقیقت)

| خواسته | معادل | چرا کپی نشد |
|---|---|---|
| CLAIM_REGISTER | intake → `initial_claims` | ۱۷ ادعا، append-only، `_batch` دار. گیت `rolling_mill_intake` ادعاهای مبهم را **فقط اینجا** می‌گردد — جداکردنشان قبلاً یک باگ نهفته ساخت (FM در تاریخچه‌ی کامیت). |
| CONTRADICTION_REGISTER | intake → `open_contradictions` | ۶ مورد با evidence class، منبع، و روش حل. |
| SUPERSESSION_LOG | intake → وضعیت ادعاها + `_reconciliation_note` | هر ۹ ادعای ۱۴ سپتامبر با وضعیت صادقانه نگه داشته شده. |
| EVIDENCE_INDEX | intake → `evidence_log` + پوشه‌ی evidence | |
| FAILURE_MEMORY | `.nexus/expert_foundry/registers/ENGINEERING_FAILURE_MEMORY.md` | FM-001 تا FM-004 با تست رگرسیون. |
| SOURCE_REGISTRY · MILL_BENCHMARK | `.nexus/expert_foundry/registers/PRIOR_ART_AND_BENCHMARK_REGISTER.md` | |
| MARKET_EVIDENCE · TECHNOLOGY_RADAR | `.nexus/expert_foundry/registers/TECHNOLOGY_RADAR_AND_MARKET_EVIDENCE.md` | |
| AUTHORITY_MAP | `docs/authority/AUTHORITY_STATUS.md` | تاپل حاکم v1.4+v1.1، با تناقض ثبت‌شده و حل‌نشده. |
| DECISION_REGISTER | `.nexus/memory/decision.jsonl` | موجود، سطح ریپو. |
| EXPERIMENT_REGISTER | اسناد IC-02 v0.1 و v0.2 | هنوز رجیستر مستقل نشده — نیازش ثابت نشده. |
| action gates | `steel_action_gates.py` | دو خروجی + سد داده‌ی منسوخ + ۲۲ تست. |

## شکاف واقعی — ساخته شد

| شکاف | پیاده‌سازی |
|---|---|
| تفکیک محدوده‌ی پروژه | `resolve_scope()` — alias resolution + تشخیص آلودگی بین‌پروژه‌ای |
| تازگی و TTL | `freshness_of()` + `FRESHNESS_POLICY.yaml` |
| مسیریابی قابلیت | `route_request()` + `CONTEXT_ROUTER.yaml` |
| بودجه‌ی توکن | `TokenClass` + `TOKEN_BUDGET_POLICY.yaml` با هزینه‌های واقعی مشاهده‌شده |
| رویداد ورود شواهد | `ingest_new_evidence()` — بند ۷ کامل |
| Preflight | `preflight()` — بند ۳ |
| ظرفیت تخمینی در برابر واقعی | `capacity_statement()` |
| replay tests بند ۱۴ | `evals/test_steel_kernel.py` |
| CHECKPOINT فولاد | `.nexus/steel/CHECKPOINT.md` |

## عمداً ساخته نشد

- **رجیسترهای `.jsonl`** — معادل json/markdown کار می‌کند. تبدیل فرمت بدون نیاز، churn است.
- **`STEEL_KNOWLEDGE_MAP`** — هنوز محتوایی ندارد که در KERNEL.md نباشد.
- **`LESSONS_LEARNED` جدا** — FM-004 تنها درس ارتقایافته است و در failure memory زندگی می‌کند. رجیستر خالی، بوروکراسی است نه ساختار.
- **`SKILL_AGENT_REGISTRY.yaml`** — `.claude/agents/` خودش رجیستر است.
