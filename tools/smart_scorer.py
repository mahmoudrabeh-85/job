#!/usr/bin/env python3
"""
smart_scorer.py — نظام تقييم ذكي للوظائف
يستخدم ملف CV + تفضيلات المستخدم لتقييم الوظائف بدقة

المهارات الفعلية (من CV):
- Procurement / Purchasing / Vendor Negotiation / Contract Management
- Supply Chain / Inventory / Logistics / Distribution
- Sales / Business Development / Account Management
- ERP: Oracle (Basic) / SAP (Basic) / Odoo
- Pharma / Pharmaceutical / Medical / Healthcare
- Operations / Management / Team Leadership
- MS Office / Excel Advanced

الاستبعاد التلقائي:
- وظائف برمجة (frontend/backend/devops/data science)
- وظائف تصميم (UI/UX/graphic)
- وظائف هندسة (engineering/architecture)
- وظائف غير مرتبطة بالخبرة
"""
import json
import re
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "data"
PROFILE_FILE = DATA_DIR / "candidate_profile.json"

# ─── الملف الشخصي للمُرشح ──────────────────────────────────────────────
DEFAULT_PROFILE = {
    "name": "[Your Name]",
    "core_skills": {
        "procurement": 10,
        "purchasing": 10,
        "vendor_negotiation": 10,
        "contract_management": 9,
        "supply_chain": 10,
        "inventory_management": 9,
        "logistics": 8,
        "distribution": 9,
        "sales": 9,
        "business_development": 8,
        "account_management": 8,
        "pharmaceutical": 10,
        "medical": 7,
        "healthcare": 7,
        "operations": 8,
        "management": 8,
        "team_leadership": 8,
        "strategic_planning": 7,
        "cost_reduction": 9,
        "negotiation": 9,
        "excel": 8,
        "ms_office": 7,
    },
    "experience_years": 15,
    "education": "commerce",
    "languages": {"arabic": "native", "english": "b2"},
    "location": "egypt",
    "work_type_preference": ["remote", "hybrid", "onsite"],
    "salary_min_annual": 12000,  # USD
    "salary_preferred_annual": 24000,  # USD
    "industries": ["pharmaceutical", "healthcare", "distribution", "trading", "fmcg", "retail"],
    "role_types": [
        "procurement manager",
        "purchasing manager",
        "supply chain manager",
        "sales manager",
        "operations manager",
        "business development manager",
        "account manager",
        "commercial manager",
        "vendor manager",
        "category manager",
    ],
}

# ─── المهارات المستبعدة (وظائف لا تناسب) ──────────────────────────────
EXCLUDE_SKILLS = {
    # برمجة
    "python", "javascript", "typescript", "react", "angular", "vue", "node.js",
    "java", "c++", "c#", "php", "ruby", "golang", "rust", "swift", "kotlin",
    "frontend", "backend", "full-stack", "fullstack", "devops", "mlops",
    "machine learning", "deep learning", "ai engineer", "data scientist",
    "data engineer", "data analyst", "cloud engineer", "site reliability",
    "database administrator", "system administrator", "network engineer",
    "cybersecurity", "information security",
    # تصميم
    "ui/ux", "ui designer", "ux designer", "graphic designer", "web designer",
    "product designer", "interaction designer", "visual designer",
    "figma", "sketch", "adobe xd", "photoshop", "illustrator",
    # هندسة
    "software engineer", "hardware engineer", "electrical engineer",
    "mechanical engineer", "civil engineer", "architect",
    # مهن أخرى غير مرتبطة
    "teacher", "professor", "nurse", "doctor", "lawyer", "accountant",
    "content writer", "copywriter", "social media manager", "translator",
}

