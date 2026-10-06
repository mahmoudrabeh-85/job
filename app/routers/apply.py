"""
routers/apply.py — Application Center API (sanitized public port)
POST /api/v1/apply-top50     → top remote-USD + Gulf opportunities, ranked
GET  /api/v1/daily-queue     → today's easiest-to-apply shortlist
GET  /api/v1/followups       → follow-up reminders from the applications table
POST /api/v1/hr-simulate     → HR/ATS screening simulation (generic guidance)
POST /api/v1/hr-simulate-top → simulate screening for top-N matches
POST /api/v1/cover-letter    → template cover letter ([Your Name] placeholders)
POST /api/v1/cv-pdf          → 🧪 experimental (501 until Arabic-font PDF lands)

Sanitization rules (public repo — no personal data):
- Candidate skills come from the REQUEST (skills text), never from a stored CV.
- All answers/messages are generic guidance or [Your Name]/[Phone]/[Email]
  placeholders — no invented years, savings, locations, or contacts.
- Public DB has no job descriptions: matching uses indexed
  title/company/location/category fields only.
"""
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.database_factory import fetch_all, db_exists
from app.routers.analysis import analyze_job, CV_SKILLS, _generate_hr_template
from app.routers.jobs import _format_job
from app.routers.jobs import list_applications as _list_applications

router = APIRouter(prefix="/api/v1", tags=["apply"])

DAILY_QUEUE_SIZE = 10
FOLLOWUP_DAYS = 6  # reminder window 5-7 days — 6 is the nudge threshold

# Approximate FX → USD (public estimates, update periodically — ranking only).
APPLY_FX = {
    "PHP": 0.0178, "HUF": 0.0028, "CZK": 0.043, "PLN": 0.25, "INR": 0.012,
    "BRL": 0.185, "MXN": 0.055, "SGD": 0.75, "CAD": 0.73, "AUD": 0.66,
    "GBP": 1.27, "EUR": 1.08, "CHF": 1.10, "SEK": 0.095, "NOK": 0.093,
    "DKK": 0.145, "ZAR": 0.055, "ILS": 0.27, "JPY": 0.0067, "TRY": 0.03,
    "SAR": 0.267, "AED": 0.272, "QAR": 0.275, "KWD": 3.26, "BHD": 2.65,
    "OMR": 2.60, "EGP": 0.0208, "RON": 0.215,
}
APPLY_GULF_LOC = re.compile(
    r"(saudi|riyadh|jeddah|dammam|khobar|united arab|dubai|abu dhabi|sharjah|"
    r"uae|qatar|doha|kuwait|bahrain|manama|oman|muscat)", re.I)
APPLY_GULF_TITLE = re.compile(
    r"(procurement|purchasing|supply chain|logistics|sourcing|buyer|vendor|"
    r"warehouse|inventory|distribution|sales|pharma)", re.I)
HR_REMOTE_BOARDS = ("remoteok", "remotive", "jobicy", "weworkremotely", "hn",
                    "linkedin:remote")

