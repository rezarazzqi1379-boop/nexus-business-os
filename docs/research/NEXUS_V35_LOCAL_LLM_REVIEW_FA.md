# NEXUS v3.5 — بازبینی امنیت و manifest آزمایش محلی

مبنای مستقل: `5a2c36c2820b4e3840558ce67ed84a87bb2420a7`.
شاخهٔ بررسی: `codex/local-llm-manifest-review-2026-10-15`.
این مرحله فقط بررسی، آزمون و آماده‌سازی است؛ دانلود مدل/runtime، نصب و اجرای LLM
هنوز مجاز یا انجام‌شده نیست. پلتفرم نصب‌شده و production تغییر نکردند.

## شواهد مستقل و وضعیت مرجعیت

آزمون کامل قبلی مستقل اجرا شد: **۱۶۸۷ موفق، ۶۹٫۹۰ ثانیه** و یک warning
upstream مربوط به Starlette/httpx. لاگ تازه در `data/research/v35-independent-tests.txt`.
پنج آزمون مقابله با پنهان‌سازی secret اضافه شد؛ آزمون متمرکز دو فایل: **۳۲ موفق**.
نتیجهٔ اجرای کامل نهایی و هش لاگ در `data/research/v35-verification.json` ثبت می‌شود.
دستورات واقعی:

```text
python -m pytest -q -p no:cacheprovider --basetemp <writable>/data/research/pytest-v35-independent tests evals
python audit_v35_evidence.py
python -m pytest -q -p no:cacheprovider --basetemp <writable>/data/research/pytest-v35-adversarial tests/test_evidence_digest_review.py tests/test_public_research_agent.py
python -m pytest -q -p no:cacheprovider --basetemp <writable>/data/research/pytest-v35-full-final tests evals
git diff 5a2c36c -- coordination_kit.py
```

Drive دوباره با دو query محدود برای Source Registry/Master جست‌وجو شد. handoff
به‌روز و Steel Intelligence Master v0.1 mirror خوانده شدند. handoff همچنان
hash/binary/supersession مرجع را حل‌نشده می‌داند؛ mirror صریحاً PROPOSED DESIGN است.
فایل‌های پذیرفته‌شدهٔ Registry v1.8/Master v2.1 در این جست‌وجوی محدود بازیابی نشدند؛
این نتیجه اثبات نبودن آن‌ها نیست. شناسهٔ پروژهٔ تجاری فولاد همچنان provisional؛
فقط `PRJ-NEXUS-SANDBOX` استفاده می‌شود. bootstrap تازه باید BLOCK بماند.
منابع: handoff `1bJyokT1ORCn5agELPcOR2s7u0ddJeBdt6ihSsJb7uNI`، mirror
`1Y9SvY8S4h_DOnSt0AYVhk8IzBlhafglCbNSd1Aukojo`.

## نتیجهٔ بازبینی امنیت

اسکن Codex Security با شناسهٔ `8ec71d27-7da4-4aae-b6a2-d98b41a9d2aa` روی
diff ثابت `127edca..5a2c36c` تکمیل و sealed شد: ۱۰ مورد inventory بررسی شد؛
بای‌پس امنیتی جدیدِ قابل‌گزارش در این diff پیدا نشد. scope و exclusions همان
گزارش canonical هستند؛ این نتیجه audit کامل مخزن یا تأیید binary آینده نیست.
گزارش canonical در مسیر برگشتی plugin نگهداری می‌شود و این سند جایگزین آن نیست.

`audit_v35_evidence.py` هر **۱۹ تطابق اصلی** را با منشأ مستقل ثبت کرد: بایت‌های
منبع، file manifest، evidence hashes یا manifest کانونی submission. سه نمایش
CRLF از blob اصلی و map ثبت‌شده بازسازی شدند؛ شواهد اصلی بازنویسی نشدند.
خروجی: `data/research/v35-nineteen-finding-audit.json`.

نکتهٔ اساسی: تطابق SHA-256 فقط تمامیت را ثابت می‌کند، نه پاک‌بودن متن از secret.
آزمون‌های جدید bodyهای مصنوعی با شکل credential و hash درست را ساختند: diagnostic
می‌تواند hash را توضیح دهد، ولی محافظ هنوز BLOCK می‌کند؛ password-context نیز
همچنان تشخیص داده می‌شود. هیچ global whitelist، حذف finding یا ALLOW اضافه نشد.
Secret Guard و ownership/approval gates بدون تغییرند. هیچ تضمین عمومی دربارهٔ
تشخیص همهٔ secretها یا همهٔ encodingها داده نمی‌شود. diagnostic نباید به مجوز تبدیل شود.

