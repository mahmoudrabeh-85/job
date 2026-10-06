# CHANGELOG.md

## 2026-09-27 — Phase 0: إنشاء مساحة `.agent/` + تدقيق
- إضافة `PROJECT.md` / `TASKS.md` / `DECISIONS.md` / `ARCHITECTURE.md` /
  `CHANGELOG.md` / `CONTEXT.md` / `TODO.md` (متطلب PRD §17).
- تثبيت guards نتائج match الفارغة في `navigate` و`exitWizardMode`
  (استعادة لما كلّلته كتابة موازية) + رفع cache-bust إلى `match-fix2`.

## 2026-09-27 — (مدفوع سابقًا `1de4bab`)
- `POST /api/v1/match` + إصلاح قراءة نموذج Wizard المكرر + حراسة السباق
  (`matchSearchSeq`/`matchSearchPending`) + علامة Winner Jobs.

## 2026-09-26 — (مدفوع)
- تنظيف placeholders والهوية + حذف كارت التواصل الميت.

## 2026-09-25 — (مدفوع `bf5141f`)
- إصلاح 3 endpoints مكسورة + `.vercelignore` + نشر Vercel/Supabase الأول.
