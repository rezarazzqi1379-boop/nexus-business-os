# گزارش مدیریتی ادامهٔ اجرا v6.1 — ۲۲ نوامبر ۲۰۲۶

مرحله: OPERATE / STABILIZE. مسئول: NEXUS_OWNER. این گزارش مشاهدات اول نوامبر را برای وضعیت امروز تازه می‌کند؛ گزارش تجاری یا پذیرش تولید نیست.

## نسخه‌ها و تغییرات

main با API رسمی GitHub دوباره بررسی شد: `e5bc75867ed85fa3869018a578d049bfdb5e57bd`.
PR134 هنوز draft در `57cbb339`؛ PR135 باز در `ad8081157e13f9f3a6deb9fe0d8ed37f955c9236`؛ PR136 باز در `5c568ef3e39af21858ac9473889471a2660af4d9`؛ PR137 باز در `adc060fb8269b2af06ee4daf58bf0d8e9a0fbbda` است. هیچ‌کدام ادغام نشدند.

شاخهٔ محلی مستقل از main: `codex/v61-official-source-acceptance`؛ commit کد `2465ba693b97289fdd49108f56ba1e0185058e01`.
کد نصب Windows، main و این candidate سه scope جدا دارند؛ CI قبلی PR136 شاهد کد v6.1 نیست.

تغییرات کد:

- `nexus_fts_source.py`: آداپتر رسمی UK در همان CommercialRuntime/PublicResearchRuntime؛ همان صف، fencing، checkpoint، Supervisor و assessor آزمایشی موجود. فقط GET ثابت؛ بدون scheduler یا agent process جدید.
- همان AttemptBudget با scope ثابت `nexus:fts:bounded-read` و سقف کل **یک درخواست**؛ binding mode/ledger در journal موجود. بودجهٔ World Bank reset یا افزایش داده نشد. شکست هم سهمیه مصرف می‌کند؛ retry صف نمی‌تواند HTTP دوم بزند.
- `nexus_free_research.py`: گزارش شکست اکنون دو دستهٔ ثابت acquisition/verification و index عددی منبع دارد؛ متن خطای provider، credential یا response منتشر نمی‌شود. سقف دو خواندن تغییر نکرد.
- `tests/test_commercial_pilot.py`: ساعت تست wrapper با fixture اکتبر ثابت شد. کنترل تازگی محصول و assertion تجاری ضعیف نشد.
- `tests/test_fts_source.py` و `tests/test_free_research.py`: آزمون‌های منفی و regression این تغییرات.

## پذیرش مهندسی و کیفیت تصمیم

