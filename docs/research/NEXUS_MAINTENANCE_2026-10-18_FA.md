# نگه‌داری محدود NEXUS — ۱۸ اکتبر ۲۰۲۶

مبنا: `1afa2c53e4ad81f625023d02b36d93b9b46aaab1`؛ شاخهٔ محلی
`codex/maintenance-preflight-2026-10-18`. سورس‌ها و مهارت‌ها از همان وضعیت ادامه
یافتند؛ تغییرات worktreeهای دیگر حفظ شد. هیچ حذف عمومی یا ارتقای خودکار dependency
انجام نشد. manifest مدل قبلی تغییر نکرد و هنوز تأیید دقیق دریافت/اجرای آن موجود نیست.

## نتیجهٔ قابل‌استفاده

اضافه شد: `maintenance_preflight.py` و wrapper پاورشل
`scripts/nexus_maintenance_preflight.ps1`. این مسیر فقط‌خواندنی است: inventory
مهارت‌ها، تفاوت نسخه‌های هم‌نام، مسیر ابزارها، budget تخصیصی و تمامیت manifest
pending را گزارش می‌کند؛ هیچ نصب/حذف، اجرای دستورِ متن مهارت، احراز credential،
تغییر permission یا اعطای approval ندارد. از allocator و project_control_plane
موجود استفاده می‌کند؛ control plane/DB جدید نیست.

آزمون‌ها تفاوت نسخهٔ مهارت، dedup مسیر، محدودیت inventory و جعل approval metadata
را پوشش دادند: حتی `authorization_received=true` در فایل JSON باعث مجوز نمی‌شود؛
تغییر بایت manifest => BLOCK_MANIFEST_DRIFT. Secret Guard و hold مرجعیت دست‌نخورده‌اند.

## بررسی واقعی محیط

Wrapper در PowerShell موجود اجرا شد، با Python پروژهٔ
`C:/Users/AvallPc/nexus-business-os/.venv/Scripts/python.exe`. پنج ریشه بررسی شد:
`.agents/skills` همین checkout، مهارت‌های محلی مالک، cacheهای bundled/curated و
primary-runtime. **۱۳۶ فایل SKILL.md** دیده شد؛ سقف ۲۰۰ به پایان نرسید. این عدد
inventory فایل‌هاست، نه تعداد pluginهای authenticated، loaded یا active. سلامت
connectorها probe نشد و UNKNOWN/NOT_PROBED باقی است. فقط متن مهارت هش شد؛ متن خام
یا تاریخچهٔ خصوصی چت در گزارش export نشد. ابزارهای pwsh/powershell/git/rg پیدا شدند.

یک collision نام مشترک با تفاوت محتوا دیده شد:
`notion-research-documentation` در skill محلی و plugin Notion 3.0.1. این تفاوت
به‌تنهایی اثبات خراب‌بودن نسخه نیست. تصمیم نگه‌داری: در کارهای NEXUS نام qualified
`notion:notion-research-documentation` و مسیر plugin مربوط را صریح resolve کنید؛
skill محلی مالک بدون بررسی کاربردهایش حذف یا بازنویسی نشود. فایل‌های عمومی plugin
تغییر نکردند. این تصمیم global routing سایر برنامه‌ها را تنظیم نمی‌کند.

## منابع جاری GitHub

دو API رسمی عمومی در ۲۰۲۶-۱۰-۱۸ تازه‌سازی شد؛ URL، query، زمان و hash در
`data/research/maintenance-source-refresh-2026-10-18.json` ثبت شده است:

- `ggml-org/llama.cpp`: not archived، MIT؛ pushed_at برابر 2026-10-18T08:48:15Z.
- `QwenLM/Qwen-Agent`: not archived، Apache-2.0؛ pushed_at برابر 2026-03-04T08:15:07Z.

این‌ها CLAIM فرادادهٔ ناشرند؛ اثبات امنیت، برتری یا آمادگی نصب نیستند. source رسمی
انتخاب شد، نه fork یا mirrorهای نتایج جست‌وجو. انتشارهای جاری llama.cpp نیز مرور
شدند: https://github.com/ggml-org/llama.cpp/releases . هیچ artifact پین‌شده‌ای با
latest جایگزین نشد. framework جدید بدون benchmark و approval نصب نمی‌شود.
remote refs خود NEXUS نیز fetch شد؛ HEADهای مشاهده‌شده در verification ثبت می‌شوند.

## دستورات و شواهد

```powershell
$env:PYTHONPATH = 'src'
& 'C:/Users/AvallPc/nexus-business-os/.venv/Scripts/python.exe' -m pytest -q -p no:cacheprovider --basetemp <writable>/data/research/pytest-maintenance-focused tests/test_maintenance_preflight.py
& './scripts/nexus_maintenance_preflight.ps1' -PythonPath 'C:/Users/AvallPc/nexus-business-os/.venv/Scripts/python.exe' -SkillRoots @('.agents/skills','C:/Users/AvallPc/.codex/skills','C:/Users/AvallPc/.codex/plugins/cache/openai-bundled','C:/Users/AvallPc/.codex/plugins/cache/openai-curated-remote','C:/Users/AvallPc/.codex/plugins/cache/openai-primary-runtime')
& 'C:/Users/AvallPc/nexus-business-os/.venv/Scripts/python.exe' -m pytest -q -p no:cacheprovider --basetemp <writable>/data/research/pytest-maintenance-full tests evals
```

متمرکز: **۳ موفق**؛ کامل: **۱۶۹۵ موفق، ۴۰٫۶۳ ثانیه**، یک warning upstream.
PowerShell wrapper هم واقعاً اجرا شد. inventory، لاگ، hash فایل‌ها و verification
کنار گزارش ثبت شدند. تخصیص allocator: history1000/evidence2500/working7000/output1500؛
مصرف واقعی کل جلسه UNKNOWN است. هیچ inference/API مدل یا خرید انجام نشد.

## مرز و rollback

این مرحله ابزار بررسی سراسریِ محدود و قابل‌تکرار را فراهم می‌کند؛ ادعای اصلاح همهٔ
پروژه‌ها، فعال‌سازی تمام چت‌ها یا دسترسی نامحدود ندارد. اتصال جدید حساب، مهارت/plugin
جدید، حذف فایل‌های مالک، انتشار، production و مدل/runtime همچنان approval مخصوص
می‌خواهند. Registry/Master HOLD محفوظ است. مسیر امن بعدی: بررسی پیشنهادهای collision
و تصمیم دربارهٔ همان manifest مدل؛ تا تأیید آن دانلودی انجام نشود.
Rollback: revert همین commit محلی؛ wrapper و helper جدید را از مسیر استفاده خارج
کنید. هیچ سرویس، database migration یا تغییر global برای بازگردانی وجود ندارد.
