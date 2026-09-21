# NEXUS Persistent Steel Kernel — v0.1

**project_id:** `rolling_mill_strip_300_pilot` · **alias:** `PRJ-STEEL-ROLLING-LINE-01`
**وضعیت: IMPLEMENTED · TESTED · COMMITTED — نه MERGED، نه ACTIVE، نه SCHEDULED.**

## اصل طراحی: این Kernel اشاره می‌کند، کپی نمی‌کند

ممیزی ۲۰۲۶-۰۹-۲۱ نشان داد بیشتر رجیسترهایی که این دستور می‌خواهد **از قبل با نام دیگری وجود دارند**. ساختن نسخه‌ی دوم، دقیقاً همان خطایی است که این Kernel قرار است جلویش را بگیرد: دو منبع حقیقت.

پس Kernel فقط **مسیریابی، سیاست و بررسی** را نگه می‌دارد و برای داده به این‌ها اشاره می‌کند:

| خواسته‌ی دستور | معادل موجود — همین حاکم است |
|---|---|
| CLAIM_REGISTER | `ROLLING_MILL_ENGINEERING_INTAKE.json` → `initial_claims` (۱۷ ادعا، append-only، با `_batch`) |
| CONTRADICTION_REGISTER | همان فایل → `open_contradictions` (۶ مورد) |
| SUPERSESSION_LOG | همان فایل → وضعیت ادعاها + `_reconciliation_note` |
| EVIDENCE_INDEX | همان فایل → `evidence_log` + `docs/expert_foundry/evidence/` |
| FAILURE_MEMORY | `.nexus/expert_foundry/registers/ENGINEERING_FAILURE_MEMORY.md` |
| SOURCE_REGISTRY · MILL_BENCHMARK | `.nexus/expert_foundry/registers/PRIOR_ART_AND_BENCHMARK_REGISTER.md` |
| MARKET_EVIDENCE · TECHNOLOGY_RADAR | `.nexus/expert_foundry/registers/TECHNOLOGY_RADAR_AND_MARKET_EVIDENCE.md` |
| AUTHORITY_MAP | `docs/authority/AUTHORITY_STATUS.md` |
| PROJECT_STATE | `.nexus/state/CURRENT_STATE.md` (کل ریپو) + `CHECKPOINT.md` (فولاد) |
| action gates | `steel_action_gates.py` |
| سد داده‌ی منسوخ | `steel_action_gates.detect_obsolete_values()` |

**رجیسترهای jsonl خواسته‌شده ساخته نشدند** چون معادل‌شان markdown/json است و کار می‌کند. تبدیل فرمت بدون نیاز، churn است نه بهبود.

## آنچه واقعاً تازه است

`steel_kernel.py` — محدوده‌ی پروژه، تازگی و TTL، مسیریابی قابلیت، بودجه‌ی توکن، رویداد ورود شواهد، و بررسی‌های fail-loud.

## Preflight

پیش از هر پاسخ مرتبط با فولاد: `preflight(request_text, kind, intake, retrieved)`.

سبک است — فقط چیزی را می‌خواند که مسیر لازم دارد، نه کل تاریخچه. **خودش را به کاربر نشان نمی‌دهد** مگر مانع یا داده‌ی STALE پیدا کند.

## دو واژگان که هرگز مخلوط نمی‌شوند

**معرفتی:** FACT · MEASUREMENT · CLAIM · ESTIMATE · ASSUMPTION · HYPOTHESIS · UNKNOWN
**اجرایی:** DESIGNED · IMPLEMENTED · TESTED · COMMITTED · PUSHED · MERGED · DEPLOYED · ACTIVE · PRODUCTION-VERIFIED

یک تست این تفکیک را قفل می‌کند.

## rollback

`steel_kernel.py` و `evals/test_steel_kernel.py` و `.nexus/steel/` را حذف کنید. هیچ فایل دیگری تغییر نکرده.
