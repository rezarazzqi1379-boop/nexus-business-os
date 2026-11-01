# اصلاح پوشش پشتیبان — ۲۰۲۶/۱۱/۰۱

در تکمیل Universal Activation، نقص واقعی BackupManager پیدا شد: دارایی ثبت‌شده‌ای که فایل یا پوشه‌اش دیگر وجود نداشت، توسط `_expand` به صفر فایل تبدیل می‌شد؛ snapshot ناقص می‌توانست manifest معتبر و نتیجهٔ verify=true داشته باشد.

دو آزمون جدید (فایل و پوشهٔ غایب) پیش از اصلاح شکست خوردند؛ چهار آزمون قبلی پاس بودند. اصلاح کوچک در همان `unified_data_environment.BackupManager.create_snapshot` پس از فیلتر دارایی secret و پیش از expand، نبودن source را با `registered_backup_asset_missing` متوقف می‌کند. مسیر cleanup موجود temporary را جمع می‌کند و snapshot نهایی ناقص منتشر نمی‌شود. هیچ source، asset، ledger یا بودجه reset/حذف نشد. API/schema/محل DB و رفتار backup کامل موجود حفظ شد.

آزمون متمرکز:16 پاس در5.48s؛ فرمان `PYTHONPATH=src;. python -m pytest -q tests/test_unified_data_environment.py tests/test_execution_durability.py tests/test_nexus_system_bootstrap.py`.
رگرسیون کامل:1877 پاس، یک هشدار موجود Starlette در50.87s؛ فرمان `PYTHONPATH=src;. python -m pytest -q tests evals`.
این شاخه از main `e5bc75867ed85fa3869018a578d049bfdb5e57bd` است و اصلاح PR135 را تکرار یا ادغام نمی‌کند؛1877=1875 main+2 fixture جدید. CI دقیق candidate جداگانه بررسی می‌شود.

## بررسی مخزن و بازیابی واقعی

کاتالوگ هاب مهندسی132 دارایی داشت. هنگام حضور در شاخهٔ گزارش Universal تعداد21 و پس از جابه‌جایی به شاخهٔ مستقل اصلاح تعداد30 مسیر در checkout غایب بودند؛ حضور فایل‌های branch-specific فرق می‌کند، دادهٔ ثبت‌شده لزوماً گم نشده است. اجرای BackupManager اصلاح‌شده روی همان هاب واقعاً BLOCK شد و snapshot نهایی `universal-engineering-postfix-20261101` ایجاد نشد.

هر30 مسیر با snapshotهای قبلیِ صحت‌سنجی‌شده یا blob ثابت Git به یک scratch مجزا بازیابی شدند؛ هیچ مسیر زنده overwrite نشد. manifest/commit و SHA256 هر فایل در `data/research/backup-asset-coverage-20261101.json` ثبت است. برای blob Git، بایت commit اثبات شده است؛ اگر digest اولیهٔ catalog موجود نباشد، تطبیق با همان بایت اولیه ادعا نمی‌شود. snapshot کامل لازم بود پیش از استفاده verify شود؛ همهٔ فایل‌های recovered اکنون در scratch با hash قابل بازخوانی‌اند.

این بازیابی scratch، کاتالوگ یا وضعیت checkout اصلی را خودکار تغییر نمی‌دهد. تصمیم دربارهٔ دارایی تاریخی هر branch لازم است: منبع را با نسخه/هش دقیق بازیابی کنید یا کاتالوگ/backup scope را با تصمیم مستند تطبیق دهید؛ asset را صرفاً برای سبزکردن backup حذف نکنید. بازیابی در مسیر اصلی یا retire کردن رکورد، عملیات مستقل با target دقیق و حفظ تاریخچه است. تا آن زمان پشتیبان کامل این هاب باید BLOCK بماند.

snapshot هاب نصب Windows و scratch SQLite restore که در گزارش Universal تأیید شدند، شاهد جدا هستند و این شکست کاتالوگ مهندسی را پنهان نمی‌کنند. نصب محلی از working tree دیگری است؛ اصلاح حاضر هنوز آنجا یا روی main ادغام/فعال نشده است.

Rollback: revert همین guard و دو fixture پس از بازبینی؛ این کار فقط رفتار کد را برمی‌گرداند و نقص silent omission را برمی‌گرداند، پس rollback ایمنی توصیه نمی‌شود مگر برای عیب تأییدشده. هیچ snapshot، scratch یا دادهٔ زنده را ضمن revert حذف نکنید. راه عملی recovery، تکمیل source coverage و اجرای دوبارهٔ همان BackupManager است.

وضعیت: ENGINEERING_VERIFIED محلی؛ merge/deployment نیازمند تأیید دقیق head است. HOLD تجاری، عدم ارسال ایمیل، عدم پرداخت و مرز تولید تغییری نکرده‌اند. گزارش Universal در PR136 و اصلاح selector در PR135 جدا باقی‌اند.
