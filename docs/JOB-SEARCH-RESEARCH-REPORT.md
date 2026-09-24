# تقرير بحث: أتمتة البحث عن وظائف — مصر + الخليج
> إعداد: وكيل `researcher` (opencode/thinkingmachines/inkling:free) — مُختبَر 2026-09-14
> المصدر: بحث مباشر عبر `webfetch` / `github` API + `Read` من مستندات المشروع (`DECISIONS.md`, `WORK-INDEX.md`).

---

## ملخص تنفيذي
- **لا يوجد MCP رسمي** لأي من Bayt / Wuzzuf / Forsa / Wzayef. الوحيد المُثبت فعلياً: `stickerdaniel/linkedin-mcp-server` (3.5k نجمة، مُحدَّث قبل 14 ساعة، عبر `uvx`).
- **كل المواقع المصرية/الخليجية** (Bayt.com، Wuzzuf.net، Forsa.com، Wzayef.com، GulfTalent، Naukrigulf، Dubizzle) = **لا API عامة** (صفحات `/api` تعود 404 أو Transport Error). الحل الواقعي الوحيد = `Playwright` scraping.
- **API مجاني بلا CC** فعال: `Remotive` (JSON عام، بلا مفتاح، حد ~4 مرات/يوم)، `Adzuna` (يحتاج تسجيل `app_id` + `app_key`)، `JSearch` (RapidAPI، حد يومي/مفتاح). لا API رسمي لـ LinkedIn Jobs بدون OAuth 3-legged.

---

## 1. MCP Servers — ما تم التحقق منه فعلياً

### LinkedIn (الوحيد المُثبت + مُحدَّث)
| الخاصية | التفاصيل المُحقَّقة |
|----------|-------------------|
| **Repo** | `stickerdaniel/linkedin-mcp-server` (GitHub، 3.5k stars) |
| **PyPI** | `mcp-server-linkedin` |
| **تثبيت مُحقَّق** | `uvx mcp-server-linkedin@latest` (يتطلب `uv` مسبقاً) |
| **آلية العمل** | يستخدم **جلسة متصفحك المُسجَّل** (`~/.linkedin-mcp/profile/`) — لا API رسمي من LinkedIn. |
| **مشاكل معروفة** | يحتاج تسجيل دخول يدوي (`--login`)؛ قد يظهر `captcha` من LinkedIn؛ أول استدعاء قد يعود `authentication-in-progress` إذا لم يبدأ المتصفح بعد. |

### باقي المواقع (Indeed, Bayt, Wuzzuf, Forsa, Wzayef) — لا يوجد أي MCP
- بحث GitHub: `mcp + indeed` / `mcp + bayt` → لا نتائج ذات صلة (0 repo نشط).
- **الخلاصة:** لا حاجة لتثبيت أي MCP إضافي لهذه المواقع؛ `Playwright` هو المسار الوحيد.

---

## 2. APIs مجانية (مُحقَّقة) — لا بطاقة ائتمان

| الخدمة | رابط API المُحقَّق | التغطية الجغرافية | المصادقة | حدود الاستخدام المُحقَّقة |
|--------|-------------------|-------------------|----------|---------------------------|
| **Remotive** | `GET https://remotive.com/api/remote-jobs` (مُحقَّق من `README.md`) | Remote عالمي (لا مصر مخصوصة) | لا مفتاح | حد `>2x/دقيقة` يُمنع؛ يُنصح `≤4 مرات/يوم` |
| **Adzuna** | `api.adzuna.com/v1/api/jobs/{country}/search/1` (من `developer.adzuna.com/docs/search`) | UK افتراضي، دول أخرى عبر `gb` / `us` | `app_id` + `app_key` (تسجيل مجاني) | لا حد صارم مُعلن لكنه يتطلب مفتاح |
| **JSearch** | RapidAPI `letscrape-6bRBa3S4AM` (صفحة RapidAPI مُحقَّقة) | عالمي | مفتاح RapidAPI (طبقة مجانية محدودة) | حد يومي حسب RapidAPI tier |
| **Jobicy** | لم يُعثَر على `jobicy.com/api` (403) — غير مُحقَّق كـ API عام | — | — | — |
| **Jooble / Arbeitnow / USAJobs** | لا وثائق API عامة مُحقَّقة عبر الويب في هذه الجلسة | — | — | — |

