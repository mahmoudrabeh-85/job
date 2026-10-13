"""
routers/cv_builder.py — ATS-compliant CV Builder (Pillar 4)
POST /api/v1/cv/build       → build ATS-safe CV HTML + plain text
POST /api/v1/cv/ats-check   → ATS-compatibility score (0-100) + recommendations

ATS-safe means: single column, standard section headings, no tables/columns/
images/icons, standard fonts, parseable dates, keywords repeated in context.
Nothing is persisted — the CV text lives only in the request/response.
"""
from __future__ import annotations

import html
import re

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/cv", tags=["cv-builder"])

# ─── Models ──────────────────────────────────────────────────────────────
class CVData(BaseModel):
    full_name: str = ""
    job_title: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    summary: str = ""
    skills: list[str] = Field(default_factory=list)          # e.g. ["Procurement", "SAP ERP"]
    experience: list[dict] = Field(default_factory=list)     # {role, company, start, end, bullets: []}
    education: list[dict] = Field(default_factory=list)      # {degree, school, year}
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class ATSCheckRequest(BaseModel):
    cv_text: str = Field(..., min_length=0, max_length=30000)


class BuildResponse(BaseModel):
    html: str
    plain_text: str
    ats: dict


# ─── ATS analyzer ────────────────────────────────────────────────────────
SECTION_HEADINGS = (
    "professional summary", "summary", "objective", "work experience",
    "professional experience", "experience", "employment history",
    "education", "skills", "certifications", "languages", "projects",
)

CONTACT_PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "phone": re.compile(r"(\+?\d[\d\s\-()]{7,}\d)"),
    "linkedin": re.compile(r"linkedin\.com/in/[\w-]+", re.I),
}


def ats_check_text(cv_text: str) -> dict:
    """Score raw CV text for ATS parseability (0-100) with recommendations."""
    text = cv_text or ""
    lower = text.lower()
    words = len(text.split())
    recommendations: list[str] = []
    score = 100

    # 1. Contact info
    contact_found = [k for k, p in CONTACT_PATTERNS.items() if p.search(text)]
    if "email" not in contact_found:
        score -= 15
        recommendations.append({"issue": "missing_email", "severity": "high",
                                "message": "أضف بريدًا إلكترونيًا واضحًا في أعلى الـ CV — أنظمة ATS تستخرج التواصل أولًا"})
    if "phone" not in contact_found:
        score -= 10
        recommendations.append({"issue": "missing_phone", "severity": "high",
                                "message": "أضف رقم هاتف بصيغة قياسية (+20 ...)"})
    if "linkedin" not in contact_found:
        score -= 3
        recommendations.append({"issue": "missing_linkedin", "severity": "low",
                                "message": "أضف رابط LinkedIn (اختياري لكنه يرفع ثقة المسؤول)"})

    # 2. Standard section headings
    found_sections = [h for h in SECTION_HEADINGS if h in lower]
    if "experience" not in " ".join(found_sections):
        score -= 12
        recommendations.append({"issue": "missing_experience_section", "severity": "high",
                                "message": "أضف قسمًا بعنوان قياسي مثل Work Experience — العناوين غير القياسية لا تُقرأ"})
    if not any(h in ("education",) for h in found_sections):
        score -= 8
        recommendations.append({"issue": "missing_education_section", "severity": "medium",
                                "message": "أضف قسم Education بعنوان قياسي"})
    if not any(h in ("skills",) for h in found_sections):
        score -= 8
        recommendations.append({"issue": "missing_skills_section", "severity": "medium",
                                "message": "أضف قسم Skills — ATS يطابق الكلمات المفتاحية من هنا غالبًا"})

    # 3. Length sanity
    if words < 120:
        score -= 12
        recommendations.append({"issue": "too_short", "severity": "high",
                                "message": f"الـ CV قصير جدًا ({words} كلمة) — استهدف 350-800 كلمة"})
    elif words > 1200:
        score -= 5
        recommendations.append({"issue": "too_long", "severity": "low",
                                "message": f"الـ CV طويل ({words} كلمة) — اختصر إلى صفحتين كحد أقصى"})

    # 4. Dates present (parseable employment history)
    date_hits = len(re.findall(r"\b(19|20)\d{2}\b", text))
    if date_hits < 2:
        score -= 10
        recommendations.append({"issue": "missing_dates", "severity": "high",
                                "message": "أضف تواريخ (YYYY) لكل وظيفة — ATS يحسب سنوات الخبرة منها"})

    # 5. ATS-hostile characters / layouts that survive text extraction
    if re.search(r"[\t]{2,}", text) or text.count("|") > 15:
        score -= 4
        recommendations.append({"issue": "heavy_tables", "severity": "low",
                                "message": "قلّل الجداول/الأعمدة والفواصل العمودية — استخدم قوائم نقطية بسيطة"})
    if re.search(r"[•◦▪●]", text):
        pass  # bullets are fine
    else:
        score -= 4
        recommendations.append({"issue": "no_bullets", "severity": "low",
                                "message": "استخدم نقاطًا (•) لوصف الإنجازات بدل الفقرات الطويلة"})

    # 6. Quantified achievements
    quantified = len(re.findall(r"\d+\s?%|\d+\s?(?:million|m\+|k\+)|\d{2,}\s?(?:egp|usd|sar|aed)", lower))
    if quantified == 0:
        score -= 6
        recommendations.append({"issue": "not_quantified", "severity": "medium",
                                "message": "أضف أرقامًا للإنجازات (15% توفير، 5M مخزون...) — ترفع ترتيبك في ATS والفلترة البشرية"})

    score = max(0, min(100, score))
    grade = ("excellent" if score >= 85 else "good" if score >= 70
             else "fair" if score >= 50 else "poor")
    return {
        "score": score,
        "grade": grade,
        "sections": found_sections,
        "contact_found": contact_found,
        "word_count": words,
        "quantified_achievements": quantified,
        "recommendations": recommendations,
    }


