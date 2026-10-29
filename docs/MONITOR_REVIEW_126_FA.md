# بستن موارد بازبینی PR #126 — ۲۰۲۶-۱۰-۲۹

دامنه: `PRJ-NEXUS-SANDBOX / industrial-tender-pilot`؛ مالک اجرا: Codex.
PR در حالت Draft می‌ماند تا پذیرش نهایی مالک انجام شود. منبع دوم و بودجهٔ
پایدار درخواست‌ها کار بعدی هستند؛ این اصلاح آن‌ها را فعال نمی‌کند.

## ۱. ترتیب و هم‌زمانی checkpoint

مبنای قبلی بر اساس آخرین `seq` انتخاب می‌شد و می‌توانست متعلق به بازهٔ آینده باشد.
اکنون `checkpoint_pair` در یک snapshot خواندن SQLite، checkpoint فعلی و مبنا را
می‌خواند. مبنا باید از همان project، mode و cadence، با شمارهٔ bucket کمتر باشد؛
از میان آن‌ها بالاترین bucket و سپس بالاترین seq انتخاب می‌شود.
فقط checkpointهایی دیده می‌شوند که پیش از seq checkpoint فعلی commit شده‌اند.
این cut-off باعث می‌شود تکمیل دیرهنگام، تاریخچهٔ replay همان نتیجه را بازنویسی نکند.

پس «مبنای قبلی» نزدیک‌ترین بازهٔ قبلیِ تکمیل‌شده و قابل‌مشاهده در زمان ثبت فعلی است؛
تضمین نمی‌شود دقیقاً بازهٔ مجاور باشد. اگر هیچ مبنایی وجود نداشته باشد BASELINE
گزارش می‌شود. observed_at نامرتب همچنان INVALID_BASELINE است؛ CLAIM یا مجوز
اقدام از یک مبنای نامعتبر ساخته نمی‌شود. snapshot فعلی و مبنا با seq و task ID
در خروجی تغییرات قابل ردیابی‌اند.

آزمون‌ها: تکمیل ۱۰/۱۲/۱۱/۱۴ پیش از ۱۳؛ تکمیل دیرهنگام ۱۱ پس از ۱۲ و replay
بدون تغییر؛ دو thread با Event که تکمیل ۱۳ را پیش از ۱۲ تحمیل می‌کنند؛ جداسازی cadence.

## ۲. تغییر ظاهری و محتوایی

فقط bid_description، contact_organization، project_ctry_name و
procurement_method_name برای مقایسهٔ نمایشی با Unicode NFC و یکسان‌سازی فاصله
نرمال می‌شوند. حروف بزرگ/کوچک، علائم، اعداد، تاریخ، شناسه و فیلدهای gate
تغییر داده نمی‌شوند. raw_changed، cosmetic_only و changed جدا هستند؛ cosmetic_only
زیرمجموعهٔ unchanged از نظر این قرارداد محدود است، نه اثبات برابری معنایی.
missing و empty نیز یکی نمی‌شوند. policy با نسخهٔ display-whitespace-nfc-v1 ثبت می‌شود.

داده و SHA اصلی منبع حفظ می‌شوند و نسخه‌های خام متفاوت یک شناسه همچنان conflict
هستند؛ این نرمال‌سازی هرگز assessment یا کنترل مجوز را آسان‌تر نمی‌کند.
آزمون‌ها فاصله، NBSP، Unicode ترکیبی، ترتیب کلیدهای JSON، تغییر عدد/تاریخ/status
و conflict دو نسخهٔ صرفاً ظاهری را پوشش می‌دهند.

## ۳. تطبیق محیط و شواهد بنچمارک

benchmark v2 از fixture ثابت با تاریخ مشخص استفاده می‌کند؛ fixture_sha256 در هر
محیط باید برابر باشد. هدف آن مسیر نرم‌افزاری و replay است، نه تازگی فرصت تجاری.
هر گزارش head، code_matches_head، SHA فایل‌های کد/تست/workflow با پایان‌خط LF،
زمان UTC، OS/release/architecture، Python، SQLite، pytest و شناسهٔ اجرای CI دارد.
گزارش working-tree که code_matches_head=false دارد شواهد exact-head نیست.

CI پذیرش روی Linux/Python 3.11 و Windows/Python 3.14 اجرا و برای هرکدام
benchmark.json، acceptance.xml و environment.txt به artifact همان head متصل می‌کند.
معیار تطبیق: کد و fixture یکسان؛ ۲۰ پذیرش و ۲۰ دریافت، replay بدون دریافت اضافه،
صفر اقدام خارجی، ۱۰۳ آزمون متمرکز موفق. اختلاف latency، OS، patch Python، SQLite
یا dependency footprint عیناً گزارش می‌شود؛ برابری زمان یا سخت‌افزار ادعا نمی‌شود.

محیط هدف فعلی آزمایش Windows 11 / AMD64 / Python 3.14.7 در venv محلی است.
CI Windows صرفاً آزمون سازگاری خانوادهٔ OS/Python است و همان میزبان یا استقرار
production نیست. production_target_verified=false حفظ می‌شود. هیچ هدف production
یا scheduler دائمی در این درخواست تأیید نشده است.

بازتولید در ریشهٔ worktree با PYTHONPATH=src:

```powershell
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/test_source_monitor.py tests/test_monitor_changes.py tests/test_commercial_pilot.py
.venv/Scripts/python.exe benchmark_source_monitor.py --context local --output monitor-evidence/benchmark.json
```

گزارش اولیهٔ نصب در monitor-test-environment-20261029.txt متعلق به venv کامل محلی
است؛ CI متمرکز فقط pytest و وابستگی‌هایش را نصب می‌کند. runtime این برش dependency
جدید ندارد؛ Crawl4AI و dlt نصب یا فعال نشده‌اند. آمار قدیمی ۱۸۲۷/۹۰ و بنچمارک v1
شواهد نسخهٔ قبلی‌اند و نباید به head اصلاح‌شده نسبت داده شوند.