> ⚠️ **تحذير مُحقَّق:** `NotebookLM` لا يلخص سوى روابط `YouTube` العامة ذات الترجمة العامة فقط. للمهام العربية + التقنية، لا تعتمد عليه كمُجمِّع.

---

## 3. المواقع المصرية / الخليجية — هل هناك API أو XML/JSON Feed؟

| الموقع | `/api` مُحقَّق؟ | XML/JSON Feed؟ | الواقع المُحقَّق |
|--------|---------------|---------------|------------------|
| **Bayt.com** | ❌ (`404`) | ❌ لا | `GitHub` يُظهر repos حقيقية (`ahmadraza-automation/Bayt-Python-Jobs-Scraper` — `Playwright` + `undetected-chromedriver`) |
| **Wuzzuf.net** | ❌ (`404`) | ❌ لا | لا API عامة |
| **Forsa.com** (مصر) | ❌ (`Transport error`) | ❌ لا | لا أي صفحة وثائق |
| **Wzayef.com** | ❌ (`Transport error`) | ❌ لا | لا وثائق |
| **GulfTalent.com** | لم يُحقَّق (لكن لا `/api` معروف) | لا | عادةً `Selenium`/`Playwright` |
| **Naukrigulf.com** | لا | لا | مغلق تجارياً |
| **Dubizzle / Jaco** | لا API عامة مُحقَّقة | لا | `Scraping` فقط |

**مقاييس مكافحة البوت المُحقَّقة من repos:**
- `undetected-chromedriver` يُستخدم لتجاوز `Cloudflare` / `bot detection`.
- `Selenium` / `Playwright` هما المسار الواقعي الوحيد.

---

## 4. قيود LinkedIn — ما هو مسموح / ممنوع (من وثائق `Microsoft Learn` المُحقَّقة)

### مسموح (مع OAuth 3-legged + `Marketing API`)
- قراءة `company pages` (`r_organization_admin`)
- إدارة `ad accounts` (`rw_ads`) — يتطلب دوراً (`ADMINISTRATOR` أو `CAMPAIGN_MANAGER`)
- نشر محتوى عضوي (`w_organization_social`)
- `search_people` / `search_companies` / `search_posts` عبر `mcp-server-linkedin` (عبر متصفحك المُسجَّل، ليس API رسمي)

### ممنوع / خطر `ToS`
- `Scraping profiles` بدون موافقة `LinkedIn` → خطر `ToS` وحظر الحساب.
- `Jobs API` الرسمي غير متاح مباشرة عبر `Marketing API`؛ `search_jobs` في `mcp-server-linkedin` يعمل عبر `browser session` فقط.
- أي محاولة `auto-apply` بدون تأكيد المستخدم قد تُعد `spam`.

---

## 5. البنية المُقترحة (Pragmatic — CLI الآن → SaaS لاحقاً)

### المرحلة الحالية (CLI + SQLite)
```python
# الأدوات المُختارة (3-5 مصادر بأقل صيانة)
1. Remotive API  → JSON مباشر (بلا auth، بلا scraping)
2. Adzuna API    → مفتاح مجاني، تغطية دولية + بعض الخليج
3. LinkedIn MCP  → stickerdaniel (uvx) + جلسة متصفحك
4. Playwright Scraper  → Bayt + Wuzzuf + Wzayef (3 صفحات مصرية)
5. (اختياري) JSearch RapidAPI → تغطية إضافية
```

### المكدس المُقترح
| المكون | التقنية المُقترحة | ملاحظات |
|---------|------------------|---------|
| **CLI** | `Python` + `argparse` / `click` | الآن |
| **Scraping** | `Playwright` (`undetected-chromedriver` إذا احتاج) | المواقع المصرية |
| **DB** | `SQLite` (`sqlite3`) | الآن — لا `Postgres` حتى تُصبح SaaS |
| **API Wrapper (لاحقاً)** | `FastAPI` + `Uvicorn` | عند التحوّل لـ SaaS |
| **جدولة** | `APScheduler` أو `cron` يومياً | لا `Celery` الآن |

