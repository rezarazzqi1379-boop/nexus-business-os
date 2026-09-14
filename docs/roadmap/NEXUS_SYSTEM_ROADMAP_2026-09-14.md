# پیشنهادهای سیستم/ایجنت/اسکیل برای NEXUS Business OS
تاریخ: 2026-09-14 — بر اساس بررسی کد واقعی پروژه + جست‌وجوی وب

## ⚠️ یافتهٔ مهم که باید قبل از هر چیز ببینی (مربوط به بخش شبکه‌سازی)

قبل از پیشنهاد دادن دربارهٔ «شبکه‌سازی»، جست‌وجو کردم ببینم وضعیت تحریم‌ها برای ورتیکال
فروآلیاژ (FAL-A واردات فرومنگنز، FAL-B صادرات فروسیلیکون) چطوره، چون قبلاً هم توی
CURRENT_STATE.md خودت این ریسک رو flag کرده بودی. چیزی که پیدا کردم:

- طبق صفحهٔ رسمی OFAC آمریکا، Executive Order 13871 مشخصاً بخش «Iron, Steel, Aluminum,
  and Copper Sectors of Iran» رو هدف قرار داده — فروآلیاژ ورودی مستقیم صنعت فولاده.
- گزارش‌های خبری (GMK Center، Eurometal) می‌گن اتحادیهٔ اروپا در 2026 تحریم تجارت فولاد و
  فلزات با ایران رو دوباره برقرار کرده.
- این‌ها رو فقط از سرچ وب پیدا کردم، **متن قانونی دقیق و این‌که فروآلیاژ به‌طور مشخص
  داخل scope هست یا نه رو نمی‌تونم خودم تعیین کنم** — این دقیقاً کاریه که یه وکیل
  تحریم/export control باید انجام بده، نه من.

**نتیجه برای این سند:** هر پیشنهاد زیر که به «شبکه‌سازی» مربوطه، فقط در حد تحقیق و
ساخت شواهد می‌مونه (research_only)، هیچ ابزار تماس/outreach واقعی پیشنهاد یا ساخته
نمی‌شه، و صریحاً می‌گم قبل از هر قدم بعدی باید با یه وکیل واقعی مشورت کنی.