# Generic interview-question bank per skill (guidance only — no personal claims).
HR_SKILL_QUESTIONS = {
    "procurement": "اشرح دورة الشراء P2P — وكيف تتصرف مع مورد متعثر في التوريد؟",
    "supply_chain": "كيف تحدد مستوى المخزون الآمن؟ اذكر تجربتك في خفض stock-out.",
    "sales": "كيف تبدأ خطة مبيعات لمنطقة أو قطاع جديد؟ اذكر أرقام تحقيق أهدافك.",
    "erp": "أي أنظمة ERP استخدمت عملياً؟ اشرح مهمة واحدة أنجزتها عليه.",
    "pharma": "ما خبرتك مع GDP ومتطلبات امتثال توزيع الأدوية؟",
    "management": "كم فريقاً أدرت وما أكبر تحدٍّ إداري واجهتك؟",
    "excel": "ما أكثر تقرير بنيته في Excel؟ ما المعادلات المتقدمة التي تستخدمها؟",
    "power_bi": "صِف داشبورد مؤشرات بنيته — ما مصادر البيانات والقياسات؟",
    "sql": "اكتب استعلاماً يجيب: أعلى 5 موردين بحسب قيمة المشتريات هذا العام؟",
    "python": "ما مهمة متكررة أتممتها بسكريبت؟ اشرح الخطوات.",
    "operations": "كيف تحسّن عملية تشغيلية مستمرة؟ اذكر مثالاً بالأرقام.",
    "finance": "كيف تقرأ ميزانية مشتريات سنوية وتدافع عنها أمام الإدارة المالية؟",
}
HR_MISSING_FIX = {
    "erp": "أضف للمهارات ما تستخدمه فعلًا + الأساسيات الجاري تعلمها — ولا تدّعِ خبرة لا تملكها؛ المقابلة تكشف ما لا يكشفه ATS.",
    "python": "إن كان دوراً تقنياً: اذكر الأتمتة العملية التي بنيتها بأدوات AI بدل ادعاء خبرة برمجية كاملة.",
    "sql": "أضف 'SQL basics — قيد التعلم' إن كان مطلوباً، وجهّز إجابة صادقة عن مستواك.",
    "power_bi": "ابنِ داشبورد مؤشرات واحدًا حقيقيًا قبل التقديم وأشر إليه في سيرتك.",
    "english": "اكتب مستواك الحقيقي وجهّز إجابات المقابلة بالإنجليزية — نقطة الفرز الأشيع.",
}


class SkillsIn(BaseModel):
    skills: str = ""
    years: Optional[int] = None
    field: str = ""
    top_per_side: int = 25


class SimulateIn(BaseModel):
    job_id: str
    skills: str = ""
    years: Optional[int] = None


class SimulateTopIn(BaseModel):
    skills: str = ""
    years: Optional[int] = None
    top: int = 50


class CoverIn(BaseModel):
    title: str = ""
    company: str = ""
    lang: str = "en"
    skills: str = ""


def _usd(job: dict) -> float:
    sal = job.get("salary_annual") or 0
    raw = (job.get("salary_raw") or "").upper()
    m = re.search(r"\b(" + "|".join(APPLY_FX) + r")\b", raw)
    if m:
        try:
            return float(sal) * APPLY_FX[m.group(1)]
        except (TypeError, ValueError):
            return 0
    try:
        if float(sal) > 400000:
            return 0
        return float(sal)
    except (TypeError, ValueError):
        return 0


def _apply_ease_bonus(job: dict) -> int:
    """Easiest to apply first: direct email (0) ← free company link (1) ← LinkedIn login (2)."""
    url = (job.get("url") or "").lower()
    src = (job.get("source") or "").lower()
    if url.startswith("mailto:") or "mail" in src:
        return 0
    if "linkedin.com" in url or "linkedin" in src:
        return 2
    return 1


def _depth(cv_text: str, job: dict, analysis: dict) -> float:
    matched_w = sum(CV_SKILLS.get(m.get("category", ""), {}).get("weight", 0)
                    for m in analysis.get("matched", []))
    missing_w = sum(CV_SKILLS.get(m.get("category", ""), {}).get("weight", 0)
                    for m in analysis.get("missing", []))
    return round(matched_w + 0.3 * missing_w, 1)


def _analyze_for(skills: str, job: dict) -> dict:
    return analyze_job(skills or "",
                       job.get("title", "") or "",
                       (job.get("matched") or "") + " " + (job.get("category") or ""))


def _base_card(job: dict, analysis: dict, depth: float) -> dict:
    card = _format_job(job, analysis)
    card.update({
        "score": analysis.get("score", 0),
        "depth": depth,
        "job_id": job.get("id"),
        "salary_raw": job.get("salary_raw") or "",
    })
    return card