# ─── Builders ────────────────────────────────────────────────────────────
def _esc(s: str) -> str:
    return html.escape(str(s or ""), quote=False)


def _build_plain(cv: CVData) -> str:
    lines: list[str] = []
    head = cv.full_name
    if cv.job_title:
        head += f" — {cv.job_title}"
    lines.append(head)
    contact = [x for x in (cv.email, cv.phone, cv.location, cv.linkedin) if x]
    if contact:
        lines.append(" | ".join(contact))
    if cv.summary:
        lines += ["", "PROFESSIONAL SUMMARY", cv.summary]
    if cv.skills:
        lines += ["", "SKILLS", " • ".join(cv.skills)]
    if cv.experience:
        lines += ["", "WORK EXPERIENCE"]
        for e in cv.experience:
            dates = f"{e.get('start', '')} - {e.get('end', '')}".strip(" -")
            lines.append(f"{e.get('role', '')} — {e.get('company', '')}"
                         + (f" ({dates})" if dates else ""))
            for b in e.get("bullets", []):
                if b:
                    lines.append(f"• {b}")
    if cv.education:
        lines += ["", "EDUCATION"]
        for d in cv.education:
            lines.append(f"{d.get('degree', '')} — {d.get('school', '')}"
                         + (f" ({d['year']})" if d.get("year") else ""))
    if cv.certifications:
        lines += ["", "CERTIFICATIONS"] + [f"• {c}" for c in cv.certifications]
    if cv.languages:
        lines += ["", "LANGUAGES", " • ".join(cv.languages)]
    return "\n".join(lines).strip()