# ─── كلمات المطابقة القوية (وزن عالي) ──────────────────────────────────
STRONG_MATCH = {
    "procurement": 10, "purchasing": 10, "buyer": 9, "sourcing": 9,
    "vendor": 8, "supplier": 8, "negotiation": 9, "contract": 8,
    "supply chain": 10, "logistics": 8, "inventory": 8, "warehouse": 7,
    "distribution": 9, "pharmaceutical": 10, "pharma": 10,
    "medical": 7, "healthcare": 7,
    "sales": 8, "business development": 8, "account manager": 8,
    "operations": 7, "management": 7, "cost reduction": 8, "strategic": 7,
    # ─── AI + Business Hybrid (مسار هجين: مجالك + AI) ─────────────────
    "ai product": 9, "ai sales": 8, "ai solutions": 8, "ai implementation": 7,
    "ai strategy": 8, "generative ai product": 9, "llm product": 8, "ml product": 7,
    "ai business development": 8, "ai account": 7, "ai procurement": 9, "ai supply chain": 9,
    "artificial intelligence product": 8, "artificial intelligence sales": 7,
}

# ─── كلمات العنوان فقط (تلوّث في الوصف) ──────────────────────────────────
TITLE_ONLY = {
    "sales": 7, "manager": 6, "director": 8, "head": 7, "lead": 6,
    "specialist": 5, "executive": 6, "consultant": 5, "advisor": 5,
    "coordinator": 4, "analyst": 4, "representative": 5,
}

# ─── استبعاد العنوان ──────────────────────────────────────────────────
EXCLUDE_TITLE = [
    "software engineer", "frontend developer", "backend developer",
    "full stack", "fullstack", "devops engineer", "data scientist",
    "data engineer", "data analyst", "machine learning", "ai engineer",
    "cloud engineer", "system administrator", "network engineer",
    "ui/ux designer", "graphic designer", "web designer", "product designer",
    "content writer", "copywriter", "social media manager",
    "teacher", "professor", "nurse", "doctor", "lawyer",
    "intern", "junior developer", "senior developer", "tech lead",
    "cto", "vp engineering", "architect",
    # تخصصات طبية ممارِسة (تحتاج ترخيص مزاولة — ليست صيدلة/توزيع)
    "surgeon", "physician", "rheumatologist", "cardiologist", "oncologist",
    "pediatrician", "psychiatrist", "dermatologist", "radiologist",
    "neurologist", "anaesthetist", "gastroenterolog", "physiotherapist",
    "general practitioner", "pharmacist", "dentist", "veterinarian",
    # تسويق رقمي / أفلييت / أداء (ليست في ملف المرشح المهني)
    "digital marketing", "performance marketing", "growth marketing",
    "affiliate", "affiliate marketing", "affiliate business development",
    "seo", "sem specialist", "social media", "influencer", "email marketing",
    "content marketing", "marketing manager", "marketing director",
    "b2b marketing", "brand manager", "product marketing",
]


def load_profile() -> dict:
    """Load candidate profile from file"""
    if PROFILE_FILE.exists():
        try:
            return json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return DEFAULT_PROFILE.copy()


def save_profile(profile: dict):
    """Save candidate profile"""
    DATA_DIR.mkdir(exist_ok=True)
    PROFILE_FILE.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")


def should_exclude(job: dict) -> tuple[bool, str]:
    """
    Check if job should be excluded entirely.
    Returns (excluded, reason)
    """
    title = (job.get("title") or "").lower()
    desc = (job.get("description") or "").lower()
    tags = " ".join(job.get("tags") or []).lower()
    
    # ─── استثناء: أدوار AI + Business الهجينة (لا تُستبعد حتى لو فيها ai engineer/ml) ───
    AI_BUSINESS_HYBRID = [
        "ai product", "ai sales", "ai solutions", "ai implementation", "ai strategy",
        "ai business development", "ai account", "ai procurement", "ai supply chain",
        "generative ai product", "llm product", "ml product",
        "artificial intelligence product", "artificial intelligence sales",
        "ai product manager", "ai sales engineer", "ai solutions engineer",
        "ai implementation consultant", "ai strategy consultant",
    ]
    is_ai_business = any(h in title for h in AI_BUSINESS_HYBRID)
    if is_ai_business:
        return False, ""
    
    # Check title exclusions
    for exclude in EXCLUDE_TITLE:
        if exclude in title:
            return True, f"Title contains '{exclude}'"
    
    # Check skill exclusions in tags/title
    for skill in EXCLUDE_SKILLS:
        if skill in tags or skill in title:
            # But allow if it's mentioned alongside our core skills
            our_skills = sum(1 for s in STRONG_MATCH if s in f"{title} {tags}")
            if our_skills < 2:  # If our skills aren't mentioned, exclude
                return True, f"Requires '{skill}'"
    
    # Check if it's a pure tech role (no business keywords)
    business_keywords = ["sales", "procurement", "supply", "vendor", "negotiation",
                         "business", "commercial", "operations", "management",
                         "pharmaceutical", "medical", "healthcare", "distribution",
                         "account", "strategy", "procurement", "purchasing"]
    has_business = any(kw in f"{title} {tags}" for kw in business_keywords)
    
    tech_keywords = ["developer", "engineer", "programmer", "coder", "architect",
                     "devops", "sre", "dba", "sysadmin"]
    is_tech_role = any(kw in title for kw in tech_keywords)
    
    if is_tech_role and not has_business:
        return True, "Pure tech role"
    
    return False, ""


