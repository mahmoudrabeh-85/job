#!/usr/bin/env python3
"""
job_aggregator.py — مُجمِّع الوظائف الذكي v2
─────────────────────────────────────────────
يجمع وظائف من مصادر متعددة + يقيّمها ذكياً حسب ملف المُرشح
+ يحلل متطلبات الوظيفة vs إمكانات الباحث

المصادر: RemoteOK / WeWorkRemotely / Remotive / Jobicy (+ مواقع مخصصة)
التقييم: AI-powered scoring基于 CV + تفضيلات المستخدم
التحليل: مطابقة المتطلبات مع المهارات الفعلية

Usage:
  python job_aggregator.py --pages 1 --top 20
  python job_aggregator.py --smart        # تقييم ذكي مع تحليل
  python job_aggregator.py --profile      # عرض الملف الشخصي
  python job_aggregator.py --analyze-all  # تحليل كل الوظائف
"""
import argparse
import json
import re
import sqlite3
import sys
import urllib.request
from datetime import date
from pathlib import Path

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "data"
DB_PATH = DATA_DIR / "jobs.db"
PROFILE_FILE = DATA_DIR / "candidate_profile.json"
SOURCES_FILE = DATA_DIR / "custom_sources.json"
REPORT_PATH = DATA_DIR / f"latest_report_{date.today().isoformat()}.md"

REMOTIVE_URL = "https://remotive.com/api/remote-jobs?limit=50&page={page}"
REMOTE_OK_URL = "https://remoteok.com/api"
WWR_URL = "https://weworkremotely.com/remote-jobs.rss"
JOBICY_URL = "https://jobicy.com/api/v2/remote-jobs?count={count}"
ADZUNA_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}?app_id={app_id}&app_key={app_key}&results_per_page={rpp}&what={what}&content-type=application/json"
ENV_FILE = DATA_DIR / ".env"


