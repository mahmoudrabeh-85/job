"""
routers/vet.py — Company Vetting + Decision Support API
GET /api/v1/company-vet → local heuristic analysis, no external keys
Query: company, title, location, salary_raw, salary_annual, salary_currency, url, source, description
Returns: salary_expected, contract, company risk, verification links, docs checklist
"""
from fastapi import APIRouter, Query
from typing import Optional
import re
from urllib.parse import quote_plus

router = APIRouter(prefix="/api/v1", tags=["vetting"])


def _parse_salary_annual(salary_raw: str, salary_annual: Optional[float], salary_currency: Optional[str]):
    raw = (salary_raw or "").strip()
    annual = salary_annual
    curr = (salary_currency or "usd").lower() if salary_currency else "usd"
    if "€" in raw or "eur" in raw.lower():
        curr = "eur"
    if annual is None and raw:
        try:
            nums = re.findall(r"\d[\d,.]*", raw.replace(",", ""))
            vals = [float(n) for n in nums if n]
            if vals:
                annual = max(vals)
                low = raw.lower()
                if "hour" in low or "/hr" in low:
                    annual *= 2080
                elif "month" in low or "/mo" in low:
                    annual *= 12
                if curr not in ("usd", "eur"):
                    curr = "usd"
        except Exception:
            annual = None
    monthly = round(annual / 12) if annual else None
    # 30k EGP ≈ 600 USD / 550 EUR monthly (conservative)
    meets_threshold = True
    if monthly is not None:
        if curr == "eur":
            meets_threshold = monthly >= 550
        else:
            meets_threshold = monthly >= 600
    return {
        "raw": raw or None,
        "annual": annual,
        "currency": curr,
        "monthly_estimate": monthly,
        "meets_30k_egp": meets_threshold,
        "missing": annual is None,
    }


def _detect_contract(title: str, description: str, location: str):
    text = f"{title or ''} {description or ''} {location or ''}".lower()
    ctype = "full-time"
    duration = None
    signals = []
    if any(k in text for k in ["freelance", "freelancer", "فريلانس", "مستقل"]):
        ctype = "freelance"
        signals.append("freelance keyword")
    elif any(k in text for k in ["part-time", "part time", "دوام جزئي"]):
        ctype = "part-time"
        signals.append("part-time keyword")
    elif any(k in text for k in ["contract", "contractor", "مؤقت", "عقد"]):
        ctype = "contract"
        signals.append("contract keyword")
    elif any(k in text for k in ["intern", "تدريب"]):
        ctype = "internship"
        signals.append("intern keyword")

    m = re.search(r"(\d+)\s*[-+]?\s*(month|months|شهر|شهور|year|years|سنة|سنوات)", text)
    if m:
        try:
            num = m.group(1)
            unit = m.group(2)
            duration = f"{num} {unit}"
            signals.append(f"duration: {duration}")
        except Exception:
            pass

    confidence = "high" if signals else "low"
    return {"type": ctype, "duration": duration, "confidence": confidence, "signals": signals}


