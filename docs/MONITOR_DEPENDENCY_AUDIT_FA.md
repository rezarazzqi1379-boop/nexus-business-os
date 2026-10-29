# ممیزی وابستگی و تصمیم برش پایش — ۲۰۲۶-۱۰-۲۹

دامنه: `PRJ-NEXUS-SANDBOX`، lane `industrial-tender-pilot`، مبنا
`2143868af6372caa531959dbc883b8e288327b8d`. آخرین main با fetch تأیید شد.
پوشهٔ اصلی روی شاخهٔ پژوهش با تغییرات نامرتبط است؛ کار در worktree جدا انجام شد.
چهار فایل پیش‌نویس پایش در worktree قبلی دیده و در این شاخه بازاستفاده شدند؛
worktree قبلی تغییر نکرد. این فایل‌ها در main موجود نبودند.

## موجودی و تصمیم

`pyproject.toml` فقط FastAPI و uvicorn و ابزارهای توسعه pytest/httpx دارد.
`CommercialRuntime`، `AutonomyStore`، supervisor، `deep_search_fabric`،
`ConnectorControlPlane` و dedup موجود برای این مسیر کافی‌اند.
زمان‌بند یا پایگاه حقیقت جدید ایجاد نشده است.

| گزینه | مجوز و سازگاری | امنیت و هزینه | تصمیم |
|---|---|---|---|
| Crawl4AI | متادیتای upstream: Apache-2.0، Python >=3.10؛ شرط attribution در انتهای LICENSE نیز باید رعایت شود. سازگاری اجرایی Python 3.14 این میزبان آزموده نشده | مرورگر Playwright/Patchright و وابستگی‌های استخراج، سطح حمله و مصرف بیشتر؛ upstream اصلاحات SSRF، نوشتن فایل و XSS را گزارش می‌کند؛ هزینه RAM/دیسک اندازه‌گیری نشده | PROPOSED/DEFERRED؛ JSON ثابت به مرورگر نیاز ندارد؛ نصب نشد |
| dlt | Apache-2.0؛ شاخهٔ devel فعلی Python >=3.10,<3.15؛ این متادیتا نسخهٔ release نصب‌شده نیست | زنجیرهٔ وابستگی، مقصد/credentials/telemetry نیازمند بررسی نسخهٔ pin‌شده؛ مشکل امنیتی مشخصی در این ممیزی اثبات نشده؛ حجم/زمان نصب اندازه‌گیری نشده | PROPOSED/DEFERRED؛ مقصد ETL یا schema evolution در این برش نیاز نیست؛ نصب نشد |
| کتابخانهٔ استاندارد + runtime موجود | با Python پروژه سازگار؛ بدون dependency جدید محصول | HTTPS ثابت، ۳ رکورد، ۶۴ KiB، timeout و بدون redirect؛ هزینهٔ شبکه/بازار در benchmark آفلاین UNKNOWN | SELECTED |

این مقایسه بررسی طراحی است، vulnerability scan کامل یا گواهی بی‌خطر بودن نیست.
نصب فقط ابزارهای لازم آزمون در `.venv` این worktree انجام می‌شود؛ هیچ نصب سراسری،
مرورگر، credential، daemon یا adapter تجاری فعال نمی‌شود.

## شواهد پژوهش

provider: ابزار web؛ تاریخ دریافت ۲۰۲۶-۱۰-۲۹؛ project/lane مطابق بالا.
queryها: `site.github.com/unclecode/crawl4ai license Apache security playwright`
و `site.github.com/dlt-hub/dlt license Apache Python requirements`.
tier: منابع اولیه؛ یافته‌های upstream ادعا هستند و مبنای promotion نیستند.

- https://raw.githubusercontent.com/unclecode/crawl4ai/main/LICENSE
- https://raw.githubusercontent.com/unclecode/crawl4ai/main/pyproject.toml
- https://github.com/unclecode/crawl4ai (توضیحات security release)
- https://raw.githubusercontent.com/dlt-hub/dlt/devel/pyproject.toml
- https://github.com/dlt-hub/dlt

منابع هر محصول از یک مالک هستند؛ corroboration مستقل ادعا نمی‌شود.
این URLها متغیرند؛ پیش از هر نصب آینده باید release، hash، license و advisory همان نسخه منجمد شود.

## اجرای قابل بازتولید

از ریشهٔ worktree، با `PYTHONPATH=src`:

```powershell
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/test_source_monitor.py tests/test_monitor_changes.py tests/test_commercial_pilot.py
.venv/Scripts/python.exe benchmark_source_monitor.py
```

benchmark بیست DB موقت مستقل ایجاد می‌کند و در هر یک tick و replay را اجرا می‌کند.
انتظار: ۲۰ پذیرش، ۲۰ دریافت fixture، صفر اقدام تجاری، حذف تکرار و BASELINE معتبر.
زمان خروجی اندازه‌گیری است و threshold سرعت یا ادعای دقت بازار ندارد.
آزمون تغییرات، changed/added/absence/conflict و baseline خراب/بیگانه/آینده را می‌سنجد؛
آزمون integration، baseline را از checkpoint پایدار قبلی بازیابی می‌کند.

تشخیص تغییرات نمونه‌ای است: absent هرگز removed نیست. منشأ و CLAIM حفظ می‌شوند.
منبع مستقل دوم، فعال‌سازی scheduler و benchmark زنده هنوز انجام نشده‌اند.

نتیجهٔ محیط ایزوله: ۱۸۲۷ آزمون موفق در ۶۴٫۳۱ ثانیه؛ یک هشدار deprecation مربوط به Starlette/httpx. بنچمارک: ۲۰ پذیرش و ۲۰ دریافت fixture در ۱٫۳۵۸۲ ثانیه؛ CPU برابر ۰٫۸۱۲۵ ثانیه. نسخه‌های دقیق و خروجی خام در data/research/monitor-* ثبت شده‌اند. pytest=8.4.2، FastAPI=0.141.1 و httpx=0.28.1 در venv نصب و آزموده شدند. uvicorn برای این مسیر لازم نبود و نصب نشد.