پیش‌نیاز ابزار امنیتی با یک worker فقط‌خواندنی اجرا شد و ready بود؛ تنظیمات تغییر نکرد.
ابزار Daybreak را برای این حساب not_granted گزارش کرد؛ محدودیت نمایش خروجی محافظت‌شده
ممکن است وجود داشته باشد. تله‌متری completion ابزار، محدودهٔ codex_rollout دو thread:
totalTokens=3094473، inputTokens=3086565، cachedInputTokens=2995584.
این اعداد مصرف گزارش‌شدهٔ ابزارند، نه هزینه یا توکن inference مدل محلی یا برآورد
مصرف افزایشی فقط این مرحله. مصرف inference این مرحله صفر است؛ هزینهٔ پولی جلسه
از این اعداد محاسبه نشده است.

## artifactهای دقیق؛ هنوز candidate

manifest ماشین‌خوان: `data/research/v35-local-llm-manifest.json`.
فرادادهٔ رسمی، license و CLI source محدود خوانده شد؛ وزن یا executable دانلود نشد.

مدل ناشر رسمی `Qwen/Qwen3-0.6B-GGUF`:

- revision: `23749fefcc72300e3a2ad315e1317431b06b590a`
- فایل: `Qwen3-0.6B-Q8_0.gguf`؛ اندازه: **639446688 bytes**
- SHA-256 ناشر: `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`
- Apache-2.0؛ ungated طبق API رسمی؛ متن LICENSE از همان revision خوانده و hash شد.

runtime رسمی `ggml-org/llama.cpp`:

- tag: `b11429`؛ commit: `d81235049384534c167caea52b85a694f6103d14`
- asset ID: `613152134`؛ فایل: `llama-b11429-bin-win-cpu-x64.zip`
- اندازه: **19398918 bytes**
- SHA-256 ناشر: `1283323272b04cd07905816a597a0da810918102de958f4ff6f7bbaa70ed2efe`
- MIT؛ license از commit ثابت خوانده و hash شد.

این SHAها از publisher metadata هستند؛ تا پس از تأیید و دانلود، hash خود فایل
محلی VERIFIED نیست. اصل Apache/MIT و noticeها باید همراه artifact بماند؛ این
بررسی حکم کلی حقوقی برای هر کاربرد یا توزیع نیست. latest release یک pointer متنی
به nightly بود؛ tag ثابت از pointer بازیابی و مستقل با release API حل شد.
manifest به latest متحرک وابسته نیست.

## سازگاری، منابع و حریم خصوصی

probe تازه: RAM حدود 15.64GiB، CPU i5-13420H با ۸ core/۱۲ logical، RTX4050
با **6141MiB** طبق NVIDIA؛ حدود **35GB فضای آزاد** روی C در زمان probe.
WMI VRAM قابل‌اعتماد تلقی نشد. Python پروژه **3.14.7** است. runtime منتخب native
CPU است؛ وابسته به wheelهای torch/transformers یا ABI پایتون نیست. حضور DLLهای
VC runtime بررسی شد؛ نبود dependency دیگر و سلامت binary فقط پس از دانلودِ مجاز
و بررسی archive/smoke test قابل‌تأیید است. هیچ runtime/model حاضر تأییدشده‌ای فرض نشد.

بودجهٔ پیشنهادی، هنوز اجرا/اندازه‌گیری نشده:
concurrency=1، threads=4، context=2048، output<=128، GPU layers=0، هر process<=120s،
کل benchmark<=1200s، حداکثر ۸ case و ۲ replay recovery، RSS cap=4GiB، حداقل
۶GiB RAM آزاد پیش از اجرا و ۳GiB فضای دیسک آزاد. مقدار model file حدود 610MiB است؛ RSS کل شامل cache/buffers
نامعلوم است و باید اندازه‌گیری شود. VRAM برای CPU-only باید نزدیک صفر باشد،
اما اندازه‌گیری انجام نشده است. هزینهٔ API/provider هدف صفر؛ برق/دانلود/زمان
ماشین رایگان فرض نشده و اندازه‌گیری نشده‌اند.