فرمان‌های نهایی از ریشهٔ همین checkout، با interpreter موجود `C:/Users/AvallPc/nexus-business-os/.venv/Scripts/python.exe`:

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONPATH='src;.'
python -m pytest -q -p no:cacheprovider --basetemp data/nexus_system/backups/v61-final-focused-20261122g tests/test_fts_source.py tests/test_free_research.py tests/test_commercial_pilot.py tests/test_source_monitor.py tests/test_router_runtime.py tests/test_http_attempt_budget.py tests/test_authority_admission.py tests/test_project_control_plane.py
# 185 passed in 6.77s
python -m pytest -q -p no:cacheprovider --basetemp data/nexus_system/backups/v61-final-full-20261122h tests evals
# 1898 passed, 1 warning in 47.85s
```

هشدار Starlette/httpx باقی است. نخستین focused قبل از اصلاح ساعت: 155pass/1fail؛ full میانی 1894pass بود و پس از چهار تست transport/binding جدید، full نهایی1898pass شد. یک fixture جدید ابتدا به‌درستی guard «budget مفقود پس از ساخت queue» را فعال کرد؛ ترتیب setup اصلاح شد. خطاهای temp/نام بسیار بلند fixture و استخراج اولیهٔ source_url به‌جای source_ref نیز ثبت شده‌اند؛ هیچ شکست به‌عنوان pass گزارش نشده است.

تست‌ها missing identity/supplier/eligibility/authority را UNKNOWN نگه می‌دارند؛ keyword fit جای مشخصات نمی‌نشیند؛ expired/stale/future/duplicate/conflicting source، high-score بدون مدارک، cross-project، checkpoint tampering، provider failure، redirect/429 و تغییر mode رد می‌شوند. قیمت، قابلیت تأمین و پنج شرط تجاری مستقل از عنوان یا score تأیید نمی‌شوند. حالت بدون agent در مسیر submit مسدود است؛ نقص lifecycle selector کشف‌شده در PR135 هنوز روی main اصلاح نشده و پذیرش کلی router تا ادغام مصوب آن باز است. حفاظت مالکیت/lease/checkpoint و authority در full suite پوشش داده شد؛ هیچ کنترل امنیتی برای سبزکردن تست کم نشد.

## اجرای واقعی و persistence

انتخاب کوچک منابع: UK FTS اولویت اول برای پوشش صنعتی/تجهیزات و مناقصهٔ مستقل از publisher عمان/EU، API عمومی، بدون credential و هزینهٔ API؛ relevance اقتصادی نمونه هنوز نامعلوم. TED و OQEP از قبل موجودند، ساخت نسخهٔ دوم آن‌ها ارزشی ندارد. World Bank فعلی context تاریخی است. Contracts Finder کاندیدای بعدی است، ولی هم‌پوشانی قراردادها با FTS باید قبل از ادعای پوشش مستقل dedup شود؛ فعال نشده است. timestamp منبع را SLA یا current demand فرض نمی‌کنیم.

مبنای رسمی API: [راهنمای دولت بریتانیا](https://www.gov.uk/government/publications/open-contracting). صفحهٔ تفصیلی API در یک probe مرورگر403 داد؛ هیچ کنترل دسترسی دور زده نشد. API عمومی جداگانه با transport محدود موجود200 داد.

task واقعی `fts_official_bounded_v61` در **همان صف موجود** `operational-live-20261031.queue.db`:

- یک GET، سه release، سقف256KiB و8ثانیه transport، بدون pagination/redirect/retry HTTP؛ 101917بایت واقعی.
- SHA256: `63e596f8c81608bb2f76775192377d73a56afdaaa4dcc13aab52dcf9b93544f5`.
- صف یک تکمیل؛ Supervisor=`accepted`. سه notice ID یکتا، صفر duplicate؛ دو notice ممکن است به همان procurement مربوط باشند، پس سه فرصت مستقل ادعا نشده است.
- تصمیم‌ها: REJECT3 / INVESTIGATE0 / PROCEED0؛ هر سه title خارج keyword صنعتی نمونه بودند. mandatory verification همچنان UNKNOWN، commercially verified/actionable0.
- assignment فقط `PRJ-NEXUS-SANDBOX` است. binding پروژهٔ واقعی **BLOCKED**؛ آن را authoritative commercial integration نمی‌نامیم.
- process مستقل SQLite را read-only باز کرد: integrity=ok، دقیقاً یک checkpoint، hash و assessment بازتولید شدند. submit تکراریfalse، drain0، ledgercount1 ثابت. artifact خلاصه و یک observation در هاب موجود مهندسی ثبت شد؛ raw queue/contacts منتشر نشدند.

شاهد: `data/research/v61-fts-live-20261122.json`. snapshot هدفمند صف و ledger از SQLite backup API، hash manifest و scratch restore/readback موفق دارد؛ live overwrite و rebinding ledger انجام نشد. این شاهد full-host/off-host DR نیست و نقص asset coverage هاب مهندسی PR137 همچنان باز است.

## عملیات موجود و تازگی

سرویس محلی ابتدا ConnectionRefusedError10061 و task=Ready داشت. همان `NEXUS-Local-Intelligence` با پیکربندی قبلی start شد؛ پس از آن task=Running، health/ready200 و protected endpoint401. نتیجه267009 وضعیت task درحال اجراست. secret خوانده/کپی نشد و deployment replacement رخ نداد. revision process **UNKNOWN**؛ production verified نیست.

checker موجود نصب‌شده پیش از refresh سه source error/stale را آشکار کرد. runner قبلی یک بار اجرا شد:

| منبع | نتیجهٔ واقعی | hash دادهٔ خام |
|---|---|---|
| OQEP | 26 ردیف،26 emitted در SANDBOX،46660بایت | `645a34d69b9f7ceb370d9c84f1c0c06cd52418ebfc4e26b90947dcf3b24fbf02` |
| World Bank context2024 | 3 ردیف،780بایت؛ دادهٔ کلان تاریخی | `9c4dfc4bbe4d436e20160393a465257bc1309096a2fb92bc6087dbd169c83f2f` |
| TED | 10 آگهی از صفحهٔ محدود؛ total_matches8633 تعداد خریدار نیست | `56d076e2a9f4c97e417cff449a014b8c2ef683c132b58b52cac1672d605b7bc4` |

hashها مستقل با فایل‌های واقعی تطبیق شدند. source_errors پس از refresh صفر شد؛ تکرار checker changed_lanes=[] و صفر network/model داشت. تعداد26 با سابقه61 فرق دارد و تغییر منبع است؛ رکورد جدیدِ بارگذاری‌شده مساوی فرصت جدید یا buyer verified نیست. چرخه **دستی** بود.

## زمان‌بندی و مانع خودکارسازی

اجرای scheduled روی main فعلی اکنون واقعاً مشاهده شد: Free Runtimeهای43913417578،44130654653،44347100282 و **44567201418** موفق؛ synthetic43870666787 موفق. در44567201418 لاگ job135712082318، task1،GET2،Supervisor accepted وcheckpoint/replaytrue را تأیید می‌کند. runner موقت است؛ state بین دو Actions run حفظ نمی‌شود و quota/delivery دقیق تضمین ندارد.

آخرین scheduled Free Runtime **44770194843** در20نوامبر شکست: startup/auth پاس، research بعد از یک HTTP attempt BLOCKED، tasks0، Supervisor NOT_VERIFIED. علت دقیق HTTP از log قابل اثبات نیست؛ redaction قبلی acquisition را از validation جدا نمی‌کرد. diagnostic اصلاح‌شده فقط candidate محلی است و این run را به success تبدیل نمی‌کند. artifact failure14647230979 در log ثبت شده؛ دانلود/ماندگاری امروز آن تأیید نشده است.

heartbeat موجود `nexus-daily-control-plane` فعال با cadence/target قبلی است. آخرین turn امروز07:44:21Z **پیش از اجرای repository** با `workspace routing discovery failed` شکست. مسیر workspace موجود و registered است؛ دو registration یک مسیر مشاهده شد، ولی root cause از آن استنتاج نشده. تغییر project mapping/provider routing از کد این repo قابل اثبات و رفع نیست. اقدام خارجی لازم: تعمیر association همان thread `01a0945e-81a2-7ef3-870a-600de84d6918` در host Codex و مشاهدهٔ اجرای واقعی بعدی. هیچ scheduler/thread جایگزینی ایجاد یا بیدار نشد. recovery کامل این مانع هنوز TESTED نیست. اعلان failed_runs_only تنظیم شده؛ تحویل اعلان به مالک مشاهده نشده است.

## پوشش سبد و پذیرش تجاری

هشت policy موجود با `watch_portfolio` پوشش داده شدند؛ `v61-portfolio-20261122.json` هدف، missing fields، مسئول، next action، monitoring، deadline نامعلوم و outcome نامعلوم را برای هرکدام دارد. policy catalog جای master نیست.

hydrostatic tester،KCl/MOP وcan forming مسیرهای procurement جدا دارند؛ heat treatment همچنان HOLD؛ food additives وcoffee research؛ tinplate blocked؛ portfolio platform workstream جدا. steel/OCTG sales وinternational tenders بدون canonical ID از تجهیزات procurement جدا و BLOCKED باقی ماندند. اسامی/current counterparts/مذاکره یا الزام جدید از عنوان سند یا تاریخچه ساخته نشد.

bootstrap واقعی جدید در `v61-preflight-20261122.json` **BLOCK** است: authenticated version-bound Registry/Master binding در دسترس نیست. بازخوانی فایل تاریخی یا اتصال plugin این مجوز را تولید نمی‌کند. این مانع فقط تصمیم‌های وابستهٔ تجاری را می‌بندد؛ تست و SANDBOX ادامه یافت.

| شاخص | نتیجهٔ این چرخه |
|---|---|
| notice جدید بررسی‌شده |3؛ یکتایی opportunity مستقل اثبات نشده |
| counterparty verified / qualified / actionable |0 / 0 / 0 |
| RFQ نهایی / follow-up مصوب / ارسال بیرونی |0 / 0 / 0 |
| پاسخ supplier / مذاکره / قرارداد / درآمد / margin |UNKNOWN؛ نتیجهٔ مالی تأییدشده وجود ندارد |

## آمادگی استقرار و وضعیت نهایی

candidate کد با SHA تغییرناپذیر و hash پیکربندی در `v61-release-candidate-20261122.json` آماده است. target همان Windows خصوصی و0هزینهٔ جدید میزبانی است؛ انرژی/compute و account quota UNKNOWN. پیکربندی compose موجود فقط alternative است، روی host جدید اجرا نشده. state SQLite موجود، auth/DPAPI موجود، health، scheduler، backup محدود، scratch restore و rollback boundary ثبت شده‌اند. off-host backup، revision پردازش، mapping پروژه و full unattended recovery اثبات نشده‌اند.

| قابلیت | طبقه‌بندی با حدود شاهد |
|---|---|
| adapterUK و تصمیم‌گیری محافظه‌کارانه |TESTED / INTEGRATED در صف SANDBOX؛ یک اجرای واقعی |
| state task و replay بین processها |PERSISTENT؛ در همان queue scope |
| API خصوصی نصب‌شده |ACTIVATED / RUNNING پس از start؛ revisionUNKNOWN |
| runner منابع موجود |TESTED؛ آخرین چرخهٔ دستی و capture تازه |
| GitHub schedule |AUTOMATED با success واقعی main؛ آخرین runfailure؛ state بین runها ephemeral |
| heartbeat کامل محلی |BLOCKED در app routing |
| canonical commercial assignment |BLOCKED در authority |
| production revision/promotion |BLOCKED؛ PRODUCTION_VERIFIED ادعا نشده |

ENGINEERING_VERIFIED فقط در scope تست/داده/صف محلی؛ PILOT_ACCEPTED کلی هنوز پذیرفته نیست؛ COMMERCIAL_RELEASE_ACCEPTED مسدود؛ BUSINESS_OUTCOME_VERIFIED نتیجهٔ اثبات‌شده ندارد.

نیازهای دقیق باقی‌مانده: (1) ارسال candidate جدید و ایجاد PR کوچک پس از تأیید دقیق خارجی؛ CI همین candidate هنوز اجرا نشده. (2) تأیید exact-head برای ادغام PR135/137/136؛ هیچ merge inferred نشود. (3) رفع routing برنامهٔ Codex و مشاهدهٔ heartbeat موفق بعدی. (4) authenticated approval برای hash/project binding Registry/Master. (5) پیش از production، تأیید target/revision/config/permission/cost/rollback مشخص و اثبات revision. هر ایمیل، bid، تماس، خرید یا قرارداد مجوز دقیق جدا لازم دارد.

گام اجرایی بعدی: انتشار همین شاخه برای بررسی و CI، سپس تعمیر association زمان‌بند موجود؛ نه ساخت control plane دیگر. تا رفع این وابستگی‌ها، ادعای تکمیل جهانی یا موفقیت تجاری مجاز نیست.
