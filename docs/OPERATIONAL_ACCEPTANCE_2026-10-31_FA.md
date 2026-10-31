# پذیرش عملیاتی محدود NEXUS — ۲۰۲۶/۱۰/۳۱

مرجع فعلی بررسی‌شده: `54e0f8242432fb1b07c54584987c01944d1153a5`، ادغام PR132.
این سند دربارهٔ پایلوت فقط‌خواندنی در PRJ-NEXUS-SANDBOX / industrial-tender-pilot است؛
پذیرش معامله، درآمد یا production نیست. Supervisor، صف AutonomyStore، fencing،
checkpoint، connector preflight، backup و deployment موجود حفظ شده‌اند.

## شواهد main و تناقض‌های قبلی

- اجرای دستی تجاری `41196727036` روی همین SHA موفق شد: یک GET، سه رکورد،
  سه REJECT، صفر فرصت verified/actionable، پوشش فیلدها ۵۰٪، زمان ۰٫۴۲۲۸ ثانیه.
- artifact واقعی `13040538851`، برابر ۴۸۵۳ بایت دریافت شد؛ SHA-256 دقیق ZIP:
  `156f0bd5af17427a11e07bff8536cbc4156c75c4420de40d815c894b4719300b`.
- SHA-256 منبع ۱۴۴۴ بایتی:
  `d6171a43c748b996de6d3d82d4af78560421faf469a5388bd401c4b31bac9a6b`.
- بایت‌های منبع، خلاصه و گزارش اصلی در `data/research/operational-main-20261031/`
  حفظ شده‌اند. بررسی منبع/commit/ارزیابی و گزارش فارسی انجام شد؛ برای اختلاف
  قدیمی float بین Pythonها فقط اعداد float با تحمل صریح 1e-12 مقایسه می‌شوند.
  بایت‌های ZIP و منبع، تصمیم‌ها، هویت‌ها و متن گزارش هیچ تحملی ندارند.
- اجرای تاریخی main پس از PR118، یعنی `40669639630` روی `71c0789` نیز مستقل
  تأیید شد؛ artifact `12806818548` و شواهد آن در
  `data/research/commercial-postmerge-20261028/` حفظ شدند.
- عبارت‌های قدیمی «dispatch در دسترس نیست»، «PR118 ادغام نشده» یا «اجرای main
  انجام نشده» برای این محدوده با شواهد بالا جایگزین می‌شوند؛ تاریخچه حذف نمی‌شود.
- free runtime زمان‌بندی‌شده `41068854309` روی main فعلی startup، readiness،
  health، diagnostics با 401/200 و پژوهش عمومی را تأیید کرد.
- آزمون disposable کانتینر `41197362654` روی main فعلی موفق شد: non-root،
  احراز هویت، restart/volume، checkpoint/replay، backup و restore در مقصد خالی.
  این اجرا host دائمی، disaster recovery خارج از volume یا production نیست.

## نقص‌ها و اصلاح محدود PR133

۱. جایگزینی sidecar بودجه بین دو process، با وجود queue موجود، قبلاً پذیرفته
می‌شد. آزمون قرمز آن را بازتولید کرد. queue اکنون به device/inode و UUID پایدار
ledger متصل است؛ تعویض فایل یا کپی ledger دیگر روی همان inode قبل از HTTP متوقف
می‌شود. این کنترل، مجوز برای تغییر مستقیم SQLite یا مقابله با مدیر مخرب سیستم نیست.

۲. حالت WAL در ledger کوچک رزرو درخواست، الزام rollback-journal را نقض می‌کرد؛
آزمون نشان داد مسیر قبلی همچنان HTTP را اجرا می‌کرد. حالت WAL یا وجود wal/shm
اکنون نیازمند بازیابی صریح است. هیچ WAL حذف یا بی‌اجازه checkpoint نمی‌شود.
این محدودیت مخصوص ledger بودجه است؛ BackupManager موجود برای SQLiteهای دیگر
از backup API استفاده می‌کند و نباید با کپی خام DB جایگزین شود.