def _simulate(job: dict, skills: str) -> dict:
    """HR/ATS screening simulation with GENERIC guidance (no personal claims)."""
    title = job.get("title") or ""
    analysis = _analyze_for(skills, job)
    score = analysis.get("score", 0)
    loc = (job.get("location") or "").lower()
    src = (job.get("source") or "")
    sal = job.get("salary_annual") or 0

    if score >= 75:
        verdict = "✅ ينجح الفرز الآلي غالباً — قدّم اليوم"
    elif score >= 55:
        verdict = "❗ حدّي — خصّص السيرة لهذا الإعلان قبل التقديم"
    else:
        verdict = "⛔ ضعيف التوافق — خصّص بقوة أو تجاوز"

    questions = [
        {"q": "حدثني عن خبرتك في دقيقة.", "risk": "",
         "answer": "جهّز قصة 60 ثانية: دورك الحالي + 3 أرقام حقيقية من إنجازاتك + لماذا هذه الشركة تحديدًا."},
        {"q": "ما توقعاتك للراتب؟",
         "risk": "" if sal else "متوسط — الراتب غير معلن",
         "answer": (f"الإعلان يقدَّر بنحو {sal / 12:,.0f}$/شهر — ابقَ داخل نطاق الإعلان واطلب أعلى حد تملك مبررًا له"
                    if sal else "غير معلن — ابحث عن نطاقات مماثلة واذكر نطاقًا لا رقمًا واحدًا")},
    ]
    gulf = ("saudi", "riyadh", "dubai", "abu dhabi", "united arab", "qatar",
            "doha", "kuwait", "sharjah", "jeddah")
    if any(g in loc for g in gulf):
        questions.append({
            "q": "هل أنت مقيم في بلد الوظيفة؟", "risk": "عالٍ — فلاتر ATS الخليجية تفرز غير المقيمين كثيرًا",
            "answer": "جهّز إجابة انتقال واضحة: مدينتك الحالية + مدة الجاهزية للانتقال + توقعات الإقامة وفق عقد البلد المعتاد."})
    elif "remote" in loc or src in HR_REMOTE_BOARDS:
        questions.append({
            "q": "هل تعمل عن بُعد بتوقيت الشركة؟", "risk": "",
            "answer": "وضّح منطقتك الزمنية وتوافقها مع فريق الشركة وساعات التداخل المتاحة لديك."})
    questions.append({
        "q": "ما مستواك في الإنجليزية؟", "risk": "",
        "answer": "اذكر مستواك الحقيقي بصدق + مثال عملي (تفاوض/مراسلات/تقارير بالإنجليزية)."})
    for m in analysis.get("matched", [])[:3]:
        q = HR_SKILL_QUESTIONS.get(m.get("category", ""))
        if q:
            questions.append({"q": q, "risk": "",
                              "answer": "مهارة مطابقة لخبرتك — جهّز قصة رقمية حقيقية من عملك."})
    for miss in analysis.get("missing", [])[:2]:
        q = HR_SKILL_QUESTIONS.get(miss.get("category", ""))
        if q:
            questions.append({"q": q, "risk": "عالٍ — سؤال كاشف شائع لهذه الفجوة",
                              "answer": "غير مغطاة في خبرتك — تعلّم أساسياتها سريعًا أو صِغ خبرتك القريبة منها بصدق."})

    feedback = [HR_MISSING_FIX[m.get("category", "")]
                for m in analysis.get("missing", [])
                if m.get("category", "") in HR_MISSING_FIX]
    if score < 75:
        feedback.append("انسخ كلمات الإعلان الحرفية في ملخص الخبرة والمهارات — ATS يفرز بالكلمات المطابقة حرفيًا.")
    if sal:
        feedback.append("قارن الراتب بالحد الأدنى المقبول لديك قبل التقديم — لا تقدّم لوظيفة تحت حدّك إلا كمدخل لسوق أفضل.")

    return {
        "job_id": job.get("id"), "title": title, "company": job.get("company") or "",
        "url": job.get("url") or "#", "location": job.get("location") or "",
        "salary": job.get("salary_raw") or "",
        "score": score, "verdict": verdict,
        "matched": analysis.get("matched", []), "missing": analysis.get("missing", []),
        "questions": questions, "feedback": feedback[:6],
    }