def smart_score(job: dict, profile: dict = None) -> tuple[int, list[str]]:
    """
    Smart scoring based on candidate profile.
    Returns (score, list_of_reasons)
    """
    if profile is None:
        profile = load_profile()
    
    title = (job.get("title") or "").lower()
    desc = (job.get("description") or "").lower()[:5000]
    tags = " ".join(job.get("tags") or []).lower()
    category = (job.get("category") or "").lower()
    company = (job.get("company_name") or "").lower()
    
    hay_title = f"{title} {tags} {category}"
    hay_all = f"{hay_title} {desc}"
    
    score = 0
    reasons = []
    
    # ─── 1. Core Skills Match (0-40 points) ──────────────────────────
    skill_score = 0
    for skill, weight in profile.get("core_skills", {}).items():
        skill_clean = skill.replace("_", " ")
        if skill_clean in hay_title:
            skill_score += weight * 3
            reasons.append(f"Strong: {skill_clean}")
        elif skill_clean in hay_all:
            skill_score += weight
            reasons.append(f"Match: {skill_clean}")
    score += min(skill_score, 40)
    
    # ─── 2. Role Type Match (0-25 points) ────────────────────────────
    role_score = 0
    role_hits = 0
    # كلمات عامة لا تُعدّ مطابقة جزئية وحدها (manager/lead/head... كانت تمنح +50 وهمية)
    GENERIC_ROLE_WORDS = {"manager", "lead", "head", "senior", "junior", "executive", "director", "specialist", "coordinator", "assistant"}
    for role in profile.get("role_types", []):
        role_clean = role.lower().strip()
        if role_clean in title:
            role_score += 15
            role_hits += 1
            reasons.append(f"Exact role: {role}")
            continue
        # المطابقة الجزئية: كلمة مميزة فقط (وليست عامة) من اسم الدور موجودة في العنوان
        distinctive = [w for w in role_clean.split() if len(w) > 3 and w not in GENERIC_ROLE_WORDS]
        matched = [w for w in distinctive if w in hay_title]
        if matched:
            # كلمتان مميزتان = مطابقة قوية، كلمة واحدة = جزئية خفيفة
            gain = 8 if len(matched) >= 2 else 4
            role_score += gain
            role_hits += 1
            reasons.append(f"Partial role match: {role} ({', '.join(matched)})")
    score += min(role_score, 25)
    
    # ─── 3. Industry Match (0-15 points) ─────────────────────────────
    industry_score = 0
    for industry in profile.get("industries", []):
        if industry in hay_all:
            industry_score += 8
            reasons.append(f"Industry: {industry}")
    score += min(industry_score, 15)
    
    # ─── 4. Title-Only Keywords (0-10 points) ────────────────────────
    title_score = 0
    for kw, weight in TITLE_ONLY.items():
        if kw in hay_title:
            title_score += weight
    score += min(title_score, 10)
    
    # ─── 5. Salary Match (0-10 points) ───────────────────────────────
    salary_annual = job.get("salary_annual")
    if salary_annual:
        if salary_annual >= profile.get("salary_preferred_annual", 24000):
            score += 10
            reasons.append(f"High salary: ${salary_annual:,.0f}/yr")
        elif salary_annual >= profile.get("salary_min_annual", 12000):
            score += 5
            reasons.append(f"Good salary: ${salary_annual:,.0f}/yr")
        else:
            score -= 5
            reasons.append(f"Low salary: ${salary_annual:,.0f}/yr")
    
    # ─── 6. Location Match (0-5 points) ──────────────────────────────
    location = (job.get("location") or "").lower()
    if "remote" in location:
        score += 5
        reasons.append("Remote work")
    elif "egypt" in location or "cairo" in location:
        score += 3
        reasons.append("Local (Egypt)")
    elif "gulf" in location or "uae" in location or "saudi" in location:
        score += 4
        reasons.append("Gulf region")
    
    # ─── 7. Penalties ────────────────────────────────────────────────
    # Penalize pure tech keywords in title
    tech_penalties = ["python", "javascript", "react", "angular", "node.js",
                      "java", "c++", "php", "ruby", "golang", "rust"]
    for tech in tech_penalties:
        if tech in title:
            score -= 10
            reasons.append(f"Penalty: tech skill '{tech}' in title")
    
    # Penalize if description is too short (likely spam)
    if len(desc) < 100:
        score -= 3
        reasons.append("Penalty: short description")
    
    return max(score, 0), reasons


