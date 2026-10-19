# NEXUS — کشف و رفع کمبودهای قابلیت اطمینان

مبنا: `690b9c84c21f7380f51345d34e63726578a3cb77`؛ شاخهٔ محلی
`codex/reliability-gaps-2026-10-18`. scope این چرخه: Router، صف/مالکیت شکست،
پژوهشگر عمومی و maintenance preflight. این یک audit کامل همهٔ سورس‌ها، پروژه‌ها
یا ضعف‌های عمومی مدل نیست؛ قسمت‌های بررسی‌نشده همچنان UNKNOWN هستند.

## یافته‌های بازتولیدشده و اصلاح

**GAP-RUNTIME-01:** خطای execute یا validation در drain از worker خارج می‌شد،
صف را قطع می‌کرد و lease تا expiry باقی می‌ماند؛ کارهای سالم مستقل هم اجرا نمی‌شدند.
اصلاح: ثبت شکستِ redacted، آزادسازی lease و retry با backoff و سقف موجود؛
ادامهٔ کارهای مستقل. API `drain` همچنان تعداد کارهای کامل‌شده را برمی‌گرداند؛
برای علت شکست باید journal/snapshot دیده شود. دیگر نباید صرف نبود exception را
به معنی کامل‌شدن همهٔ کارها گرفت. هیچ exception/body ارائه‌دهنده وارد journal نمی‌شود.

**GAP-RUNTIME-02:** adapter مسیر شکستِ attempt-fenced نداشت. اکنون `fail` از همان
project/action/owner/attempt/expiry fence مسیر finish استفاده می‌کند. stale owner،
owner با attempt قدیمی، lease منقضی و cancellation اجازهٔ overwrite ندارند.
failure event و تغییر صف در یک transaction‌اند؛ شکست journal هر دو را rollback می‌کند.
صف/DB جدید ساخته نشد. backoff مطابق صف موجود: ۳۰،۶۰ ثانیه و dead-letter پس از
رسیدن به max_attempts. لغو/stop/reclaim بر ثبت شکست worker قدیمی مقدم است.

**GAP-METADATA-01:** JSON خراب، array به‌جای object یا فایل بسیار بزرگِ approval/
manifest می‌توانست preflight را crash کند یا به‌عنوان metadata سالم نمایش داده شود.
اصلاح: خواندن حداکثر 128KiB، بررسی JSON object و نتیجهٔ BLOCK برای خطا؛ هیچ مقدار
داخل JSON به approval واقعی تبدیل نمی‌شود. فایل v35 approval/manifest اصلی تغییر نکرد.

**GAP-INVENTORY-01:** یک SKILL ناخوانا می‌توانست inventory سالمِ بقیه را متوقف کند؛
فایلِ رشدکرده بعد از stat نیز بدون bound واقعی خوانده می‌شد. اصلاح: read محدود،
وضعیت NOT_READ_IO_ERROR یا NOT_READ_SIZE_LIMIT؛ خواهرهای سالم بررسی می‌شوند.
متن exception خروجی نمی‌شود؛ hash ناقص به‌عنوان hash کامل ثبت نمی‌شود. coverage
صریحاً «فایل‌های enumerate‌شده» است، نه اثبات نبود مسیرهای غیرقابل‌دسترسی.

## شواهد و سنجش

پیش از ویرایش، آزمون‌های موجود مرتبط **۴۵ موفق** بودند. هفت آزمون تازه روی کد
قبلی اجرا و **هفت failure** بازتولید کردند: سه کمبود runtime و چهار حالت metadata.
لاگ red حفظ شد. پس از اصلاح و افزودن تست‌های expiry/atomic journal/skill IO،
**۵۷ آزمون مرتبط موفق** شدند؛ یک warning upstream. نتیجهٔ full در verification.

```text
python -m pytest -q tests/test_router_runtime.py tests/test_public_research_agent.py tests/test_maintenance_preflight.py
python -m pytest -q tests/test_router_runtime.py tests/test_maintenance_preflight.py
python -m pytest -q tests/test_router_runtime.py tests/test_public_research_agent.py tests/test_maintenance_preflight.py tests/test_router_console.py
python benchmark_router_failure_isolation.py --output data/research/reliability-gaps-benchmark-2026-10-18.json
python -m pytest -q tests evals
```

در اجراهای واقعی pytest، `-p no:cacheprovider` و `--basetemp` داخل writable workspace
استفاده شد؛ Python همان `C:/Users/AvallPc/nexus-business-os/.venv/Scripts/python.exe`،
PYTHONPATH=src بود. هیچ package یا مدل نصب نشد.

بنچمارک ده‌تایی paired با source دقیق commit قبل از اصلاح و همین ورودی مصنوعی:
یک worker در task خراب خطا می‌دهد و task سالم بعد از آن در صف است. تکمیل task
سالم: baseline **۰/۱۰**، اصلاح‌شده **۱۰/۱۰**. baseline صف را abort می‌کند؛ اصلاح‌شده
هر بار یک failure event ثبت می‌کند و پنج child سالم/مستقل را کامل می‌کند.
میانهٔ زمان baseline **0.00382485s** و اصلاح‌شده **0.042913s**؛ این افزایش طبیعی است،
چون مسیر اصلاح‌شده کار بیشتری انجام می‌دهد. ادعای speedup یا reliability اینترنت
وجود ندارد. همهٔ faultها مصنوعی‌اند؛ model/API calls و هزینهٔ provider صفر.

## ثبت ضعف‌ها و سازگاری عامل

دفتر ماشین‌خوان: `data/research/reliability-gaps-register-2026-10-18.json`؛ برای هر
مورد status، نوع شاهد، acceptance check، مانع و next action ثبت شده است.
مورد اصلاح‌شده به معنی promote شدن به production نیست؛ remote CI جدید اجرا نشده.

کمبود فرایند خودِ عامل: آزمون‌های قبلی مسیرهای عادی/کرش را پوشش می‌دادند، ولی
execute failure همراه با کار مستقل و metadata خراب را به‌اندازهٔ کافی نمی‌سنجیدند.
این ادعا از red fixtures همین چرخه می‌آید، نه ارزیابی کلی «هوش» عامل یا مالک.
adaptation پیشنهادی: پیش از ادعای worker durability، fault injection و throughput
کارهای سالم، failure accounting، malformed inputs و rollback مشترک بررسی شود.
این چرخهٔ اصلاح‌شده PARTIAL است؛ قانون global، skill یا policy از آن خودکار منتشر نشد.

موارد باقی‌مانده: Registry/Master HOLD، approval دقیق دانلود/آزمایش LLM، عدم
اثبات secret-free بودن از روی digest، رفتار provider واقعی در اختلال، gapهای
coverage سراسری، و collision مهارت Notion. این‌ها بدون شاهد به «رفع‌شده» تبدیل نمی‌شوند.
نصب framework بیشتر یا حذف فایل‌های مالک راه‌حل خودکار این کمبودها نیست.

## مرزها و rollback

Secret Guard، ApprovalStore و acceptance gates تغییر نکردند؛ هیچ external action،
پرداخت، publication، deployment یا credentials تغییر نکرد. شکست acquisition اکنون
در صف queued/dead_letter و journal دیده می‌شود؛ crash واقعیِ process همچنان از lease
expiry بازیابی می‌شود. exactly-once برای عملیات خارجی ادعا نمی‌شود.
Rollback: revert commit محلی و اجرای همین تست‌ها؛ audit داده‌ها حذف نشوند. کاربران
قدیمی که exception از drain را سیگنال می‌دانستند باید اکنون وضعیت صف را بررسی کنند.