def _top50(skills: str, top_per_side: int = 25) -> dict:
    """Top remote-by-USD + Gulf opportunities ranked by skill depth then score."""
    remote, gulf = [], []
    for j in fetch_all("SELECT * FROM jobs ORDER BY id DESC"):
        loc = j.get("location") or ""
        title = j.get("title") or ""
        a = _analyze_for(skills, j)
        card = _base_card(j, a, _depth(skills, j, a))
        if APPLY_GULF_LOC.search(loc) and APPLY_GULF_TITLE.search(title):
            gulf.append({**card, "salary": ""})
            continue
        card["usd_monthly"] = round(_usd(j) / 12, 0) if _usd(j) else 0
        remote.append(card)
    remote.sort(key=lambda x: (-x.get("depth", 0), -x.get("score", 0)))
    gulf.sort(key=lambda x: (-x.get("depth", 0), -x.get("score", 0)))
    return {"remote": remote[:top_per_side], "gulf": gulf[:top_per_side]}


@router.post("/apply-top50")
def apply_top50(req: SkillsIn):
    """Ranked apply list. Skills come from the request only — never stored."""
    if not db_exists():
        return {"remote": [], "gulf": [],
                "filters": {"skills": req.skills, "years": req.years, "field": req.field}}
    top = max(1, min(req.top_per_side or 25, 50))
    data = _top50(req.skills or "", top)
    data["generated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    data["filters"] = {"skills": req.skills, "years": req.years, "field": req.field}
    return data


@router.get("/daily-queue")
def daily_queue(skills: str = "", size: int = DAILY_QUEUE_SIZE):
    """Today's plan: easiest-to-apply jobs from top opportunities, minus applied."""
    if not db_exists():
        return {"generated": datetime.now().strftime("%Y-%m-%d %H:%M"), "items": []}
    top = _top50(skills or "")
    pool = (top.get("remote") or []) + (top.get("gulf") or [])
    try:
        applied_ids = {a.get("job_id") for a in _list_applications().get("items", [])
                       if a.get("job_id")}
    except Exception:
        applied_ids = set()
    pool = [j for j in pool if j.get("job_id") and j["job_id"] not in applied_ids]
    jobs_by_id = {j.get("id"): j for j in fetch_all("SELECT * FROM jobs")}
    items = []
    for j in pool:
        job_row = jobs_by_id.get(j.get("job_id")) or {}
        sim = _simulate(job_row, skills or "") if job_row else None
        screen_qa = [{"q": q["q"], "answer": q["answer"], "risk": q.get("risk", "")}
                     for q in (sim["questions"][:5] if sim else [])]
        items.append({
            **j,
            "apply_method": ("mailto" if _apply_ease_bonus(j) == 0 else
                             "linkedin" if _apply_ease_bonus(j) == 2 else "direct"),
            "hr_message": _generate_hr_template(j.get("title", ""), j.get("company", ""), "en"),
            "screen_qa": screen_qa,
        })
    items.sort(key=lambda x: (_apply_ease_bonus(x), -x.get("depth", 0), -x.get("score", 0)))
    return {"generated": datetime.now().strftime("%Y-%m-%d %H:%M"), "items": items[:size]}


@router.get("/followups")
def followups():
    """Reminders for applications still 'applied' after the follow-up window."""
    try:
        items = _list_applications().get("items", [])
    except Exception:
        items = []
    now = datetime.now()
    due, waiting = [], 0
    for a in items:
        if (a.get("status") or "applied") != "applied":
            continue
        try:
            dt = datetime.fromisoformat(str(a.get("applied_at") or "").replace("Z", ""))
        except (ValueError, TypeError):
            continue
        days = (now - dt).days
        if days >= FOLLOWUP_DAYS - 2:
            due.append({**a, "days": days,
                        "overdue": days >= FOLLOWUP_DAYS + 1,
                        "suggested_message": _generate_hr_template(
                            a.get("title", ""), a.get("company", ""), "en")})
        else:
            waiting += 1
    due.sort(key=lambda x: -x["days"])
    return {"generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "followup_days": FOLLOWUP_DAYS, "due": due, "waiting": waiting}


@router.post("/hr-simulate")
def hr_simulate(req: SimulateIn):
    """Simulate HR/ATS screening for one job using request skills only."""
    if not db_exists():
        return {"error": "no jobs indexed"}
    job = next((j for j in fetch_all("SELECT * FROM jobs")
                if str(j.get("id")) == str(req.job_id)), None)
    if not job:
        return {"error": "job not found"}
    return _simulate(job, req.skills or "")


@router.post("/hr-simulate-top")
def hr_simulate_top(req: SimulateTopIn):
    """Simulate screening for top-N skill matches."""
    if not db_exists():
        return {"counts": {"pass": 0, "border": 0, "weak": 0}, "results": []}
    top = max(1, min(req.top or 50, 100))
    scored = []
    for j in fetch_all("SELECT * FROM jobs ORDER BY id DESC"):
        a = _analyze_for(req.skills or "", j)
        scored.append((_depth(req.skills or "", j, a), a.get("score", 0), j))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    results = [_simulate(j, req.skills or "") for _d, _s, j in scored[:top]]
    return {"counts": {
        "pass": sum(1 for r in results if r["score"] >= 75),
        "border": sum(1 for r in results if 55 <= r["score"] < 75),
        "weak": sum(1 for r in results if r["score"] < 55),
    }, "results": results}


@router.post("/cover-letter")
def cover_letter(req: CoverIn):
    """Template cover letter from ACTUAL matched skills + [Your Name] placeholders.

    Never invents years, savings, or contacts — the user fills their own facts.
    """
    company = req.company or "your company"
    analysis = analyze_job(req.skills or "", req.title or "", company)
    tops = analysis.get("matched", [])[:3]
    sig_en = "[Your Name] | [Phone] | [Email] | [LinkedIn]"
    sig_ar = "[الاسم] | [الهاتف] | [البريد] | [لينكدإن]"
    if (req.lang or "en") == "ar":
        if tops:
            bullets = "\n".join("• %s: %s" % (m.get("category", "").replace("_", " "),
                                              ", ".join(m.get("skills", []))) for m in tops)
        else:
            bullets = "• [اذكر مهاراتك المرتبطة بهذا الدور]"
        letter = ("عزيزي مدير التوظيف،\n\nأتقدم بطلب لشغل وظيفة %s في %s. "
                  "المهارات التالية من خبرتي مرتبطة مباشرة بهذا الدور:\n\n%s\n\n"
                  "[أضف فقرة إنجازاتك بأرقام حقيقية من عملك هنا]\n\n"
                  "يسعدني مناقشة كيف أسهم في فريقكم. سيرتي الذاتية مرفقة للمراجعة.\n\n"
                  "مع خالص التحيات،\n%s" % (req.title, company, bullets, sig_ar))
    else:
        if tops:
            bullets = "\n".join("• %s: %s" % (m.get("category", "").replace("_", " "),
                                              ", ".join(m.get("skills", []))) for m in tops)
        else:
            bullets = "• [List your skills relevant to this role]"
        letter = ("Dear Hiring Manager,\n\nI am writing to apply for the %s position at %s. "
                  "The following skills from my experience are directly relevant to this role:\n\n%s\n\n"
                  "[Add a paragraph with YOUR real achievement numbers here]\n\n"
                  "I would welcome the opportunity to discuss how I can contribute to your team. "
                  "My CV is attached for your review.\n\nSincerely,\n%s"
                  % (req.title, company, bullets, sig_en))
    return {"letter": letter}


@router.post("/cv-pdf")
def cv_pdf_experimental():
    """Experimental: server-side CV PDF needs Arabic fonts first.

    Temporary path: print any report from the browser (Ctrl+P).
    """
    return {"error": "experimental - server PDF not ready; use browser print",
            "status": 501}
