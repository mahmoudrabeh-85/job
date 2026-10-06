# ARCHITECTURE.md — خريطة النظام (تدقيق Phase 0 — 2026-09-27)

## Stack
- **Backend:** FastAPI 0.115 + uvicorn (Python 3.12) — `app/main.py` المدخل.
- **Frontend:** SPA بلا build (vanilla JS ~1680 سطرًا `frontend/app.js` + `style.css`)
  عربي/إنجليزي + RTL/LTR — تُقدَّم عبر catch-all في نفس الخادم (same-origin).
- **DB:** Supabase Postgres (إنتاج، eu-central-1) + SQLite محليًا (`data/jobs.db`
  محجوب عن git). طبقة تجريد: `app/database_factory.py` + `database.py` + `database_pg.py`.
- **النشر:** Vercel serverless (`fra1`) — scope `mahoud-85-org` إلزامي.
  ملفات Render/Docker قديمة (legacy) ما زالت في الريبو.

## مخطط الوحدات
```text
frontend/index.html + app.js + style.css   (SPA: 7 صفحات)
        │ same-origin fetch
        ▼
app/main.py ── routers ──┬── jobs.py      (jobs/search/stats/match/applications)
                         ├── analysis.py   (analyze/hr-template/swot/skills)
                         ├── vet.py        (company-vet heuristic محلي)
                         ├── refresh.py    (admin refresh — غير مدفوع بعد)
                         └── cv_builder.py (build/ats-check — غير مدفوع بعد)
        │                 + legacy shims (/api/search, /api/cv_list, cv_generate→501)
        ▼
database_factory → Postgres (إنتاج) / SQLite (محلي)
        جدول jobs (14 عمودًا — بلا وصف وظيفي!) + جدول applications (بذرة CRM)
```

## تدفق المطابقة الحالي (heuristic — بلا LLM)
`POST /api/v1/match {skills, years, field}` → مطابقة كلمات ضد
(title/company/location/category) + seniority-fit من العنوان →
`{items, total, filters}`. الواجهة تحمي النتائج بـ
`matchSearchSeq` + `matchSearchPending` + `matchSearchCompleted`.

## أدوات CLI (tools/ — محلية)
`job_aggregator.py` (جمع) + `smart_scorer.py` (تقييم) + `job_analyzer.py` +
`job_swot.py` + `custom_sources.py` + `direct_employers.py` (غير مدفوع) +
`auto_apply.py` (آمن: وظيفة واحدة، بلا ضغط إرسال) + `generate_html_report.py`.

## تكاملات AI
**لا يوجد أي تكامل LLM في الخادم** (فجوة PRD §15/§7 — موثقة كأولوية Phase 1).