۳. جمع float در نسخه‌های Python پشتیبانی‌شده یک اختلاف بسیار کوچک ایجاد کرد.
جمع پایدار `math.fsum` و rounding ثابت برای امتیاز جدید به‌کار رفت. ابزار
`scripts/verify_commercial_artifact.py` ZIP را بدون extract کردن مسیرها بررسی
می‌کند؛ عضو اضافی، hash/commit اشتباه، دستکاری منبع/ارزیابی/گزارش رد می‌شود.
مقایسهٔ عادی دقیق است؛ تحمل legacy فقط از فراخوانی محلی صریحِ verifier با کد
تاریخیِ بازیابی‌شده از commit معلوم امکان دارد، نه از محتوای artifact.

۴. امتیاز یا برچسب ساختگی نمی‌تواند PROCEED ایجاد کند. وضعیت مستقل هویت طرف،
تقاضای جاری، سازگاری فنی، eligibility و امکان تجاری صریحاً UNKNOWN است.
نرخ تأیید خریدار، qualification فنی، feasibility و false-positive تا داشتن
ارزیابی مستقل UNKNOWN می‌مانند. شمار اقدام تأییدشده و نتیجهٔ تجاری صفر است.
کامل‌بودن فیلدها و source screening به معنای تأیید مستقل نیستند.

اصلاحات قدیمی این چت پیش از بازیابی main در stash
`c1074f80086035546bfe44ddd8c1b696ab0d0287` حفظ شدند؛ بخش‌های superseded دوباره
اعمال نشدند. PR119 به بعد قبلاً شمارندهٔ REJECT و امتیاز واژگانی فنی را اصلاح
کرده بودند. نگارش این سند آن کارها را به‌عنوان اصلاح جدید این PR معرفی نمی‌کند.

## آزمون و عملیات واقعی candidate

پیاده‌سازی: `17e543176f90102a72bd2b8c8382427863fcc079`.

```text
python -m pytest -q tests/test_http_attempt_budget.py tests/test_source_monitor.py tests/test_monitor_changes.py tests/test_commercial_pilot.py tests/test_commercial_artifact.py tests/test_router_runtime.py tests/test_public_research_agent.py tests/test_free_research.py
195 passed in 12.77s

python -m pytest -q tests evals
1874 passed, 1 existing Starlette warning in 73.08s
```

دو آزمون اولیهٔ restart replacement و WAL قرمز شدند و سپس سبز شدند. آزمون
rename روی Windows می‌تواند با قفل خود OS متوقف شود؛ اکنون هم WinError32 و هم
رد identity روی Linux با شرط صفر reservation ثبت‌شده بررسی می‌شوند. دو assertion
قدیمیِ PROCEED با قرارداد سخت‌گیرانهٔ جدید ناسازگار بودند؛ انتظارشان به
INVESTIGATE تغییر کرد و unknown risk همچنان REJECT باقی ماند. اجراهای ناموفق
در evidence ثبت می‌شوند، نه اینکه موفق گزارش شوند.

یک tick واقعی روی candidate اجرا شد؛ supervisor پذیرفت. بازکردن مجدد همان صف
و همان bucket درخواست دیگری انجام نداد؛ شمار رزرو پایدار ۱ ماند. integrity_check
هر دو DB برابر ok بود. دادهٔ عمومی tick و replay در evidence ثبت شده‌اند؛ DB،
ledger و snapshot خصوصی artifact عمومی نیستند. CI موجود monitor با تست‌های
بودجه/artifact روی Linux3.11 و Windows3.14 گسترش یافت؛ control plane جدیدی نیست.