def _assess_company(company: str, url: str, source: str, title: str, description: str, salary_annual: Optional[float]):
    name = (company or "").strip()
    text = f"{title or ''} {description or ''}".lower()
    flags = []

    if not name or name.lower() in ("unknown", "—", "-", "n/a", "confidential"):
        flags.append({"code": "no_name", "level": "high", "msg_ar": "اسم الشركة غير مذكور — تحقق قبل إرسال بيانات حساسة"})
    if not url or url.strip() in ("", "#"):
        flags.append({"code": "no_url", "level": "medium", "msg_ar": "لا يوجد رابط تقديم رسمي — انسخ الرابط من المصدر الأصلي"})
    if salary_annual and salary_annual > 300000:
        flags.append({"code": "salary_too_high", "level": "high", "msg_ar": "راتب مرتفع جدا بشكل غير واقعي — علامة نصب شائعة"})
    for kw, msg in [
        ("fee", "يطلب رسوما — لا تدفع أي مبلغ للتقديم"),
        ("payment", "يذكر دفعا مقدما — توقف وتحقق"),
        ("telegram only", "تواصل عبر تيليجرام فقط بدون موقع — خطر"),
        ("whatsapp only", "تواصل واتساب فقط بدون بريد رسمي — خطر"),
        ("crypto", "يذكر عملات رقمية للدفع — تحقق بعمق"),
    ]:
        if kw in text:
            flags.append({"code": f"kw_{kw.replace(' ', '_')}", "level": "high", "msg_ar": msg})

    if "remote" in (description or "").lower() and not name:
        flags.append({"code": "remote_anon", "level": "medium", "msg_ar": "وظيفة عن بعد بدون اسم شركة — اطلب عقدا وبريدا رسميا"})

    high = sum(1 for f in flags if f["level"] == "high")
    risk_level = "high" if high >= 1 else ("medium" if flags else "low")

    # Guess website + verification links (no scraping, manual check)
    q_company = quote_plus(name) if name else quote_plus(title or "company")
    links = {
        "google": f"https://www.google.com/search?q={q_company}+company+reviews",
        "linkedin": f"https://www.linkedin.com/search/results/companies/?keywords={q_company}",
        "glassdoor": f"https://www.glassdoor.com/Search/results.htm?sc.keyword={q_company}",
        "trustpilot": f"https://www.trustpilot.com/search?query={q_company}",
        "crunchbase": f"https://www.crunchbase.com/textsearch?q={q_company}",
    }

    return {
        "name": name or None,
        "has_name": bool(name),
        "risk_flags": flags,
        "risk_level": risk_level,
        "verification_links": links,
        "note_ar": "التحقق اليدوي إلزامي قبل التقديم — افتح روابط Glassdoor و LinkedIn وابحث عن سنة التأسيس وآراء الموظفين",
    }


def _docs_checklist(location: str, contract_type: str, source: str):
    loc = (location or "").lower()
    docs = [
        {"id": "cv_en", "label_ar": "سيرة ذاتية إنجليزية محدثة PDF", "required": True},
        {"id": "cv_ar", "label_ar": "سيرة ذاتية عربية PDF", "required": False},
        {"id": "cover", "label_ar": "خطاب تغطية مخصص للشركة", "required": True},
        {"id": "linkedin", "label_ar": "رابط LinkedIn محدث", "required": True},
    ]
    if any(k in loc for k in ["saudi", "uae", "gulf", "qatar", "kuwait", "السعودية", "الإمارات", "الخليج"]):
        docs.append({"id": "passport", "label_ar": "جواز سفر ساري + صورة إقامة إن وجدت", "required": True})
    if "remote" in loc or contract_type in ("freelance", "contract"):
        docs.append({"id": "portfolio", "label_ar": "نماذج أعمال أو إثبات خبرة", "required": True})
        docs.append({"id": "contract_draft", "label_ar": "مسودة عقد تحدد الدفع ومدة العقد وطريقة التحويل", "required": True})
    docs.append({"id": "certs", "label_ar": "شهادات تدعم المهارة المطلوبة", "required": False})
    docs.append({"id": "id_copy", "label_ar": "صورة بطاقة شخصية عند الطلب الرسمي فقط", "required": False})
    return docs


@router.get("/company-vet")
def company_vet(
    company: str = Query("", description="Company name"),
    title: str = Query("", description="Job title"),
    location: str = Query("", description="Job location"),
    salary_raw: str = Query("", description="Raw salary text"),
    salary_annual: Optional[float] = Query(None),
    salary_currency: Optional[str] = Query(None),
    url: str = Query("", description="Apply URL"),
    source: str = Query("", description="Job source"),
    description: str = Query("", description="Job description snippet"),
):
    salary = _parse_salary_annual(salary_raw, salary_annual, salary_currency)
    contract = _detect_contract(title, description, location)
    comp = _assess_company(company, url, source, title, description, salary.get("annual"))
    docs = _docs_checklist(location, contract["type"], source)

    if comp["risk_level"] == "high":
        recommendation_ar = "لا تقدم قبل التحقق اليدوي — توجد إشارة خطر عالية"
    elif salary["missing"]:
        recommendation_ar = "اطلب الراتب ومدة العقد كتابة قبل المقابلة"
    elif not salary["meets_30k_egp"]:
        recommendation_ar = "الراتب أقل من حد 30 ألف جنيه — قارن بالبدائل قبل القبول"
    else:
        recommendation_ar = "الفرصة صالحة مبدئيا — أكمل فحص الشركة ثم جهز ملف التقديم"

    return {
        "salary_expected": salary,
        "contract": contract,
        "company": comp,
        "docs": docs,
        "decision_ar": recommendation_ar,
    }