def _load_adzuna_keys() -> tuple[str, str] | None:
    """Load Adzuna app_id/app_key from data/.env. Returns None if missing."""
    if not ENV_FILE.exists():
        return None
    app_id = app_key = None
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("ADZUNA_APP_ID="):
            app_id = line.split("=", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("ADZUNA_APP_KEY="):
            app_key = line.split("=", 1)[1].strip().strip('"').strip("'")
    return (app_id, app_key) if app_id and app_key else None

# --------------------------------------------------------------------------
# Candidate Profile (from CV)
# --------------------------------------------------------------------------
DEFAULT_PROFILE = {
    "name": "[Your Name]",
    "title": "Procurement Manager | Sales Manager | Supply Chain Expert",
    "experience_years": 15,
    "location": "Cairo, Egypt",
    "languages": {"arabic": "native", "english": "b2"},

    # ─── المهارات الأساسية (وزن 1-10) ──────────────────────────────
    "core_skills": {
        # Procurement & Supply Chain
        "procurement": 10, "purchasing": 10, "buyer": 9,
        "vendor negotiation": 10, "contract management": 9,
        "sourcing": 9, "strategic sourcing": 9,
        "supply chain": 10, "supply chain management": 10,
        "inventory management": 9, "logistics": 8, "distribution": 9,
        "warehouse": 7, "quality control": 7, "gdp": 6,
        # Sales & Business
        "sales": 9, "business development": 8, "account management": 8,
        "key account": 8, "revenue": 7, "client relationships": 8,
        # Tools (أُلغي Oracle/ERP من المهارات 2026-09-16 بطلب المستخدم)
        "excel": 8, "ms office": 7, "powerpoint": 6,
        # Industry
        "pharmaceutical": 10, "pharma": 10, "medical": 7, "healthcare": 7,
        "fmcg": 6, "distribution": 9, "trading": 8,
        # Management
        "operations": 8, "management": 8, "team leadership": 8,
        "strategic planning": 7, "cost reduction": 9, "budget": 7,
        "compliance": 7, "regulatory": 6,
    },

    # ─── المهارات المستبعدة (لا أملكها) ──────────────────────────────
    "exclude_skills": [
        # برمجة
        "python developer", "javascript developer", "react developer",
        "angular developer", "vue developer", "node.js developer",
        "java developer", "c++ developer", "php developer", "ruby developer",
        "golang developer", "rust developer", "swift developer",
        "frontend developer", "backend developer", "full stack developer",
        "fullstack developer", "devops engineer", "site reliability",
        "data scientist", "data engineer", "machine learning engineer",
        "ai engineer", "cloud engineer", "database administrator",
        "system administrator", "network engineer", "cybersecurity",
        "information security", "blockchain developer",
        # تصميم
        "ui/ux designer", "ux designer", "ui designer", "graphic designer",
        "web designer", "product designer", "interaction designer",
        "figma designer", "sketch designer",
        # هندسة
        "software engineer", "hardware engineer", "electrical engineer",
        "mechanical engineer", "civil engineer", "architect",
        # مهن غير مرتبطة
        "teacher", "professor", "nurse", "doctor", "lawyer",
        "content writer", "copywriter", "social media manager",
        "translator", "interpreter",
    ],

    # ─── أنواع الوظائف المستهدفة ──────────────────────────────────
    "target_roles": [
        "procurement manager", "procurement specialist", "procurement officer",
        "purchasing manager", "purchasing specialist", "buyer",
        "supply chain manager", "supply chain analyst", "supply chain specialist",
        "logistics manager", "logistics coordinator",
        "vendor manager", "supplier manager", "category manager",
        "sales manager", "sales director", "business development manager",
        "account manager", "key account manager", "commercial manager",
        "operations manager", "operations director",
        "distribution manager", "warehouse manager",
        "pharmaceutical sales", "medical sales", "healthcare sales",
        "trade marketing manager", "trade marketing specialist",
        "business analyst", "process improvement", "quality manager",
    ],

    # ─── الصناعات المستهدفة ──────────────────────────────────────
    "target_industries": [
        "pharmaceutical", "pharma", "healthcare", "medical",
        "distribution", "trading", "fmcg", "consumer goods",
        "retail", "supply chain", "logistics", "manufacturing",
        "chemical", "cosmetics", "food & beverage",
    ],

    # ─── تفضيلات العمل ──────────────────────────────────────────
    "work_preferences": {
        "work_type": ["remote", "hybrid", "onsite"],
        "locations": ["remote", "egypt", "uae", "saudi", "gulf", "worldwide"],
        "salary_min_annual_usd": 12000,
        "salary_preferred_annual_usd": 24000,
        "max_relocation": "gulf",  # egypt → gulf ok, usa/europe no
    },

    # ─── كلمات العنوان فقط (لا تُحسب في الوصف) ──────────────────
    "title_only_keywords": {
        "sales": 7, "manager": 6, "director": 8, "head": 7,
        "lead": 6, "specialist": 5, "executive": 6, "consultant": 5,
        "advisor": 5, "coordinator": 4, "representative": 5,
        "officer": 5, "analyst": 4,
    },
}


def load_profile() -> dict:
    if PROFILE_FILE.exists():
        try:
            return json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return DEFAULT_PROFILE.copy()


def save_profile(profile: dict):
    DATA_DIR.mkdir(exist_ok=True)
    PROFILE_FILE.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------
# Smart Exclusion — استبعاد ذكي
# --------------------------------------------------------------------------
def should_exclude(job: dict, profile: dict = None) -> tuple[bool, str]:
    """
    Check if job should be excluded entirely.
    Returns (excluded, reason)
    """
    if profile is None:
        profile = load_profile()

    title = (job.get("title") or "").lower()
    desc = (job.get("description") or "").lower()
    tags = " ".join(job.get("tags") or []).lower()

    # ─── 1. استبعاد بالعنوان (مهارات لا أملكها) ─────────────────────
    for exclude in profile.get("exclude_skills", []):
        if exclude in title:
            return True, f"❌ مهارة مستبعدة في العنوان: '{exclude}'"

    # ─── 2. استبعاد وظائف البرمجة/التصميم ──────────────────────────
    tech_in_title = ["developer", "engineer", "programmer", "coder",
                     "architect", "devops", "sre", "dba", "sysadmin",
                     "designer", "design"]
    for tech in tech_in_title:
        if tech in title:
            # تحقق: هل ذُكرت مهارة مبيعات/مشتريات في العنوان؟
            has_sales = any(w in title for w in ["sales", "procurement", "supply", "vendor", "business"])
            if not has_sales:
                return True, f"❌ وظيفة تقنية: '{tech}'"

    # ─── 3. استبعاد إذا كانت الوظيفة تتطلب مهارة تقنية + لا توجد مهاراتنا ──
    tech_keywords = ["python", "javascript", "react", "angular", "vue",
                     "node.js", "java", "c++", "php", "ruby", "golang",
                     "rust", "swift", "kotlin", "typescript"]
    our_keywords = ["sales", "procurement", "supply", "vendor", "negotiation",
                    "business", "commercial", "operations", "management",
                    "pharmaceutical", "medical", "healthcare", "distribution",
                    "account", "strategy", "purchasing", "inventory", "logistics"]

    tech_count = sum(1 for kw in tech_keywords if kw in f"{title} {tags}")
    our_count = sum(1 for kw in our_keywords if kw in f"{title} {tags}")

    if tech_count >= 2 and our_count < 2:
        return True, f"❌ وظيفة تقنية ({tech_count} مهارة تقنية، {our_count} مهارة مطابقة)"

    return False, ""


# --------------------------------------------------------------------------
# Smart Scoring — تقييم ذكي
# --------------------------------------------------------------------------
def smart_score(job: dict, profile: dict = None) -> tuple[int, dict]:
    """
    AI-powered scoring based on candidate profile.
    Returns (score, details_dict)
    """
    if profile is None:
        profile = load_profile()

    title = (job.get("title") or "").lower()
    desc = (job.get("description") or "").lower()[:5000]
    tags = " ".join(job.get("tags") or []).lower()
    category = (job.get("category") or "").lower()
    company = (job.get("company_name") or "").lower()
    location = (job.get("location") or "").lower()
    salary_annual = job.get("salary_annual")

    hay_title = f"{title} {tags} {category}"
    hay_all = f"{hay_title} {desc}"

    details = {
        "skill_score": 0,
        "role_score": 0,
        "industry_score": 0,
        "title_score": 0,
        "salary_score": 0,
        "location_score": 0,
        "penalty": 0,
        "matched_skills": [],
        "matched_roles": [],
        "matched_industries": [],
        "warnings": [],
    }

    # ─── 1. المهارات الأساسية (0-40) ────────────────────────────────
    skill_points = 0
    for skill, weight in profile.get("core_skills", {}).items():
        if skill in hay_title:
            skill_points += weight * 3
            details["matched_skills"].append(f"✅ {skill} (عنوان)")
        elif skill in hay_all:
            skill_points += weight
            details["matched_skills"].append(f"📌 {skill} (وصف)")
    details["skill_score"] = min(skill_points, 40)

    # ─── 2. نوع الوظيفة (0-25) ──────────────────────────────────────
    role_points = 0
    for role in profile.get("target_roles", []):
        role_lower = role.lower()
        if role_lower in title:
            role_points += 15
            details["matched_roles"].append(f"🎯 {role}")
        elif any(w in title for w in role_lower.split() if len(w) > 3):
            role_points += 5
            details["matched_roles"].append(f"📌 {role}")
    details["role_score"] = min(role_points, 25)

    # ─── 3. الصناعة (0-15) ──────────────────────────────────────────
    industry_points = 0
    for industry in profile.get("target_industries", []):
        if industry in hay_all:
            industry_points += 8
            details["matched_industries"].append(industry)
    details["industry_score"] = min(industry_points, 15)

    # ─── 4. كلمات العنوان (0-10) ────────────────────────────────────
    title_points = 0
    for kw, weight in profile.get("title_only_keywords", {}).items():
        if kw in hay_title:
            title_points += weight
    details["title_score"] = min(title_points, 10)

    # ─── 5. الراتب (0-10) ──────────────────────────────────────────
    prefs = profile.get("work_preferences", {})
    if salary_annual:
        preferred = prefs.get("salary_preferred_annual_usd", 24000)
        minimum = prefs.get("salary_min_annual_usd", 12000)
        if salary_annual >= preferred:
            details["salary_score"] = 10
        elif salary_annual >= minimum:
            details["salary_score"] = 5
        else:
            details["salary_score"] = -5
            details["warnings"].append(f"⚠️ راتب منخفض: ${salary_annual:,.0f}/سنة")

    # ─── 6. الموقع (0-5) ───────────────────────────────────────────
    if "remote" in location:
        details["location_score"] = 5
    elif "egypt" in location or "cairo" in location:
        details["location_score"] = 3
    elif any(g in location for g in ["uae", "saudi", "gulf", "dubai", "abu dhabi"]):
        details["location_score"] = 4

    # ─── 7. غرامات ──────────────────────────────────────────────────
    tech_penalties = ["python", "javascript", "react", "angular", "node.js",
                      "java", "c++", "php", "ruby", "golang", "rust"]
    for tech in tech_penalties:
        if tech in title:
            details["penalty"] -= 10
            details["warnings"].append(f"⚠️ مهارة تقنية في العنوان: {tech}")

    if len(desc) < 100:
        details["penalty"] -= 3
        details["warnings"].append("⚠️ وصف قصير جداً")

    total = (details["skill_score"] + details["role_score"] +
             details["industry_score"] + details["title_score"] +
             details["salary_score"] + details["location_score"] +
             details["penalty"])

    return max(total, 0), details


# --------------------------------------------------------------------------
# Job Requirements Analysis — تحليل متطلبات الوظيفة
# --------------------------------------------------------------------------
def analyze_match(job: dict, profile: dict = None) -> dict:
    """
    تحليل تفصيلي: متطلبات الوظيفة vs إمكانات الباحث
    Returns dict with match analysis
    """
    if profile is None:
        profile = load_profile()

    title = (job.get("title") or "").lower()
    desc = (job.get("description") or "").lower()
    tags = " ".join(job.get("tags") or []).lower()
    hay_all = f"{title} {tags} {desc}"

    core = profile.get("core_skills", {})

    # ─── استخراج المتطلبات من الوظيفة ────────────────────────────────
    job_requirements = []

    # مهارات مطلوبة في العنوان
    title_skills = ["procurement", "purchasing", "buyer", "supply chain",
                    "sales", "vendor", "negotiation", "contract",
                    "inventory", "logistics", "distribution", "pharmaceutical",
                    "erp", "oracle", "sap", "odoo", "operations", "management"]
    for skill in title_skills:
        if skill in title:
            job_requirements.append({"skill": skill, "where": "title", "critical": True})

    # مهارات مطلوبة في الوصف
    desc_skills = ["procurement", "purchasing", "supply chain", "vendor management",
                   "negotiation", "contract management", "inventory management",
                   "logistics", "distribution", "pharmaceutical", "medical",
                   "erp", "oracle", "sap", "sales", "business development",
                   "account management", "operations", "management",
                   "leadership", "strategic planning", "cost reduction",
                   "budget management", "compliance", "quality control",
                   "excel", "powerpoint", "ms office"]
    for skill in desc_skills:
        if skill in desc and skill not in [r["skill"] for r in job_requirements]:
            job_requirements.append({"skill": skill, "where": "description", "critical": False})

    # ─── حساب التطابق ──────────────────────────────────────────────
    matched = []
    missing = []
    partial = []

    for req in job_requirements:
        skill = req["skill"]
        if skill in core:
            level = core[skill]
            if level >= 7:
                matched.append({"skill": skill, "level": level, "critical": req["critical"]})
            else:
                partial.append({"skill": skill, "level": level, "critical": req["critical"]})
        else:
            missing.append({"skill": skill, "critical": req["critical"]})

    # ─── حساب نسبة التطابق ──────────────────────────────────────────
    total_required = len(job_requirements)
    if total_required == 0:
        match_pct = 0
    else:
        matched_count = len(matched) + len(partial) * 0.5
        match_pct = round((matched_count / total_required) * 100)

    # ─── التصنيف ──────────────────────────────────────────────────
    if match_pct >= 80:
        rating = "مطابق تماماً"
        rating_color = "🟢"
    elif match_pct >= 60:
        rating = "مطابق جزئياً"
        rating_color = "🟡"
    elif match_pct >= 40:
        rating = "مطابق ضعيف"
        rating_color = "🟠"
    else:
        rating = "غير مطابق"
        rating_color = "🔴"

    # ─── التوصيات ──────────────────────────────────────────────────
    recommendations = []
    if missing:
        critical_missing = [m for m in missing if m["critical"]]
        if critical_missing:
            recommendations.append(f"❌ مهارات حرجة ناقصة: {', '.join(m['skill'] for m in critical_missing)}")
        if len(missing) > len(critical_missing):
            recommendations.append(f"⚠️ مهارات عامة ناقصة: {len(missing) - len(critical_missing)} مهارة")
    if partial:
        recommendations.append(f"📌 مهارات بمستوى منخفض: {', '.join(p['skill'] for p in partial)}")
    if matched:
        recommendations.append(f"✅ مهارات مطابقة: {len(matched)} مهارة")
    if not missing and not partial:
        recommendations.append("🎯 تطابق مثالي — تتقدم فوراً!")

    return {
        "match_percentage": match_pct,
        "rating": rating,
        "rating_color": rating_color,
        "total_requirements": total_required,
        "matched": matched,
        "partial": partial,
        "missing": missing,
        "recommendations": recommendations,
        "job_requirements": job_requirements,
    }


# --------------------------------------------------------------------------
# Fetching — جمع الوظائف
# --------------------------------------------------------------------------
def fetch_remotive(page: int = 1) -> list[dict]:
    url = REMOTIVE_URL.format(page=page)
    req = urllib.request.Request(url, headers={"User-Agent": "job-hunt-aggregator/2.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("jobs", [])


def _fix_mojibake(text: str) -> str:
    if not text:
        return text
    try:
        return text.encode("latin-1", "ignore").decode("utf-8", "ignore")
    except Exception:
        return text


def _extract_company(title: str, company: str) -> str:
    """Fallback: WWR puts company as prefix before colon in title."""
    if company and company.strip():
        return company.strip()
    if not title or ":" not in title:
        return company or ""
    prefix = title.split(":", 1)[0].strip()
    # avoid mistaking location-like prefixes; require at least 2 chars and not too long
    if 2 <= len(prefix) <= 80:
        return prefix
    return company or ""


def fetch_remoteok() -> list[dict]:
    req = urllib.request.Request(REMOTE_OK_URL, headers={"User-Agent": "job-hunt-aggregator/2.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    jobs = []
    for item in data[1:]:
        jobs.append({
            "id": int(item.get("id") or 0),
            "title": _fix_mojibake(item.get("position") or item.get("title") or ""),
            "company_name": _fix_mojibake(item.get("company") or ""),
            "location": "Remote",
            "salary": _fix_mojibake(item.get("salary") or ""),
            "url": item.get("url") or "",
            "category": (item.get("tags") or ["remote"])[0] if item.get("tags") else "remote",
            "tags": item.get("tags") or [],
            "description": _fix_mojibake(item.get("description") or ""),
            "publication_date": (item.get("date") or "")[:10],
        })
    return jobs


def fetch_weworkremotely() -> list[dict]:
    import xml.etree.ElementTree as ET
    req = urllib.request.Request(WWR_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read()
    root = ET.fromstring(body)
    jobs = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        company = (item.findtext("company") or "").strip()
        company = _extract_company(title, company)
        link = (item.findtext("link") or "").strip()
        cat = (item.findtext("category") or "").strip()
        desc = (item.findtext("description") or "").strip()
        pub = (item.findtext("pubDate") or "")[:16]
        jobs.append({
            "id": None,
            "title": title,
            "company_name": company,
            "location": "Remote",
            "salary": "",
            "url": link,
            "category": cat,
            "tags": [cat],
            "description": re.sub(r"<[^>]+>", " ", desc),
            "publication_date": pub,
        })
    return jobs


def fetch_jobicy(count: int = 200) -> list[dict]:
    """Jobicy public API — no key, structured JSON with salary + company.
    Credit: Jobicy must be credited with direct link; apply buttons use original URL."""
    url = JOBICY_URL.format(count=max(1, min(count, 200)))
    req = urllib.request.Request(url, headers={"User-Agent": "job-hunt-aggregator/2.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    jobs = []
    for item in data.get("jobs", []):
        title = (item.get("jobTitle") or "").strip()
        company = (item.get("companyName") or "").strip()
        company = _extract_company(title, company)
        geo = (item.get("jobGeo") or "Remote").strip()
        jtype = (item.get("jobType") or [""])[0] if isinstance(item.get("jobType"), list) else (item.get("jobType") or "")
        industry = item.get("jobIndustry") or []
        cat = industry[0] if industry else "remote"
        smin, smax, scur = item.get("salaryMin"), item.get("salaryMax"), (item.get("salaryCurrency") or "USD")
        salary = ""
        if smin or smax:
            salary = f"{smin or ''}-{smax or ''} {scur} yearly".strip()
        desc_html = item.get("jobDescription") or item.get("jobExcerpt") or ""
        jobs.append({
            "id": item.get("id"),
            "title": title,
            "company_name": company,
            "location": geo,
            "salary": salary,
            "url": item.get("url") or "",
            "category": cat,
            "tags": industry if isinstance(industry, list) else [cat],
            "description": re.sub(r"<[^>]+>", " ", desc_html)[:8000],
            "publication_date": (item.get("pubDate") or "")[:10],
        })
    return jobs


def fetch_adzuna(country: str = "gb", what: str = "procurement supply chain sales", rpp: int = 50) -> list[dict]:
    """Adzuna API — free tier requires app_id + app_key from data/.env.
    No keys → returns [] (source skipped silently with a note).
    Note: `where` is intentionally omitted — Adzuna needs a real location
    and 'Remote' returns 0 results. UK-wide results include remote jobs;
    the smart scorer ranks them (+5 for remote in location text)."""
    keys = _load_adzuna_keys()
    if not keys:
        print("[i] Adzuna: no keys in data/.env — skipped (register at https://developer.adzuna.com)", file=sys.stderr)
        return []
    app_id, app_key = keys

    from urllib.parse import quote

    url = ADZUNA_URL.format(
        country=country, page=1, app_id=app_id, app_key=app_key,
        rpp=max(1, min(rpp, 50)), what=quote(what),
    )
    req = urllib.request.Request(url, headers={"User-Agent": "job-hunt-aggregator/2.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    jobs = []
    seen = set()
    for item in data.get("results", []):
        title = (item.get("title") or "").strip()
        if not title:
            continue
        # تخطي ضجيج التوظيف/الامتياز التجاري ( franchise مكرر لكل مدينة)
        tl = title.lower()
        if "franchise" in tl or "recruitment consultant" in tl or "trainee recruitment" in tl:
            continue
        comp = (item.get("company") or {}).get("display_name") or ""
        # إزالة تكرار نفس الإعلان لمدن مختلفة (العنوان بعد حذف " - المدينة")
        norm_title = re.sub(r"\s+-\s+[A-Z][A-Za-z ]+$", "", title).strip().lower()
        dup_key = (norm_title, comp.strip().lower())
        if dup_key in seen:
            continue
        seen.add(dup_key)
        loc = (item.get("location") or {}).get("display_name") or "Remote"
        smin, smax = item.get("salary_min"), item.get("salary_max")
        salary = ""
        if smin or smax:
            salary = f"{int(smin or 0)}-{int(smax or 0)} {country.upper()} yearly"
        cat = item.get("category") or {}
        cat_label = cat.get("label") if isinstance(cat, dict) else ""
        cat_tag = cat.get("tag") if isinstance(cat, dict) else ""
        jobs.append({
            "id": item.get("id"),
            "title": title,
            "company_name": _extract_company(title, comp),
            "location": loc,
            "salary": salary,
            "url": item.get("redirect_url") or "",
            "category": cat_label or "remote",
            "tags": [t for t in [cat_label, cat_tag] if t],
            "description": (item.get("description") or "")[:8000],
            "publication_date": (item.get("created") or "")[:10],
        })
    return jobs
KEYWORDS = {
    "procurement": 3, "purchasing": 3, "purchase": 2, "buyer": 2,
    "supply chain": 3, "supply-chain": 3, "logistics": 2, "sourcing": 2,
    "vendor": 1, "supplier": 1, "inventory": 1, "warehouse": 1,
    "distribution": 2, "pharma": 3, "pharmaceutical": 3,
    "operations manager": 2, "media buyer": 3, "media buying": 3,
    "account manager": 2, "business development": 2,
}
TITLE_ONLY_KEYWORDS = {
    "sales": 2, "selling": 1, "medical": 2, "healthcare": 1,
    "operations": 1, "marketing": 1, "digital marketing": 1, "analyst": 1,
}
EXCLUDE_TITLES = ["software engineer", "frontend", "backend", "full-stack",
                  "data scientist", "data engineer", "devops", "qa engineer",
                  "ux ", "ui designer", "game developer", "intern"]


def score_job(job: dict) -> tuple[int, str]:
    title = (job.get("title") or "").lower()
    tags = " ".join(job.get("tags") or []).lower()
    category = (job.get("category") or "").lower()
    desc = (job.get("description") or "").lower()[:8000]
    hay_title = f"{title} {tags} {category}"
    hay_all = f"{hay_title} {desc}"
    score = 0
    matched = []
    for kw, weight in KEYWORDS.items():
        if kw in hay_title:
            score += weight * 3
            matched.append(kw)
        elif kw in hay_all:
            score += weight
            matched.append(kw)
    for kw, weight in TITLE_ONLY_KEYWORDS.items():
        if kw in hay_title:
            score += weight * 2
            matched.append(kw)
    return score, ", ".join(dict.fromkeys(matched))


def excluded(job: dict) -> bool:
    title = (job.get("title") or "").lower()
    return any(bad in title for bad in EXCLUDE_TITLES)


# --------------------------------------------------------------------------
# Salary
# --------------------------------------------------------------------------
def parse_salary(text: str) -> tuple[float | None, str, str]:
    text = (text or "").strip()
    if not text:
        return None, "unknown", ""
    currency = "usd"
    clean = text
    if "€" in text or "eur" in text.lower():
        currency = "eur"
    nums = re.findall(r"\d[\d,.]*", clean.replace(",", ""))
    vals = [float(n) for n in nums if n]
    if not vals:
        return None, "unknown", text
    annum = max(vals)
    low = text.lower()
    if "hour" in low or "/hr" in low or "/ hour" in low:
        annum *= 2080
    elif "month" in low or "/mo" in low or "/ month" in low:
        annum *= 12
    return annum, currency, text


def good_pay(annual: float | None, currency: str) -> bool:
    if annual is None:
        return True
    return annual >= 12_000


# --------------------------------------------------------------------------
# Database
# --------------------------------------------------------------------------
def init_db() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            company TEXT,
            location TEXT,
            salary_raw TEXT,
            salary_currency TEXT,
            salary_annual REAL,
            url TEXT,
            category TEXT,
            score INTEGER,
            matched TEXT,
            posted DATE,
            fetched_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
    return conn


def upsert_jobs(conn: sqlite3.Connection, jobs: list[dict]) -> int:
    new = 0
    for j in jobs:
        # safety net: fill company from title prefix when missing (any source)
        try:
            j["company_name"] = _extract_company(j.get("title") or "", j.get("company_name") or "")
        except Exception:
            pass
        salary_annual, cur_code, raw = parse_salary(j.get("salary"))
        posted = (j.get("publication_date") or "")[:10] or None
        src = j.get("_source", "remotive")
        raw_id = j.get("id")
        raw_id = str(raw_id) if raw_id is not None else (j.get("url") or "?").replace("https://", "")[:80]
        jid = f"{src}:{raw_id}"
        conn.execute("""
            INSERT OR IGNORE INTO jobs
            (id, source, title, company, location, salary_raw, salary_currency,
             salary_annual, url, category, score, matched, posted)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            jid, src, j.get("title"), j.get("company_name"),
            j.get("location") or j.get("candidate_required_location"), raw,
            cur_code, salary_annual, j.get("url"), j.get("category"),
            j.get("_score"), j.get("_matched"), posted,
        ))
        new += conn.execute("SELECT changes()").fetchone()[0]
    conn.commit()
    return new


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------
def build_report(conn: sqlite3.Connection, top: int, profile: dict = None) -> str:
    if profile is None:
        profile = load_profile()

    rows = conn.execute("""
        SELECT id, title, company, location, salary_raw, salary_currency,
               salary_annual, url, category, score, matched, posted
        FROM jobs WHERE score > 0 ORDER BY score DESC, salary_annual IS NULL,
                    salary_annual DESC LIMIT ?
    """, (top,)).fetchall()

    lines = [
        f"# Job Report — {date.today().isoformat()}",
        f"المُرشح: {profile['name']}",
        "",
        f"Top {len(rows)} of filtered jobs (score > 0)",
        "",
    ]

    # ─── جدول ملخص ────────────────────────────────────────────────
    lines.append("| # | Match | Score | Title | Company | Salary |")
    lines.append("|---|-------|-------|-------|---------|--------|")

    for i, (jid, t, c, loc, sraw, scur, sann, url, cat, score, matched, posted) in enumerate(rows, 1):
        # تحليل التطابق
        job = {"title": t, "description": matched or "", "tags": [cat] if cat else [],
               "salary_annual": sann}
        analysis = analyze_match(job, profile)
        match_str = f"{analysis['rating_color']} {analysis['match_percentage']}%"

        sal = sraw or (f"${sann:,.0f}/yr" if sann else "?")
        lines.append(f"| {i} | {match_str} | {score} | {t[:40]} | {(c or '?')[:25]} | {str(sal)[:20]} |")

    # ─── تفاصيل أفضل 10 ──────────────────────────────────────────
    lines += ["", "---", "", "## 🏆 أفضل 10 وظائف — تحليل تفصيلي", ""]

    for i, (jid, t, c, loc, sraw, scur, sann, url, cat, score, matched, posted) in enumerate(rows[:10], 1):
        job = {"title": t, "description": matched or "", "tags": [cat] if cat else [],
               "salary_annual": sann}
        analysis = analyze_match(job, profile)

        sal = sraw or (f"${sann:,.0f}/yr" if sann else "?")
        lines.append(f"### {i}. {t}")
        lines.append(f"**{c or '?'}** — {loc or 'Remote'} — {sal}")
        lines.append(f"**التطابق:** {analysis['rating_color']} {analysis['rating']} ({analysis['match_percentage']}%)")
        lines.append(f"**النتيجة:** {score} | **المنشور:** {posted or '?'}")
        if url:
            lines.append(f"**الرابط:** [{t}]({url})")
        lines.append("")

        if analysis["matched"]:
            lines.append("**✅ المهارات المطابقة:**")
            for m in analysis["matched"][:8]:
                lines.append(f"  - {m['skill']} (مستوى {m['level']}/10)")
        if analysis["missing"]:
            lines.append("**❌ المهارات الناقصة:**")
            for m in analysis["missing"][:5]:
                crit = "حرج" if m["critical"] else "عام"
                lines.append(f"  - {m['skill']} ({crit})")
        if analysis["recommendations"]:
            lines.append("**💡 التوصية:**")
            for r in analysis["recommendations"]:
                lines.append(f"  {r}")
        lines.append("")

    text = "\n".join(lines)
    REPORT_PATH.write_text(text, encoding="utf-8")
    return text


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description="Smart Job Aggregator v2")
    ap.add_argument("--pages", type=int, default=1, help="Remotive pages")
    ap.add_argument("--top", type=int, default=20, help="Top N in report")
    ap.add_argument("--smart", action="store_true", help="Use smart scoring + analysis")
    ap.add_argument("--profile", action="store_true", help="Show candidate profile")
    ap.add_argument("--analyze-all", action="store_true", help="Analyze all jobs in DB")
    args = ap.parse_args()

    if args.profile:
        p = load_profile()
        print(f"\n📋 الملف الشخصي: {p['name']}")
        print(f"   الخبرة: {p['experience_years']} سنة")
        print(f"   المهارات الأساسية: {len(p['core_skills'])} مهارة")
        print(f"   أنواع الوظائف: {len(p['target_roles'])} نوع")
        print(f"   الصناعات: {len(p['target_industries'])} صناعة")
        return 0

    conn = init_db()

    if args.analyze_all:
        profile = load_profile()
        rows = conn.execute("SELECT * FROM jobs").fetchall()
        print(f"\n🔍 تحليل {len(rows)} وظيفة...")
        results = []
        for row in rows:
            j = dict(row)
            skip, reason = should_exclude(j, profile)
            if skip:
                continue
            score, details = smart_score(j, profile)
            analysis = analyze_match(j, profile)
            if score > 10:
                results.append((score, analysis, j))
        results.sort(key=lambda x: -x[0])
        for score, analysis, j in results[:args.top]:
            print(f"\n  [{score:3d}] {j['title']}")
            print(f"       {j.get('company', '?')} | {j.get('location', '?')}")
            print(f"       {analysis['rating_color']} {analysis['rating']} ({analysis['match_percentage']}%)")
        conn.close()
        return 0

    # ─── جمع الوظائف ──────────────────────────────────────────────
    all_jobs = []

    for page in range(1, args.pages + 1):
        try:
            jobs = fetch_remotive(page)
            for j in jobs:
                j["_source"] = "remotive"
            all_jobs.extend(jobs)
            print(f"[i] Remotive page {page}: {len(jobs)} jobs")
            if len(jobs) < 50:
                break
        except Exception as e:
            print(f"[!] Remotive page {page} failed: {e}", file=sys.stderr)

    try:
        jobs = fetch_remoteok()
        for j in jobs:
            j["_source"] = "remoteok"
        all_jobs.extend(jobs)
        print(f"[i] RemoteOK: {len(jobs)} jobs")
    except Exception as e:
        print(f"[!] RemoteOK failed: {e}", file=sys.stderr)

    try:
        jobs = fetch_weworkremotely()
        for j in jobs:
            j["_source"] = "weworkremotely"
        all_jobs.extend(jobs)
        print(f"[i] WeWorkRemotely: {len(jobs)} jobs")
    except Exception as e:
        print(f"[!] WeWorkRemotely failed: {e}", file=sys.stderr)

    try:
        jobs = fetch_jobicy(count=200)
        for j in jobs:
            j["_source"] = "jobicy"
        all_jobs.extend(jobs)
        print(f"[i] Jobicy: {len(jobs)} jobs")
    except Exception as e:
        print(f"[!] Jobicy failed: {e}", file=sys.stderr)

    try:
        jobs = fetch_adzuna()
        for j in jobs:
            j["_source"] = "adzuna"
        all_jobs.extend(jobs)
        print(f"[i] Adzuna: {len(jobs)} jobs")
    except Exception as e:
        print(f"[!] Adzuna failed: {e}", file=sys.stderr)

    # ─── تقييم + فلترة ──────────────────────────────────────────────
    profile = load_profile()
    kept = []

    for j in all_jobs:
        # فلترة قديمة (للتوافق)
        if excluded(j):
            continue

        if args.smart:
            # فلترة ذكية جديدة
            skip, reason = should_exclude(j, profile)
            if skip:
                print(f"  [skip] {j.get('title', '?')[:40]} — {reason}")
                continue
            sc, details = smart_score(j, profile)
            j["_score"] = sc
            j["_matched"] = ", ".join(details["matched_skills"][:5])
        else:
            sc, matched = score_job(j)
            if sc <= 0:
                continue
            ann, cur, _ = parse_salary(j.get("salary"))
            if not good_pay(ann, cur):
                continue
            j["_score"] = sc
            j["_matched"] = matched

        kept.append(j)

    kept.sort(key=lambda j: -j["_score"])
    added = upsert_jobs(conn, kept)

    print(f"\n[i] Total fetched: {len(all_jobs)} | kept: {len(kept)} | new in DB: {added}")
    print(f"[i] DB: {DB_PATH}")

    if kept:
        print(build_report(conn, args.top, profile))
        print(f"[i] Report: {REPORT_PATH}")
    else:
        print("[!] No matching jobs this run.")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
