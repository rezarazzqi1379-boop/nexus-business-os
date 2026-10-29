# برش اول پایش منابع مجاز — ۲۰۲۶-۱۰-۲۹

مبنای کار: main با SHA `2143868af6372caa531959dbc883b8e288327b8d` (PR #124).
این برش در `PRJ-NEXUS-SANDBOX` و lane موجود `industrial-tender-pilot` است؛
هیچ پروژهٔ تجاری دیگری را فعال یا از HOLD خارج نمی‌کند.

## معماری و اجرای قابل بازتولید

`source_monitor.tick` برای هر بازهٔ UTC یک task پایدار در `AutonomyStore`
ثبت می‌کند. اجرای آن از lease، retry، سقف تلاش، توقف اضطراری، checkpoint و
supervisor موجود در `CommercialRuntime` استفاده می‌کند. هر tick حداکثر یک
کار واجد شرایط را تلاش می‌کند؛ ممکن است آن کار retry بازهٔ قبلی باشد.
HTTP دقیقاً یک‌بار تضمین نمی‌شود: crash پیش از ثبت checkpoint ممکن است به دریافت مجدد منجر شود.
برای هر cadence یک DB اختصاصی استفاده شود؛ تغییر cadence مهاجرت جداگانه می‌خواهد.

دریافت زنده فقط از URL ثابت بانک جهانی با transport محدود موجود ممکن است:
حداکثر ۳ رکورد، ۶۴ KiB، timeout و بدون دنبال‌کردن redirect.
این مسیر جدید هیچ transport عمومی برای URL دلخواه ایجاد نمی‌کند.
`assess` موجود از `deep_search_fabric`، نرمال‌سازی، `group_duplicates` و
منطق محافظه‌کارانهٔ PR #124 استفاده می‌کند.
provenance شامل project، lane، query، URL منبع/سند، زمان دریافت و SHA-256 است.
URL سند کشف‌شده فقط `CANDIDATE_NOT_ACTIVATED` است و خودکار fetch نمی‌شود.

`compare_sources` از `ConnectorControlPlane` برای تازگی، سلامت و جداسازی
پروژه استفاده می‌کند؛ binding lane نیز کنترل می‌شود. گروه استقلال باید توسط
اپراتور از مالکیت/منشأ منبع تعیین شود؛ تفاوت hostname یا provider کافی نیست.
اختلاف مقدار موجب REJECT، شواهد ناکافی موجب INVESTIGATE و همگرایی فقط
`CORROBORATED_CLAIM` می‌شود. این نتیجه مجوز معامله نیست.
منبع دوم زنده هنوز نصب/فعال/احراز نشده است؛ آزمون چندمنبعی frozen است.

نمونهٔ اجرای آفلاین با همان DB در دفعات بعد:

```powershell
$env:PYTHONPATH='src'
python source_monitor.py --db data/source-monitor/queue.db --fixture sample.json --output data/source-monitor/report.json
```

در این میزبان به‌جای `python` از مسیر محیط مجازی معتبر استفاده شود.
اجرای `--live` به‌جای `--fixture` فقط دریافت محدود همین منبع را انتخاب می‌کند.
سرویس دائمی یا زمان‌بند سیستم‌عامل نصب/فعال نشده است؛ host باید tick را فراخوانی کند.
فعال‌سازی cadence و نخستین اجرای زنده در محیط هدف باید دامنهٔ مجوز مشخص داشته باشد.
workflow جدید فقط acceptance آفلاین را در PR اجرا می‌کند؛ workflow اصلی کل suite را اجرا می‌کند.

## قرارداد پذیرش برش اول

- restart و tick هم‌زمان در یک bucket فقط یک کار ثبت کنند؛ completion ثبت‌شده دریافت مجدد نکند.
- failure با پیام ثابت ثبت شود، backoff حفظ شود و emergency stop جلوی دریافت را بگیرد.
- حذف تکرار، provenance، CLAIM و HOLD حفظ شوند؛ actionable و external writes صفر باشند.
- mirror مستقل شمرده نشود؛ conflict، stale، future و cross-project رد شوند؛ cross-lane fail closed باشد.
- بهره‌وری واقعی: elapsed_seconds، work_attempted، completed_queue_items، تعداد دریافت‌شده،
  نرخ تکرار و source gate از اجرای واقعی همان مسیر گزارش شوند. درآمد، دقت تجاری،
  پوشش بازار و نرخ false positive هنوز UNKNOWN هستند.

## backlog با معیار پذیرش

| فاز | کار محدود | معیار پذیرش |
|---|---|---|
| ۲ | adapter منبع مستقل دوم با منشأ و شرایط دسترسی مستند | replay ثابت، ۲ گروه منشأ بررسی‌شده، conflict حفظ‌شده، بودجه/timeout/redirect/حریم داده آزموده؛ هیچ ارتقای خودکار به FACT |
| ۳ | کشف کاندید منبع از نتیجهٔ deep search و ثبت در store موجود | URL نرمال و یکتا، provenance کامل و project/lane ثابت؛ ۱۰۰٪ کاندیدها پیش از فعال‌سازی در انتظار بررسی |
| ۴ | اتصال tick به scheduler موجود در محیط هدف | restart، backoff، قفل هم‌زمانی، retention، clock boundary و stop در آزمون یک‌روزه؛ بودجهٔ روزانهٔ محدود و مجوز دقیق فعال‌سازی |
| ۵ (در این PR پیاده‌سازی شد) | پایش تغییرات بین بازه‌ها | تشخیص added/changed/removed روی fixture نسخه‌دار، حفظ نسخه‌های متناقض، نبودن رکورد در نمونهٔ ۳تایی به معنای حذف بازار نباشد |
| ۶ | تطبیق معنایی و راستی‌آزمایی سند مستقل | claim-to-span و منشأ مستقل برای هر ادعا؛ همگرایی بدون سند کافی verified یا مجوز تجاری نشود |
| ۷ | سنجش بهره‌وری و adoption | baseline ثابت، هزینه/زمان واقعی، نتیجهٔ بررسی انسانی و پوشش/شکاف اندازه‌گیری‌شده؛ frozen evaluation و rollback و adoption gate پیش از promotion |

Rollback: host را از فراخوانی tick متوقف کنید؛ journal و DB را نگه دارید.
هیچ merge، deployment، ایمیل یا اقدام تجاری جزئی از این برش نیست.

اصلاحات بازبینی PR #126، قرارداد ترتیب checkpoint و تفکیک تغییر ظاهری، و معیار
تطبیق محیط/بنچمارک در `docs/MONITOR_REVIEW_126_FA.md` مستند شده‌اند.
