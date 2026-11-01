# پذیرش مأموریت v5 — ۲۰۲۶/۱۱/۰۱

مرحله: VERIFY / STABILIZE / کاندید استقرار. مسئول عملیات: مالک مخزن.
این گزارش پذیرش تجاری یا مجوز تولید نیست.

## مرجع و اجرای واقعی

main از origin بازیابی شد: `e5bc75867ed85fa3869018a578d049bfdb5e57bd`.
PR133 واقعاً merged است؛ PR134 در head `57cbb339ba5398890c6bb0d8650df8166e7cfda9` یک سند draft جداست و وارد این شاخه نشد.
آزمون main: run41277840729 SUCCESS. اجرای تازه پایلوت main: [41278336412](https://github.com/rezarazzqi1379-boop/nexus-business-os/actions/runs/41278336412) SUCCESS؛ task واقعی World Bank، یک GET، سه رکورد و سه REJECT، صفر verified/actionable؛ Supervisor accepted، checkpoint و جلوگیری از replay برقرار.
artifact13072575498، 5050 بایت، SHA256 `bdcfbf51b0218336fcd49303da7a561ade896a5e06b1957d10f599630149986e`.
فایل ZIP واقعاً دریافت و با `scripts/verify_commercial_artifact.py` برای همان main بازتولید شد؛ تلورانس صفر. منبع1444 بایت با SHA256 `d6171a43c748b996de6d3d82d4af78560421faf469a5388bd401c4b31bac9a6b`.

## اصلاح حداقلی

`project_control_plane._select_agent` در main یک عضو WATCH را انتخاب و work را در برنامه running قرار می‌داد. پنج fixture منفی پیش از تغییر شکست خوردند؛ فیلتر lifecycle اکنون فقط SANDBOX_READY/EXPERIMENT/PILOT/ADOPTED_ADAPTER را برای پیشنهاد تخصیص می‌پذیرد و شرط تمام قابلیت‌ها حفظ شد. این فیلتر availability، نصب، اتصال یا مجوز تجاری ایجاد نمی‌کند؛ adapter ثابت موجود، Supervisor و permission gates همچنان لازم‌اند. چهار lifecycle مطالعاتی و انتخاب رقیب بررسی شدند؛ 185 آزمون مرتبط موفق در9.52s.
main کامل:1875 پاس، یک هشدار موجود Starlette،77.75s. candidate کامل:1880 پاس، یک هشدار موجود،79.63s. اجرای کانتینر موقت main41278556064 SUCCESS؛ این تولید نیست. کد و patch محلی checkout قدیمی روی main اعمال کور نشد؛ شرط full-capability از قبل در main موجود بود. lane ساختگی sandbox در scheduler main وجود ندارد؛ نخستین probe آن ValueError داد و با lane معتبر commercial/engineering دوباره بررسی شد؛ هیچ widening انجام نشد.
Rollback: توقف مصرف برنامه جدید، revert همین تغییر selector و تست‌ها با بررسی مالک؛ queue، checkpoint، budget و observations را حذف یا reset نکنید.

## ثبت داده و عامل

هاب checkout ثبت‌شده `C:/Users/AvallPc/nexus-business-os/data/nexus_system/nexus.db` با SQLite mode=ro در process مستقل بازخوانی شد: هر شش observation ادعاشده commercial-expansion-20261101 وجود دارند. این داده گم نشده و نیازی به DB موازی ندارد. شناسه‌های محلی hydrostatic_tester و شناسه‌های PRJ-* هنوز به canonical Registry/Master مصوب متصل نیستند؛ هیچ مهاجرت خودکار، ادغام خصوصی یا کپی کامل داده انجام نشد. بازخوانی فیزیکی VERIFIED است؛ صحت تجاری و canonical integration نیست.
درخواست مستقل commercial-verification/independent-qualification به‌درستی no_qualified_agent است؛ قالب SDK عامل احراز صلاحیت محسوب نمی‌شود. مسیر پژوهش فقط یک پیشنهاد کاتالوگ است. هشت ProjectPolicy از طریق portfolio_watchdog دیده شدند؛ recovery پیشنهادی مجوز بازگشایی heat_treatment HOLD یا tinplate blocked نیست.

## منابع جدید؛ شکست‌ها حفظ شدند

[TED API رسمی](https://docs.ted.europa.eu/api/latest/search.html) جست‌وجوی ناشناس POST /v3/notices/search را مستند می‌کند. یک درخواست sandbox با limit3، سقف100KB و timeout20s از ledger موجود AttemptBudget رزرو شد؛ HTTP400. احتمال ناسازگاری query/field هنوز تشخیص قطعی نیست، چون خطای schema تفصیلی ذخیره نشده. صفر notice دریافت‌شده به معنای صفر بازار نیست. ledger count1، cap1؛ بدون reset/retry.
[ADB Project Procurement](https://www.adb.org/business/project-procurement): یک GET با سقف500KB/20s تلاش شد؛ URLError؛ اتصال محلی تأیید نشد. جست‌وجوی وب به صفحه رسمی دسترسی داشت، ولی این موفقیت adapter runtime نیست. خطای TLS/شبکه دور زده نشد.
هویت ارائه‌دهنده TED=Publications Office EU و ADB=Asian Development Bank. TED روش دسترسی عمومی مستند دارد؛ جزئیات مجوز حقوقی صفحه به challenge مرورگر رسید؛ نرخ، سهمیه، SLA و cadence داده UNKNOWN. ADB اجازه bulk/API/license/cadence هنوز UNKNOWN. هزینه مستقیم درخواست عمومی بدون billing جدید؛ هزینه compute/quota UNKNOWN. geography TED اروپا/آگهی‌های منتشرشده و ADB پروژه‌های بانک؛ qualification و eligibility هر دو UNKNOWN. فایل‌های v5-*-probe query/time/hash/error را ثبت می‌کنند. این‌ها نامزد onboarding هستند، نه منبع canonical یا تولید؛ به‌دلیل شکست آزمون و HOLD، در Registry حاکم promote نشدند.
بودجه فعلی کافی برای اثبات دسترسی adapter دوم نبود. گام منبع بعدی: نمونه schema رسمی TED را در fixture offline اعتبارسنجی کنید، سپس یک بودجه مستقل صریح و محدود برای probe بعدی ثبت کنید؛ ledger مصرف‌شده را دوباره استفاده/پاک نکنید.

## نقشه اجزای حاکم

| قابلیت | پیاده‌سازی موجود | حد اثبات |
|---|---|---|
| Supervisor | agent_supervisor.py | قبول پایلوت و checkpoint واقعی |
| Queue/lease | autonomy.py / nexus_router_runtime.py | همان queue و fences؛ تضمین duplicate در همین scope |
| Research | nexus_public_research_agent.py / nexus_free_research.py | adapter قطعی؛ نه عامل LLM عمومی |
| Commercial | nexus_commercial_pilot.py | یک source، احراز مستقل UNKNOWN |
| Monitor/budget | source_monitor.py / nexus_http_attempt_budget.py | queue binding و restart/fencing تست شده؛ daemon تولید نیست |
| Connectors/MCP | nexus_connector_control_plane.py / src/nexus_core/mcp_broker.py | metadata وجود دارد؛ credential_locator اثبات auth نیست |
| Lab/Search | research_lab.py / deep_search_fabric.py | stages رزروشده entities/sources الزاماً فعال نیستند |
| Storage/backup | unified_data_environment.py | هاب موجود و BackupManager؛ DB موازی ممنوع |
| Authority | authority_admission.py / canonical_sources.py / nexus_chat_bootstrap.py | preflight تازه BLOCK؛ بدون approval معتبر |
| Approval | approvals.py / autonomy.py | approval به‌تنهایی از عنوان سند استنباط نمی‌شود |
| Scheduler | execution_scheduler.py / workflows / automation موجود | برنامه با execution یکی نیست |

پیکربندی connectorهای Gmail/Drive/Notion/GitHub/Supabase/Vercel/Railway/WorldBank inventory است. GitHub اکنون authenticated read اندازه‌گیری شد؛ WorldBank real HTTP موفق؛ دیگر connectorها در این چرخه refresh محتوایی نشدند و ACTIVE اعلام نمی‌شوند. داده خصوصی، token و credential به evidence عمومی منتقل نشد. Apollo/ABRAMS نصب‌بودن ابزار مساوی مجوز مصرف credit نیست؛ مصرف نشد.

## عملیات، هزینه و سبد تجاری

automation موجود nexus-daily-control-plane با cadence روزانه09:00 ACTIVE در config بازیابی شد؛ target همان chat قبلی است و تغییر نکرد. متن آن از adapter TED قبلی سخن می‌گوید ولی فایل‌های نام‌برده در checkout ثبت‌شده پیدا نشدند؛ saved prompt اثبات اجرای نصب‌شده نیست. نه automation جدید ساختیم، نه existing را wake/message کردیم. GitHub free-runtime برنامه weekday07:17UTC دارد؛ runهای تاریخی موفق‌اند، پیوستگی تجاری تضمین نشده. cadence تجاری فعال نشد.
هشت پروژه در data/research/v5-portfolio-watch-20261101.json قابل مشاهده‌اند؛ گزارش private قبلی نامزد دارد، اما این چرخه نامزد جدید مستقلاً qualified نکرد. تعداد qualified/actionable صفر؛ پاسخ، قرارداد، درآمد و margin UNKNOWN. تاریخچه آگهی را درآمد و قیمت tender را margin حساب نکردیم.
Token provider، quota باقی‌مانده Actions، ذخیره‌سازی هزینه‌دار و uptime دائمی UNKNOWN. هیچ paid API/hosting/account/permission اضافه نشد. سه درخواست آزمایشی تازه در این چرخه: WorldBank در Actions موفق، TED400، ADB اتصال ناموفق؛ جست‌وجو و دانلود artifact جداگانه‌اند.

## کاندید استقرار پایدار و تأیید لازم

همان Dockerfile، railway.toml و deploy/compose.persistent.yml حفظ شدند؛ توپولوژی حداقلی یک Linux Docker host، یک API، volume /data، secret خارجی، loopback، health/readiness و resource limits است. worker و hub/queue/ledger نیز باید روی همان storage مصوب و تک‌میزبان باشند. هیچ SQLite را به Vercel ephemeral نبردیم. گزارش قدیمی Vercel placeholder اثبات revision امروز نیست و در این چرخه production مجدداً تأیید نشده.
قبل production باید مالک دقیقاً این موارد را تعیین و تصویب کند: host/account، revision/image digest، سقف هزینه، permission، TLS/firewall، محل off-host backup، RPO/RTO، اپراتور، rollback و پنجره اجرا. secret در UI رسمی/محیط مصوب مالک provision شود؛ وارد گزارش نشود. BackupManager از SQLite backup API و manifest استفاده کند؛ restore فقط به target خالی و با تأیید دقیق. image rollback و حفظ volume از حذف volume جداست. وضعیت کنونی Stage B آماده‌سازی با target نامشخص است؛ Stage C/D BLOCKED.
مرزهای باقیمانده: authority Registry/Master authenticated approval، مستقل‌بودن و صحت منبع دوم، project-ID reconciliation، عامل احراز صلاحیت، cadence تأییدشده، میزبان و backup خارج میزبان. ادغام PR جدید و تولید بدون تأیید دقیق انجام نمی‌شود.