def get_profile_summary() -> str:
    """Get human-readable profile summary"""
    profile = load_profile()
    lines = [
        "📋 الملف الشخصي للمُرشح",
        "=" * 40,
        f"الاسم: {profile['name']}",
        f"الخبرة: {profile['experience_years']} سنة",
        f"الموقع: {profile['location']}",
        "",
        "🎯 المهارات الأساسية:",
    ]
    for skill, level in sorted(profile.get("core_skills", {}).items(), key=lambda x: -x[1]):
        bar = "█" * (level // 2) + "░" * (5 - level // 2)
        lines.append(f"  {skill.replace('_', ' '):25s} {bar} {level}/10")
    
    lines += [
        "",
        "🏢 الصناعات المستهدفة:",
        "  " + ", ".join(profile.get("industries", [])),
        "",
        "💼 أنواع الوظائف:",
        "  " + ", ".join(profile.get("role_types", [])),
        "",
        f"💰 الراتب: ≥ ${profile.get('salary_min_annual', 0):,}/سنة",
    ]
    return "\n".join(lines)


# ─── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    
    import argparse
    ap = argparse.ArgumentParser(description="Smart job scorer")
    sub = ap.add_subparsers(dest="cmd")
    
    sub.add_parser("profile", help="Show candidate profile")
    sub.add_parser("update", help="Update profile from CV")
    
    p_score = sub.add_parser("score", help="Score a job")
    p_score.add_argument("--title", required=True)
    p_score.add_argument("--desc", default="")
    p_score.add_argument("--tags", default="")
    
    p_filter = sub.add_parser("filter-db", help="Filter and score all jobs in DB")
    p_filter.add_argument("--top", type=int, default=30)
    
    args = ap.parse_args()
    
    if args.cmd == "profile":
        print(get_profile_summary())
    
    elif args.cmd == "score":
        job = {"title": args.title, "description": args.desc, "tags": args.tags.split(",")}
        excluded, reason = should_exclude(job)
        if excluded:
            print(f"❌ مستبعد: {reason}")
        else:
            score, reasons = smart_score(job)
            print(f"📊 النتيجة: {score}/100")
            for r in reasons[:10]:
                print(f"  • {r}")
    
    elif args.cmd == "filter-db":
        conn = sqlite3.connect(DATA_DIR / "jobs.db")
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM jobs").fetchall()
        profile = load_profile()
        
        results = []
        for row in rows:
            job = dict(row)
            excluded, reason = should_exclude(job)
            if excluded:
                continue
            score, reasons = smart_score(job, profile)
            if score > 10:
                results.append((score, reasons, job))
        
        results.sort(key=lambda x: -x[0])
        
        print(f"\n📊 أفضل {args.top} وظيفة من {len(rows)}:")
        print("-" * 70)
        for score, reasons, job in results[:args.top]:
            print(f"\n  [{score:3d}] {job['title']}")
            print(f"       {job.get('company', '?')} | {job.get('location', '?')}")
            if job.get('salary_raw'):
                print(f"       💰 {job['salary_raw']}")
            print(f"       🔗 {', '.join(reasons[:5])}")
        
        conn.close()
    
    else:
        print(get_profile_summary())
