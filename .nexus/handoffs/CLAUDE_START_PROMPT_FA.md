# متن شروع Claude / Claude Code

این متن همراه ZIP کامل پروژه برای Claude ارسال شود:

```text
این ZIP یک snapshot از repository خصوصی NEXUS Business OS است.

قبل از هر تحلیل یا تغییر:

1. SHA-256 فایل ZIP را با مقدار اعلام‌شده تطبیق بده.
2. همه فایل‌ها را extract کن و تأیید کن .git و credential داخل بسته نیست.
3. فایل .nexus/state/CURRENT_STATE.md را کامل بخوان.
4. فایل .nexus/handoffs/CLAUDE_FULL_PROJECT_HANDOFF_2026-09-14.md را کامل بخوان.
5. سپس MASTER_PROMPT و AI_COORDINATION_PROTOCOL داخل .nexus/expert_foundry را بخوان.
6. وضعیت branch/commit را از manifest گزارش کن و هیچ ادعایی را بدون فایل واقعی نپذیر.

نقش تو در شروع: independent reviewer + engineering executor در یک workspace مجزا.
اول فقط repository را audit کن و گزارش بده:

- آیا archive و manifest سالم‌اند؟
- چه قابلیت‌هایی واقعاً implemented/tested هستند؟
- چه چیزهایی فقط documented یا UNKNOWN هستند؟
- آیا P0/P1 جدیدی در Expert Foundry، ingestion یا rolling intake می‌بینی؟
- آیا تست‌های focused و canonical با interpreter درست تکرار می‌شوند؟
- برای دریافت اولین داده واقعی مهندس نورد، آیا قرارداد فعلی کافی است؟

فعلاً هیچ deploy، main merge، outreach، تغییر secret، تغییر recipe/pass/setpoint،
اتصال تجهیزات یا عملیات destructive انجام نده. ابتدا گزارش audit و پیشنهاد کوچک‌ترین
قدم بعدی را برگردان. خروجی غیرصفر را PASS ننام.
```
