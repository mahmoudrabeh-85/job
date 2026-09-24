"""
routers/analysis.py — CV Analysis + HR Templates API
POST /api/v1/analyze      → analyze job vs CV
POST /api/v1/hr-template  → generate HR letter
GET  /api/v1/swot         → SWOT analysis data
GET  /api/v1/skills       → available skills map
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from app.config import settings

router = APIRouter(prefix="/api/v1", tags=["analysis"])


# ─── CV Skills Engine (from existing job_app.py) ────────────────────────
CV_SKILLS = {
    "procurement": {"keywords": ["procurement", "purchasing", "sourcing", "buyer", "buying", "vendor management", "negotiation", "contract management", "rfq", "rfp", "tender", "vendor"], "weight": 10, "cv_has": True},
    "supply_chain": {"keywords": ["supply chain", "logistics", "inventory", "warehouse", "distribution", "stock", "supplier"], "weight": 10, "cv_has": True},
    "sales": {"keywords": ["sales", "business development", "account executive", "account manager", "revenue", "client", "customer"], "weight": 8, "cv_has": True},
    "erp": {"keywords": ["erp", "oracle", "sap", "odoo", "netsuite", "dynamics", "salesforce"], "weight": 7, "cv_has": False},
    "pharma": {"keywords": ["pharmaceutical", "pharma", "drug", "medicine", "healthcare", "medical", "clinical", "fda", "gdp"], "weight": 9, "cv_has": True},
    "management": {"keywords": ["manager", "leadership", "team lead", "supervision", "management", "director"], "weight": 6, "cv_has": True},
    "excel": {"keywords": ["excel", "spreadsheet", "data analysis", "reporting", "dashboard"], "weight": 5, "cv_has": True},
    "operations": {"keywords": ["operations", "process improvement", "quality", "compliance", "audit"], "weight": 5, "cv_has": True},
    "python": {"keywords": ["python", "programming", "coding"], "weight": 3, "cv_has": False},
    "sql": {"keywords": ["sql", "database", "mysql", "postgresql"], "weight": 3, "cv_has": False},
    "power_bi": {"keywords": ["power bi", "tableau", "data visualization", "bi tool"], "weight": 3, "cv_has": False},
    "digital_marketing": {"keywords": ["digital marketing", "seo", "sem", "social media marketing", "content marketing"], "weight": 4, "cv_has": False},
    "pmp": {"keywords": ["pmp", "project management professional", "project manager"], "weight": 4, "cv_has": False},
    "six_sigma": {"keywords": ["six sigma", "lean", "continuous improvement"], "weight": 3, "cv_has": False},
    "crm": {"keywords": ["crm", "salesforce", "hubspot", "customer relationship"], "weight": 3, "cv_has": False},
    "agile": {"keywords": ["agile", "scrum", "kanban"], "weight": 2, "cv_has": False},
    "data_analysis": {"keywords": ["data analysis", "analytics", "business intelligence"], "weight": 4, "cv_has": False},
    "ai_ml": {"keywords": ["artificial intelligence", "machine learning", "ai", "ml", "deep learning"], "weight": 2, "cv_has": False},
}

GAP_ADVICE = {
    "python": {"course": "Python for Data Analysis", "platform": "Coursera / edX", "duration": "1-2 months", "cost": "Free-$50", "priority": "medium"},
    "sql": {"course": "SQL for Business Analysis", "platform": "Codecademy / Coursera", "duration": "1-2 months", "cost": "Free-$50", "priority": "medium"},
    "power_bi": {"course": "Power BI Certification", "platform": "Microsoft Learn / Udemy", "duration": "1-2 months", "cost": "Free-$100", "priority": "medium"},
    "digital_marketing": {"course": "Digital Marketing Certification", "platform": "Google / HubSpot", "duration": "1-2 months", "cost": "Free", "priority": "low"},
    "pmp": {"course": "PMP Certification", "platform": "PMI / Coursera", "duration": "3-6 months", "cost": "$400-600", "priority": "high"},
    "six_sigma": {"course": "Six Sigma Green Belt", "platform": "ASQ / Udemy", "duration": "2-3 months", "cost": "$200-400", "priority": "medium"},
    "crm": {"course": "CRM Administration (Salesforce/HubSpot)", "platform": "Trailhead / HubSpot Academy", "duration": "1-2 months", "cost": "Free", "priority": "low"},
    "agile": {"course": "Agile/Scrum Certification", "platform": "Scrum.org / Udemy", "duration": "1-2 months", "cost": "$100-200", "priority": "low"},
    "data_analysis": {"course": "Data Analysis with Excel/Python", "platform": "Coursera / Google", "duration": "2-3 months", "cost": "Free-$100", "priority": "medium"},
    "ai_ml": {"course": "AI for Business", "platform": "Coursera / Google AI", "duration": "2-3 months", "cost": "Free-$100", "priority": "low"},
}


# ─── CV Loader ───────────────────────────────────────────────────────────
_cv_cache: str | None = None


def load_cv_text() -> str:
    """Load and cache CV text content."""
    global _cv_cache
    if _cv_cache is not None:
        return _cv_cache

    cv_dir = settings.cv_full_path
    text = ""
    for pattern in ["*_EN.txt", "*_AR*.txt"]:
        for f in cv_dir.glob(pattern):
            text += f.read_text(encoding="utf-8", errors="replace") + "\n"

    _cv_cache = text.lower()
    return _cv_cache


def analyze_job(cv_text: str, title: str, description: str) -> dict:
    """Analyze a job posting against the CV. Returns score + matched/missing skills."""
    combined = (title + " " + description).lower()
    matched = []
    missing = []
    score = 0
    max_score = 0

    for cat, info in CV_SKILLS.items():
        cat_matched = [k for k in info["keywords"] if k in combined]
        if cat_matched:
            max_score += info["weight"]
            if info["cv_has"]:
                matched.append({"category": cat, "skills": cat_matched[:3], "level": "strong"})
                score += info["weight"]
            else:
                missing.append({
                    "category": cat,
                    "skills": cat_matched[:3],
                    "severity": "high" if info["weight"] >= 7 else "medium",
                })
                score += info["weight"] * 0.3

    # Experience bonus
    if any(w in combined for w in ["10+ years", "10 years", "15+", "senior", "lead", "director"]):
        score += 5
        max_score += 5
    elif any(w in combined for w in ["5+ years", "5 years", "3+ years"]):
        score += 3
        max_score += 3

    pct = min(int((score / max(max_score, 1)) * 100), 100) if max_score > 0 else 0

    return {
        "score": pct,
        "matched": matched,
        "missing": missing,
        "matched_count": len(matched),
        "missing_count": len(missing),
    }


# ─── Pydantic Models ────────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    title: str
    description: str = ""
    company: str = ""


class HrTemplateRequest(BaseModel):
    title: str
    company: str = ""
    lang: str = "en"


# ─── Endpoints ───────────────────────────────────────────────────────────
@router.post("/analyze")
def analyze_endpoint(req: AnalyzeRequest):
    """Analyze a job posting against the CV."""
    cv_text = load_cv_text()
    analysis = analyze_job(cv_text, req.title, req.description)

    gaps_with_advice = []
    for g in analysis["missing"]:
        advice = GAP_ADVICE.get(g["category"], {
            "course": f"Course in {g['category']}",
            "platform": "Coursera/Udemy",
            "duration": "1-2 months",
            "cost": "Free-$100",
            "priority": "medium",
        })
        gaps_with_advice.append({**g, **advice})

    hr_en = _generate_hr_template(req.title, req.company, "en")
    hr_ar = _generate_hr_template(req.title, req.company, "ar")

    return {
        "analysis": analysis,
        "hr_en": hr_en,
        "hr_ar": hr_ar,
        "gaps": gaps_with_advice,
    }


@router.post("/hr-template")
def hr_template_endpoint(req: HrTemplateRequest):
    """Generate HR cover letter template."""
    template = _generate_hr_template(req.title, req.company, req.lang)
    return {"template": template, "lang": req.lang}


@router.get("/swot")
def get_swot():
    """Live SWOT matrix + TOWS strategies from real DB stats."""
    from tools import job_swot
    stats = job_swot.load_market_stats()
    s, w, o, t = job_swot.build_swot(stats)
    strategies = job_swot.build_tows(s, w, o, t)
    return {
        "strengths": s, "weaknesses": w,
        "opportunities": o, "threats": t,
        "strategies": strategies,
        "stats": {
            "total": stats["total"], "avg_score": stats["avg_score"],
            "cats": stats["cats"], "sources": stats["sources"],
        },
    }


@router.get("/skills")
def get_skills():
    """Return the skills mapping used for analysis."""
    return {
        "cv_skills": {
            cat: {
                "keywords": info["keywords"],
                "weight": info["weight"],
                "cv_has": info["cv_has"],
            }
            for cat, info in CV_SKILLS.items()
        },
        "total_categories": len(CV_SKILLS),
        "cv_owned": sum(1 for v in CV_SKILLS.values() if v["cv_has"]),
        "cv_missing": sum(1 for v in CV_SKILLS.values() if not v["cv_has"]),
    }


# ─── HR Template Generator ──────────────────────────────────────────────
def _generate_hr_template(title: str, company: str, lang: str = "en") -> str:
    if lang == "en":
        return f"""Subject: Application for {title} — [Your Name]