CI پیاده‌سازی: commercial `41197506204`، regression `41197506196` و monitor
`41197506206` همگی موفق. monitor روی هر دو سیستم ۱۳۷ آزمون موفق داشت؛ commercial
۱۲۲ آزمون و یک GET واقعی در ۰٫۲۷۴۹ ثانیه انجام داد. artifact `13041555366` با
SHA-256 `93708df6e4a04cd25ea9812963adeb32e45e0136c70064456e91c9283ba50771`
دریافت و این بار بدون هیچ تحمل عددی بازتولید شد؛ منبع با main یکسان بود.
این اختلاف زمان با main، آزمایش کنترل‌شدهٔ سرعت نیست و بهبود عملکرد ادعا نمی‌شود.
head مستندات نیز پیش از پایان جداگانه از CI خوانده می‌شود.

## دادهٔ زنده و محدودهٔ مجاز

تنها منبع زنده همان World Bank عمومیِ قبلی است. metadata آن در config/connectors.json
با binding پروژه/lane، روش GET بدون credential، محدودیت نمونه، quota نامعلوم و
وضعیت EXPERIMENT ثبت شده است. [کاتالوگ رسمی](https://datacatalog.worldbank.org/search/dataset/0037795/world-bank-procurement-notices)
طبقه‌بندی Public و CC BY4.0 را اعلام می‌کند؛ [صفحهٔ تأمین‌کنندگان](https://www.worldbank.org/ext/en/what-we-do/project-procurement/for-suppliers)
API و مسیر فرصت‌ها را معرفی می‌کند. attribution و provenance حفظ می‌شوند.
این صفحات منشأ مستقل از همان آگهی نیستند. منبع دوم، crawling، paid API یا plugin
جدیدی فعال نشد. سند قانونی/تجاری کنترل‌کننده یا supplier واقعی مستقل تأیید نشد.

## پیشنهاد cadence — فعال نشده

پس از پذیرش candidate، ادغام مجاز و اجرای همان نسخه روی main، پیشنهاد اولیه
دو اجرا در هفته (دوشنبه و پنجشنبه، 03:00 UTC / 06:30 تهران)، هر بار یک GET،
حداکثر سه رکورد و شش دقیقه job، artifact هفت‌روزه و مرور انسانی هفته‌ای یک‌بار است.
این فقط پیشنهاد است و به تأیید صریح cadence مالک نیاز دارد؛ cron تجاری اضافه نشد.
اجرای Actions موقت است؛ dedup سراسری و دوام بین دو runner ادعا نمی‌شود.
monitor پایدار مستقل نیز همان cap شش attempt/سه tick/دو attempt در هر tick را
دارد و بعد از آن متوقف می‌شود؛ reset یا rearm خودکار مجاز نیست.

## بازیابی، rollback و موانع

قبل از تغییرات، tick را متوقف کنید. queue و ledger یک جفت شواهد هستند؛ حذف
sidecar، صفرکردن شمارنده یا کپی خام DB باز، بازیابی معتبر نیست. برای queueهای
legacy بدون binding، انتقال host، restore یا WAL غیرمنتظره، پیش از ادامه باید
اپراتور مقصد و بودجهٔ مصرف‌شده را با snapshot تأییدشده تطبیق دهد؛ ابزار حاضر
خودکار binding جدید برای سابقهٔ نامعلوم نمی‌سازد. این تغییر ممکن است availability
queue قدیمی را متوقف کند و عمداً fail-closed است.

Rollback: tick را متوقف، جفت داده را حفظ و PR محدود را revert کنید؛ تنظیمات
production و Docker/Railway موجود تغییر نکردند. نسخهٔ قدیمی حفاظت restart جدید
را ندارد؛ rollback به معنای مجوز ادامهٔ live یا reset بودجه نیست.

HOLD مرجع‌ها پابرجاست. مستقل‌بودن مدارک هویت/تقاضا/فنی/صلاحیت/شرایط معامله،
مجوز هدف production، TLS/secrets، backup خارج از volume، آزمون restore و cadence
هنوز گیت‌های جداگانه‌اند. هیچ ایمیل، تماس تأمین‌کننده، bid، پرداخت، خرید، merge
خودکار یا استقرار production انجام نشد. درآمد و سود بدون تراکنش مستقل نامعلوم‌اند.
