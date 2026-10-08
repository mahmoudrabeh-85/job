# مهارات البحث عن الوظائف وروابطها — ماذا نأخذ منها لـ Winner Jobs
> آخر تحديث: 2026-10-08 — كل روابط GitHub/APIs verified (الأرقام من GitHub API).

## أولًا: مهارات الجلب (أين نجد الوظائف) + روابطها

| المهارة | الرابط | مفتاح؟ | عندنا؟ |
|---------|--------|--------|--------|
| ‏Greenhouse Boards API (مئات الشركات) | ‏https://github.com — ابحث `greenhouse board API` (عام، موثق) | بلا | ✅ |
| ‏Lever / Ashby / Arbeitnow / JazzHR APIs | ‏https://www.arbeitnow.com/api/job-board-api (يجمع ATS) | بلا | ✅ |
| ‏RemoteOK / Remotive / Jobicy / WWR | ‏https://remoteok.com/api — ‏https://remotive.com/api/remote-jobs | بلا | ✅ |
| ‏Hacker News Who's Hiring | ‏https://hn.algolia.com/api/v1 | بلا | ✅ ‏tools/hn_jobs.py |
| ‏LinkedIn Guest Jobs API | ‏https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search | بلا (حجم منخفض) | ✅ ‏tools/linkedin_jobs.py |
| ‏Adzuna API | ‏https://developer.adzuna.com | **مفتاح** (في `.env` المحلي) | ✅ الكود |
| ‏USAJobs API | ‏https://developer.usajobs.gov | مفتاح بريد مجاني | ❌ مقترح إضافته |
| ‏Indeed / Naukri / Glassdoor / Dice / ZipRecruiter | بلا API مجاني (OAuth/مدفوع) | — | روابط بحث فقط |

## ثانيًا: مهارات الوكلاء العشرة + روابطها (verified)

| # | الأداة | الرابط | النجوم/الرخصة | نأخذ منها |
|---|--------|--------|---------------|-----------|
| 1 | ‏Career-Ops | ‏https://github.com/career-ops-hq/career-ops | ‏73,810⭐ MIT (نشط اليوم) | فحص «الإعلان مفتوح؟» + Fit 1-5 + معالجة جماعية |
| 2 | ‏CareerAgent | ابحث GitHub: `CareerAgent` (تعددت الأسماء — تحقق قبل التثبيت) | ‏Beta/MIT | دعم 120+ بوابة ATS + Ollama محلي |
| 3 | ‏CareerPulse | ابحث GitHub: `CareerPulse` | — | ‏Match 0-100 + إضافة Chrome لملء ATS |
| 4 | ‏Job Hunter Team | ابحث GitHub: `Job Hunter Team multi-agent` | — | لا شيء (معماريًا مختلف) |
| 5 | ‏job_search_agent (RAG) | ابحث GitHub: `job_search_agent` | — | ‏RAG فوق السيرة + رسائل المجندين (بعد طبقة AI) |
| 6 | ‏JobPilot AI (suxrobGM/jobpilot — ‏65⭐ MIT) | ‏https://github.com/suxrobGM/jobpilot | ‏65⭐ MIT | حملات بحث + إعادة فحص المرفوض (بدون تقديم تلقائي) |
| 7 | ‏Job Application Agent (Sheets+Gemini) | ابحث GitHub: `Job Application Agent` | — | توليد PDF + الإيقاف قبل Submit (سياستنا نفسها) |
| 8 | ‏JobPilot v2 (تلقائي كامل) | — | — | 🚫 مرفوض (تقديم تلقائي = خطر ToS) |
| 9 | ‏Mirror (أسلوب الكتابة) | ابحث GitHub: `Mirror resume` (Pre-1.0) | — | بعد طبقة AI فقط |
| 10 | ‏CareerBridge | ابحث GitHub: `CareerBridge` | — | ⏳ بانتظار تفاصيله منك |
| + | ‏jobpilot-ai (PyPI 3.0.0, MIT, محلي 100%) | ‏https://pypi.org/project/jobpilot-ai | ‏MIT | جدولة محلية + Tailor بلا اختراع خبرات |
| + | ‏Indeed/FoundRole/Workopia (تطبيقات ChatGPT) | متجر GPT | — | كشف الوهمي + بحث لغة طبيعية (لاحقًا) |

## ثالثًا: المزايا التي سنضيفها لـ Winner Jobs (بالترتيب)

1. **فحص «الإعلان مفتوح؟»** (من Career-Ops): تحقق حي من رابط الوظيفة قبل التقديم + شارة ميت/حي.
2. **حملات بحث مع إعادة فحص** (من suxrobGM/jobpilot): البحث المحفوظ موجود — نضيف إعادة فحص المرفوض/المتخطى.
3. **توليد PDF** (من Job Application Agent): بقالب ATS نظيف، يتوقف قبل أي إرسال.
4. **إضافة Chrome لملء ATS** (من CareerPulse): البوكماركلت موجود كبداية → ترقية لاحقًا.
5. **USAJobs كمصدر** (مفتاح بريد مجاني): وظائف حكومية أمريكية عن بُعد.
6. **Arbeitnow UK + فلتر visa_sponsorship**: سطر واحد في الجالب.
7. **بعد طبقة AI**: تحضير مقابلات + RAG + أسلوب Mirror + بحث لغة طبيعية.
8. **محلي فقط (لا يدخل العامة أبدًا)**: Gmail/Telegram + مفاتيح Adzuna + السيرة الشخصية.
