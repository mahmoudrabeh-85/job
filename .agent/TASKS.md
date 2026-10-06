# TASKS.md — الحالة والمهام

## DONE — Phase 0: تدقيق المستودع (2026-09-27)
- [x] فحص البنية: FastAPI + SPA + Supabase/SQLite + Vercel fra1.
- [x] حصر الـ routes (v1 + legacy shims + catch-all) والمكونات (7 صفحات SPA).
- [x] حصر نموذج البيانات: jobs (14 عمودًا، بلا وصف) + applications.
- [x] تأكيد: لا تكامل LLM في الخادم (التقييم heuristic فقط).
- [x] حصر الدين التقني والمخاطر (أدناه) + إنشاء مساحة `.agent/`.

## الحالة الحالية (خارج نطاق Phase 0 — للعلم فقط)
- търг `1de4bab` مدفوع: `POST /api/v1/match` + إصلاح Wizard + علامة Winner Jobs.
- عمل غير مدفوع قيد التطوير (جلسة موازية): `directOnly` + `cv-builder` +
  `refresh` + `direct_employers` — **يُترك لصاحبه، لا يُدفع هنا**.

## PROPOSED — Phase 1 (مقترح، بانتظار موافقة المستخدم)
- [ ] توثيق الفارق الحي: 500 وظيفة/32 مصدرًا مقابل 397 في الذاكرة.
- [ ] تنظيف المكرر legacy (app/index.html، job_app.py، صفحات الجذر، ملفا v2.0).
- [ ] مراجعة أمنية لنقطة `admin/refresh-direct` (توكن عبر query).
- [ ] تقييد `POST /api/v1/applications` (مفتوحة بلا auth/حد).
- [ ] طبقة AI provider abstraction (PRD §15) + أول استخدام حقيقي واحد فقط.
- [ ] إثبات Deduplication fingerprint (PRD §11) على عينة.

## Technical Debt (من التدقيق)
1. ملفات legacy ميتة تُقدَّم عبر catch-all وتشتت الواجهة.
2. لا وصف وظيفي في DB → سقف جودة المطابقة محدود (PRD §4.2).
3. RLS مفتوحة للجميع + لا auth + لا rate-limit موثق على serverless.
4. لا اختبارات آلية في CI (فحوصات يدوية فقط).
5. تحرير متزامن من جلستين في نفس الشجرة — خطر الكتابة فوق بعض.