فقط fixture عمومی ذخیره‌شده، بدون private chat یا credentials؛ CLI محلی با
`--offline`، بدون server/HTTP listener، بدون tool/shell delegation، بدون telemetry
مجاز یا promotion تجاری. وجود flagها در `common/arg.cpp` همان commit بررسی شد؛
پشتیبانی binary و رفتار واقعی هنوز smoke-test نشده‌اند. اگر timeout، محدودیت RSS،
عدم شبکه یا محیط پاک قابل‌تأیید نباشد، آزمایش باید BLOCK شود؛ firewall/access
سیستم نباید برای ادامه تغییر کند.

## مراحل پس از تأیید دقیق؛ اکنون اجرا نشوند

محیط محدود:
`C:/Users/AvallPc/.codex/worktrees/8cdc/nexus-business-os/data/local-llm-experiments/v35-qwen-cpu`

1. فقط دو URL ثابت manifest را در همین پوشهٔ disposable دریافت کنید؛ هیچ global
   PATH، registry، سرویس، task زمان‌بندی‌شده یا package پایتون تغییر نکند.
2. پیش از اجرا، اندازه و SHA256 دو فایل را با manifest مقایسه کنید؛ mismatch => STOP.
3. archive را از نظر traversal، absolute path، reparse/symlink و expansion بررسی
   کنید؛ حداکثر ۵۱۲MiB مجموع استخراج و ۱۰۰۰ entry. فقط داخل `runtime/` استخراج شود.
4. license/notice حفظ شود؛ dependencyها و `llama-cli.exe --version` در sandbox
   بدون دسترسی network/credential بررسی شوند. شکست => BLOCK، نه نصب dependency تازه.
5. یک adapter محدود از hookهای موجود Router با action جدا، project SANDBOX،
   lease/checkpoint/Supervisor موجود و argv ثابت ساخته شود؛ queue/DB جدید نسازید.
6. نمونهٔ argv، پس از تطبیق نسخه و safety boundary:

```text
llama-cli.exe --offline --no-conversation --model <pinned-model.gguf> --ctx-size 2048 --n-predict 128 --threads 4 --n-gpu-layers 0 --seed 42 --temp 0 --file <public-fixture.txt>
```

مدل نباید مستقیم اقدام کند؛ پاسخ generated CLAIM است. خروجی JSON ساختاریافته
و ارجاع منبع باید از validatorهای مستقل بگذرد. صحت پاسخ LLM را خود LLM داوری نکند.
RSS با Windows Job Object یا مکانیزم موجودِ قابل‌تأیید محدود شود؛ process tree در
timeout بسته شود؛ خروجی و stderr محدود و secret-safe باشند. اگر این کنترل‌ها آماده
نیستند، inference شروع نشود.

## طرح سنجش و rollback

از همان شواهد عمومی frozen پژوهشگر قطعی استفاده شود. ۸ case از پیش frozen:
facts قابل‌استخراج، شاهد ناکافی، تعارض، سند stale، entity غلط، prompt injection،
query نامرتبط و evidence tampering. rubric پیش از اجرای مدل ثبت شود: field exact
match، citation binding، unsupported-claim rate، abstention و acceptance gate.
مقایسه با baseline قطعی با ورودی/بودجهٔ یکسان؛ latency شبکه با inference مخلوط نشود.
wall time، CPU، peak RSS، VRAM delta، token count و دو restart/replay اندازه‌گیری شوند.
فعلاً همهٔ نتایج LLM **NOT_RUN** هستند؛ دادهٔ ساختگی یا benchmark فرضی وجود ندارد.

Rollback: فقط processهای همین آزمایش متوقف شوند؛ پس از بررسی resolved path در
همین پوشهٔ disposable، artifactهای آزمایش پاک شوند؛ شواهد و queue audit حفظ شوند.
restoration یا حذف production، محیط Python اصلی یا global config مجاز نیست.

## مجوز لازم

تأیید باید دقیقاً شامل **همین revision/asset/hashها، همین پوشه، دریافت و استخراج
موقت و یک آزمایش CPU-only فقط‌خواندنی با حدود بالا** باشد. تأیید publication،
merge، deploy، پرداخت، سرویس دائمی، credential یا permission change نیست.
بدون این تأیید، دانلود/نصب/inference متوقف می‌مانند؛ کار امن این مرحله کامل است.