def _build_html(cv: CVData, plain: str) -> str:
    """Single-column, print-ready, ATS-safe HTML (no tables/images/columns)."""
    ats = ats_check_text(plain)

    contact_bits = [x for x in (cv.email, cv.phone, cv.location, cv.linkedin) if x]

    def section(title: str, body: str) -> str:
        return f"<h2>{_esc(title)}</h2>\n{body}\n" if body else ""

    summary = section("Professional Summary", f"<p>{_esc(cv.summary)}</p>") if cv.summary else ""

    skills = ""
    if cv.skills:
        skills = section("Skills", "<ul>" + "".join(f"<li>{_esc(s)}</li>" for s in cv.skills) + "</ul>")

    exp = ""
    if cv.experience:
        items = []
        for e in cv.experience:
            dates = f"{e.get('start', '')} - {e.get('end', '')}".strip(" -")
            date_s = f' <span class="dates">({_esc(dates)})</span>' if dates else ""
            bullets = "".join(f"<li>{_esc(b)}</li>" for b in e.get("bullets", []) if b)
            items.append(
                f'<div class="job"><h3>{_esc(e.get("role", ""))}</h3>'
                f'<p class="meta">{_esc(e.get("company", ""))}{date_s}</p>'
                + (f"<ul>{bullets}</ul>" if bullets else "")
                + "</div>"
            )
        exp = section("Work Experience", "\n".join(items))

    edu = ""
    if cv.education:
        items = "".join(
            f'<p><strong>{_esc(d.get("degree", ""))}</strong> — {_esc(d.get("school", ""))}'
            + (f' <span class="dates">({_esc(d["year"])})</span>' if d.get("year") else "")
            + "</p>"
            for d in cv.education
        )
        edu = section("Education", items)

    certs = ""
    if cv.certifications:
        certs = section("Certifications", "<ul>" + "".join(f"<li>{_esc(c)}</li>" for c in cv.certifications) + "</ul>")

    langs = ""
    if cv.languages:
        langs = section("Languages", "<ul>" + "".join(f"<li>{_esc(l)}</li>" for l in cv.languages) + "</ul>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{_esc(cv.full_name)} — CV</title>
<style>
  /* ATS-safe: single column, standard fonts, no tables/images */
  body {{ font-family: Arial, Helvetica, sans-serif; max-width: 800px;
         margin: 0 auto; padding: 32px 24px; color: #111; line-height: 1.45; }}
  h1 {{ font-size: 22pt; margin: 0 0 4px; }}
  h2 {{ font-size: 13pt; border-bottom: 1px solid #333; padding-bottom: 2px;
       margin: 20px 0 8px; text-transform: uppercase; }}
  h3 {{ font-size: 11.5pt; margin: 12px 0 2px; }}
  p, li {{ font-size: 10.5pt; }}
  ul {{ margin: 4px 0 8px 22px; padding: 0; }}
  .contact {{ font-size: 10pt; color: #333; margin-bottom: 6px; }}
  .title {{ font-size: 13pt; color: #333; margin: 0 0 6px; }}
  .meta {{ margin: 0; color: #444; }}
  .dates {{ color: #555; font-size: 9.5pt; }}
  .job {{ margin-bottom: 10px; }}
  @media print {{ body {{ padding: 0; }} h2 {{ page-break-after: avoid; }} .job {{ page-break-inside: avoid; }} }}
</style>
</head>
<body>
<h1>{_esc(cv.full_name)}</h1>
{f'<p class="title">{_esc(cv.job_title)}</p>' if cv.job_title else ""}
{f'<p class="contact">{" | ".join(_esc(x) for x in contact_bits)}</p>' if contact_bits else ""}
{summary}{skills}{exp}{edu}{certs}{langs}
</body>
</html>"""


# ─── Endpoints ───────────────────────────────────────────────────────────
@router.post("/build", response_model=BuildResponse)
def build_cv(cv: CVData):
    """Build ATS-safe CV (print-to-PDF-ready HTML + plain text) with live ATS score."""
    plain = _build_plain(cv)
    ats = ats_check_text(plain)
    page = _build_html(cv, plain)
    return {"html": page, "plain_text": plain, "ats": ats}


@router.post("/ats-check")
def ats_check(req: ATSCheckRequest):
    """Score raw CV text for ATS parseability. Nothing is stored."""
    return ats_check_text(req.cv_text)