Dear Hiring Manager,

I am writing to express my strong interest in the {title} position at {company}. With over 15 years of experience in pharmaceutical procurement and supply chain management, I bring a proven track record of achieving 15% cost savings through strategic vendor negotiation.

Key qualifications:
• 10+ years managing procurement across Egypt and the Gulf
• Expertise in vendor negotiation, contract management, cost reduction
• Dual background in Sales & Procurement
• ERP proficiency (Oracle, SAP, Odoo)
• <2% stock-out rate across 5M+ EGP inventory

I would welcome the opportunity to discuss how my experience aligns with your needs.

Best regards,
[Your Name] |  | [Email]"""
    else:
        return f"""الموضوع: طلب توظيف — [اسمك]

عزيزي مدير التوظيف،

أكتب للتعبير عن اهتمامي بوظيفة {title} في {company}. مع أكثر من 15 عاماً من الخبرة في إدارة المشتريات وسلسلة التوريد، أحضر سجلاً حافلاً بالإنجازات.

مؤهلاتي الرئيسية:
• أكثر من 10 سنوات في إدارة المشتريات في مصر والخليج
• خبرة في التفاوض مع الموردين وإدارة العقود
• خلفية مزدوجة في المبيعات والمشتريات
• إتقان أنظمة ERP (Oracle, SAP, Odoo)
• أقل من 2% معدل نفاد مخزون

أتطلع إلى فرصة مناقشة مدى تطابق خبرتي مع احتياجاتكم.

[اسمك] |  | [Email]"""