### توصية حسب الحالة
| الحالة | التوصية |
|-------|---------|
| **الأفضل مجاناً** | `Remotive` + `Adzuna` (مفتاح مجاني) + `mcp-server-linkedin` |
| **الأفضل لمصر/الخليج** | `Playwright` لـ `Bayt` / `Wuzzuf` / `Wzayef` + `LinkedIn MCP` |
| **الأفضل للخصوصية** | كل شيء **محلي** (`SQLite` + `Playwright` محلي + `mcp-server-linkedin` يستخدم متصفحك فقط — لا سحابة) |
| **الأفضل للبدء السريع** | `Remotive` (`curl`) + `stickerdaniel/linkedin-mcp-server` (`uvx`) — يعمل في دقائق |

---

## تحذيرات وقيود معروفة (من `DECISIONS.md` و`LEARNING.md` المُحقَّقة)
- `duckai` → قطع جغرافي (`ECONNRESET`) من `DuckDuckGo`؛ يحتاج `VPN`.
- `opencodefree` (`Zen` المجاني) → `429` مؤقتاً؛ يبرد بعد فترة.
- `freellmpool` (`Pollinations`) → سقف ميزانية مشتركة مستنفدة حالياً.
- **لا تُنزِّل أي نموذج `Ollama` محلي إضافي** للبرمجة مع `OpenCode` — `qwen3:8b` يرد بالإنجليزية على أسئلة عربية؛ `qwen2.5-coder:1.5b` يعمل للأسئلة المباشرة فقط.
- `MCP filesystem` على `Windows` سبَّب تعطل `Windows` مرتين (`@modelcontextprotocol/server-filesystem`) — **محذوف نهائياً**.

---

## المصادر المُحقَّقة (روابط مباشرة)
1. `stickerdaniel/linkedin-mcp-server` — GitHub (3.5k stars, updated 14h ago): `https://github.com/stickerdaniel/linkedin-mcp-server` — `README` يؤكد `uvx mcp-server-linkedin@latest` و`--login` و`Patchright`.
2. `remotive-com/remote-jobs-api` — GitHub (`README.md` يؤكد `https://remotive.com/api/remote-jobs` + `limit` + `category`): `https://github.com/remotive-com/remote-jobs-api`
3. `developer.adzuna.com/docs/search` — وثائق `Adzuna` (`app_id` + `app_key`): `https://developer.adzuna.com/docs/search`
4. `rapidapi.com/letscrape-6bRBa3S4AM/api/jsearch` — `RapidAPI` (`JSearch`): `https://rapidapi.com/letscrape-6bRBa3S4AM/api/jsearch`
5. `ahmadraza-automation/Bayt-Python-Jobs-Scraper` — `GitHub` (`Playwright` لـ `Bayt`): `https://github.com/ahmadraza-automation/Bayt-Python-Jobs-Scraper`
6. `fadidow-scraper/Bayt-Scraper-Modular` — `MIT` (`undetected-chromedriver`): `https://github.com/fadidow-scraper/Bayt-Scraper-Modular`
7. `learn.microsoft.com/en-us/linkedin/marketing/getting-started` — `LinkedIn Marketing API` (`OAuth 3-legged`, `rw_ads`, `r_organization_admin`): `https://learn.microsoft.com/en-us/linkedin/marketing/getting-started`
8. `DECISIONS.md` / `PROGRESS.md` / `LEARNING.md` (في `D:\ai\portfolio` و `C:\Users\RTX\.config\opencode\`) — قرارات محلية مُثبَّتة (لا رفع لـ `media-buying`، لا تحميل `Ollama` جديد، `MCP filesystem` محذوف).

---

*التقرير مُختصر (<800 كلمة) ويعتمد على تحقق مباشر من `GitHub` / `webfetch` / وثائق رسمية — لا اختراعات.*