Sources:
- [Iran Sanctions | Office of Foreign Assets Control](https://ofac.treasury.gov/sanctions-programs-and-country-information/iran-sanctions)
- [The EU has reinstated sanctions against Iran, banning trade in steel and metals](https://gmk.center/en/news/the-eu-has-reinstated-sanctions-against-iran-banning-trade-in-steel-and-metals/)
- [EU bans steel trade with Iran - EUROMETAL](https://eurometal.net/eu-bans-steel-trade-with-iran/)
- [EU sanctions against Iran - Consilium](https://www.consilium.europa.eu/en/policies/sanctions-against-iran/)

---

## ۱. مدیریت پروژه (Management)

### قبلاً وجود داره (استفاده کن، دوباره نساز)
- `decision_engine.py` + `owner_decision_runtime.py` — رتبه‌بندی تصمیم و تفویض محدود
  (هیچ تصمیم پرریسک/غیرقابل‌برگشت خودکار اجرا نمی‌شه).
- `project_control_plane.py`, `projects.py` — وضعیت پروژه‌ها.
- Task list همین Claude Code (که همین الان هم دارم ازش استفاده می‌کنم).

### پیشنهاد جدید
**یه اسکیل «NEXUS status brief»**: هر بار که می‌خوای بدونی «کجای کاریم»، به‌جای این‌که
من دوباره کل کد رو بخونم، یه اسکیل کوچیک بسازم که `projects.py` + `decision_engine.py`
+ فایل‌های `.nexus/state/` رو می‌خونه و یه خلاصهٔ یک‌صفحه‌ای فارسی می‌ده: چی فعاله، چی
قفله، چی منتظر تایید توئه. ریسک: صفر (فقط خواندنیه). می‌تونم همین الان بسازمش.

## ۲. ارتقای فنی (Upgrade)

### قبلاً انجام شده امروز
- `rolling_mill_mechanics.py`, `opportunity_suggestion_engine.py`,
  `fal_trade_economics.py` — همه تست‌شده، همه به gate/lane موجود قفلن.
- `PLUGIN_CAPABILITY_MAP.md` — الان می‌دونیم کدوم پلاگین واقعاً کار می‌کنه.

### پیشنهاد جدید (اولویت‌بندی‌شده)
1. **تست برای ماژول‌های بی‌تست** — طبق بررسی امروز، `need_radar.py` قبلاً هیچ تستی
   نداشت (حالا داره). باید چک کنم چند ماژول دیگهٔ حساس (`decision_engine.py`,
   `owner_decision_runtime.py`) تست کافی دارن یا نه. اگه بخوای، همین رو ادامه می‌دم.
2. **یکی‌کردن fal_vertical.py و prj_fal_01.py** — خودِ CURRENT_STATE.md این رو به‌عنوان
   یه duplication حل‌نشده ثبت کرده. من دست بهش نزدم چون نیاز به یه تصمیم معنایی
   (END_USER vs IMPORTER) داره که باید تو یا ChatGPT/NEXUS بگیرید، نه من به‌تنهایی.
3. **بستهٔ استاندارد داده برای فروآلیاژ** — یه اسکیمای JSON مشابه
   `ROLLING_MILL_ENGINEERING_INTAKE.json` ولی برای قیمت/کیفیت هر خرید فروآلیاژ، تا
   `fal_trade_economics.py` بتونه از داده‌های واقعی (نه دستی) تغذیه بشه.

## ۳. سودآوری (Profitability)

### قبلاً وجود داره
- `fal_trade_economics.py` (امروز ساخته شد) — محاسبهٔ landed cost/margin، فقط منتظر
  عدد واقعیه (قیمت FOB، کرایه، تعرفه).

### پیشنهاد جدید — منابع قیمت واقعی که پیدا کردم
برای این‌که `fal_trade_economics.py` واقعاً روی عدد زنده کار کنه، به یه منبع قیمت
نیاز داری. این‌ها منابع شناخته‌شدهٔ صنعت فروآلیاژن (من به هیچ‌کدوم دسترسی مستقیم
API ندارم؛ باید خودت/تیم مشترک بشید):
- [Fastmarkets – Ores & Ferroalloys](https://www.fastmarkets.com/metals-and-mining/ores-and-alloys/)
- [Mysteel – China Ferroalloys Market](https://www.mysteel.net/commodities/ferroalloys/)
- [Asian Metal – Ferrosilicon Price Index](https://www.asianmetal.com/Ferrosilicon-Price-Index/)
- [CRU Group – Ferroalloys](https://www.crugroup.com/en/commodities/ferroalloys/)

پیشنهاد عملی: یه ماژول `market_price_snapshot.py` بسازم که هر بار قیمت رو (از هرکدوم
از این منابع که خودت دسترسی خریدی/دستی کپی می‌کنی) به‌عنوان یه `NeedEvidence`
(همون کلاس موجود توی `need_radar.py`، با `classification="MEASUREMENT"` یا
`"CLAIM"` بسته به منبع) ثبت کنه — نه این‌که من قیمت رو حدس بزنم یا از سایتی که
API عمومی نداره scrape کنم.

## ۴. شبکه‌سازی (Networking) — با احتیاط، به‌خاطر یافتهٔ بالا

### قبلاً وجود داره (و همین‌جوری می‌مونه، فقط تحقیقاتی)
- `need_radar.py` + `opportunity_suggestion_engine.py` — outreach همیشه غیرمجازه
  (`outreach_authorized: False`, ساختاری، نه یه فلگ که بشه عوضش کرد).

### پیشنهاد جدید (فقط در حد جمع‌آوری شواهد، صفر تماس واقعی)
1. **Sanctions/compliance evidence gate**: قبل از این‌که یه سیگنال (`NeedSignal`) از
   `need_radar.py` حتی وارد `opportunity_suggestion_engine.py` بشه، یه چک اضافه کنم
   که وضعیت طرف مقابل (کشور، بخش صنعتی) رو به‌عنوان یه `UNKNOWN` اجباری علامت بزنه
   تا وقتی یه انسان صریحاً بنویسه که بررسی حقوقی/تحریمی انجام شده. این دقیقاً همون
   الگوی fail-closed خودِ پروژه‌ته، فقط برای این ریسک مشخص.
2. **کاتالوگ منابع اطلاعات عمومی صنعت** (نه تماس، فقط خواندن اخبار/دایرکتوری عمومی)
   برای تغذیهٔ signal های `need_radar.py` — Fastmarkets/Mysteel/CRU برای اخبار بازار،
   نه برای پیدا کردن مخاطب.
3. **هرچیز فراتر از این (پیام دادن واقعی، پیدا کردن ایمیل/تلفن، ثبت در CRM بیرونی)**
   رو پیشنهاد نمی‌دم و نمی‌سازم تا وقتی جواب یه وکیل واقعی رو دربارهٔ scope دقیق
   تحریم برای فروآلیاژ ببینی.

---

## جمع‌بندی: چی رو همین الان بسازم؟

از موارد بالا، این‌ها ریسک صفر دارن و می‌تونم همین الان بسازم (اگه بخوای):
- اسکیل «NEXUS status brief» (بخش ۱)
- چک کردن پوشش تست `decision_engine.py`/`owner_decision_runtime.py` (بخش ۲.۱)
- ماژول `market_price_snapshot.py` برای ثبت دستی قیمت‌ها به‌عنوان evidence (بخش ۳)
- Sanctions evidence gate روی `opportunity_suggestion_engine.py` (بخش ۴.۱)

بقیه (یکی‌کردن fal_vertical/prj_fal_01، هر چیز API واقعی قیمت، هر چیز شبکه‌سازی فراتر
از تحقیق) نیاز به یه تصمیم یا مشاورهٔ بیرونی از طرف تو داره.
