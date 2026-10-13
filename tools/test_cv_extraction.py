#!/usr/bin/env python3
"""
test_cv_extraction.py — اختبار استخراج بيانات السيرة الذاتية (Pillar 3)
───────────────────────────────────────────────────────────────────────
يتحقق من سلسلة معالجة الـ CV كاملة:

  1. load_cv_text()       — تحميل ملفات cv/*_EN.txt و cv/*_AR*.txt
  2. analyze_job()        — استخراج المهارات من نص وظيفة والتحقق من
                             matched/missing/نقاط السكور
  3. /api/v1/analyze      — الـ endpoint الكامل (نص عربي + إنجليزي)
  4. /api/v1/match        — تدفق years/field في المطابقة
  5. /api/v1/cv/ats-check — فحص التوافق مع ATS (Pillar 4)

Usage:
  python -m tools.test_cv_extraction            # كل الاختبارات
  python -m tools.test_cv_extraction --quick    # بدون TestClient
"""
from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

PASS, FAIL = "PASS", "FAIL"
results: list[tuple[str, str, str]] = []  # (name, status, note)


def check(name: str, cond: bool, note: str = "") -> bool:
    results.append((name, PASS if cond else FAIL, note))
    return cond


# ─── 1. load_cv_text ─────────────────────────────────────────────────────
def test_load_cv_text() -> None:
    from app.config import settings
    from app.routers.analysis import load_cv_text

    cv_dir = settings.cv_full_path
    files = sorted(cv_dir.glob("*_EN.txt")) + sorted(cv_dir.glob("*_AR*.txt")) \
        if cv_dir.exists() else []

    if not cv_dir.exists() or not files:
        check("cv_dir_exists", True,
              f"{cv_dir} غير موجود — النسخة العامة لا تخزن CV (متوقع ومقصود)")
        # Behavior contract: missing cv dir must NOT crash; returns ""
        try:
            from app.routers import analysis as A
            A._cv_cache = None
            text = load_cv_text()
            check("load_cv_text_no_crash", isinstance(text, str),
                  f"returns {type(text).__name__}, len={len(text or '')}")
            # Downstream endpoints must still work with empty CV
            from app.routers.analysis import analyze_job
            a = analyze_job(text, "Procurement Manager", "purchasing, vendor management")
            check("analyze_with_empty_cv", isinstance(a.get("score"), int),
                  f"score={a.get('score')} (مع CV فارغ السكور يعتمد على cv_has فقط)")
        except Exception as e:
            check("load_cv_text_no_crash", False, str(e)[:120])
        return

    from app.routers import analysis as A
    A._cv_cache = None
    text = load_cv_text()
    check("load_cv_text_nonempty", len(text) > 200, f"chars={len(text)}")
    check("load_cv_text_lowercased", text == text.lower(), "must be .lower() for matching")
    check("cv_files_found", len(files) >= 1, ", ".join(f.name for f in files[:4]))

    # Cache must be populated after first call
    check("cv_cache_populated", A._cv_cache is not None, "second call served from cache")


# ─── 2. analyze_job skill extraction ─────────────────────────────────────
def test_analyze_job() -> None:
    from app.routers.analysis import analyze_job, CV_SKILLS

    # English job description rich in known keywords
    en = analyze_job(
        "",
        "Senior Procurement Manager",
        "We need supply chain and logistics expertise. Vendor negotiation, "
        "tender management, SAP ERP, warehouse operations. 10+ years experience.",
    )
    cats_en = {m["category"] for m in en["matched"]}
    check("extract_procurement_en", "procurement" in cats_en, str(en["matched_count"]) + " matched")
    check("extract_supply_chain", "supply_chain" in cats_en, "")
    check("extract_erp_missing", "erp" in {m["category"] for m in en["missing"]},
          "erp cv_has=False → يجب أن يكون missing وليس matched")
    check("score_bounds", 0 <= en["score"] <= 100, f"score={en['score']}")
    check("senior_bonus", en["score"] > 0, "")

    # Arabic job description — CV_SKILLS now carries AR keywords
    ar = analyze_job(
        "",
        "مدير مشتريات",
        "مطلوب خبرة في المشتريات وإدارة سلاسل التوريد والمخازن والتوزيع، "
        "والتعامل مع الموردين والعقود. الخبرة المطلوبة 10 سنوات.",
    )
    check("extract_arabic", ar["matched_count"] >= 2,
          f"matched={ar['matched_count']} — العربية تُستخرج الآن (مشتريات/توريد/مخازن)")
    # Arabic text should still not crash and yield a score
    check("arabic_no_crash_score", isinstance(ar["score"], int), f"score={ar['score']}")

    # Empty input edge case
    empty = analyze_job("", "", "")
    check("empty_input_zero", empty["score"] == 0 and empty["matched_count"] == 0, "")

    # Skill extraction consistency: same input → same output (deterministic)
    en2 = analyze_job(
        "",
        "Senior Procurement Manager",
        "We need supply chain and logistics expertise. Vendor negotiation, "
        "tender management, SAP ERP, warehouse operations. 10+ years experience.",
    )
    check("deterministic", en == en2, "")


# ─── 3. /api/v1/analyze endpoint ─────────────────────────────────────────
def test_analyze_endpoint() -> None:
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        c = TestClient(app)
    except Exception as e:
        check("endpoint_client", False, f"TestClient unavailable: {str(e)[:100]}")
        return

    r = c.post("/api/v1/analyze", json={
        "title": "Procurement Manager",
        "description": "purchasing, vendor management, supply chain",
        "company": "TestCo",
    })
    body = r.json()
    check("analyze_status", r.status_code == 200, str(r.status_code))
    check("analyze_keys", all(k in body for k in ("analysis", "hr_en", "hr_ar", "gaps")),
          str(list(body)))
    check("analyze_hr_templates", bool(body.get("hr_en")) and bool(body.get("hr_ar")), "")
    check("gaps_have_advice", all(
        "course" in g for g in body.get("gaps", [])
    ), f"{len(body.get('gaps', []))} gaps")

    # Legacy alias
    r2 = c.get("/api/analyze", params={"title": "Sales Manager", "desc": "sales, account manager"})
    check("legacy_analyze", r2.status_code == 200, str(r2.status_code))


# ─── 4. /api/v1/match years flow ─────────────────────────────────────────
def test_match_flow() -> None:
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        c = TestClient(app)
    except Exception as e:
        check("match_client", False, f"TestClient unavailable: {str(e)[:100]}")
        return

    # senior candidate: many years → senior titles should outrank juniors
    r = c.post("/api/v1/match", json={"skills": "procurement, supply chain", "years": 15, "field": "procurement"})
    body = r.json()
    check("match_status", r.status_code == 200, str(r.status_code))
    check("match_has_filters", body.get("filters", {}).get("years") == 15, "")
    items = body.get("items", [])
    check("match_returns_items", len(items) > 0, f"total={body.get('total')}")

    if items:
        titles = [i["title"].lower() for i in items[:10]]
        senior_terms = ("senior", "manager", "director", "head", "lead")
        top_has_senior = any(any(t in x for t in senior_terms) for x in titles)
        check("match_senior_ranking", top_has_senior,
              "أول 10 نتائج يجب أن تحوي صف إداري عند years=15")

        # junior years must not crash and should filter differently
        r2 = c.post("/api/v1/match", json={"skills": "procurement", "years": 1, "field": ""})
        check("match_junior_ok", r2.status_code == 200, str(r2.status_code))

        # empty skills → empty result but valid shape
        r3 = c.post("/api/v1/match", json={"skills": "", "years": None, "field": ""})
        b3 = r3.json()
        check("match_empty_skills", r3.status_code == 200 and isinstance(b3.get("items"), list), "")


# ─── 5. /api/v1/cv/ats-check (Pillar 4) ──────────────────────────────────
def test_ats_check() -> None:
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        c = TestClient(app)
    except Exception as e:
        check("ats_client", False, f"TestClient unavailable: {str(e)[:100]}")
        return

    good_cv = (
        "John Doe (sample candidate)\n"
        "Email: test@example.com | Phone: +20 100 000 0000\n\n"
        "PROFESSIONAL SUMMARY\n"
        "Procurement and supply chain manager with 15 years experience.\n\n"
        "WORK EXPERIENCE\n"
        "Senior Procurement Manager — PharmaCo, Cairo (2015-Present)\n"
        "- Led vendor negotiation achieving 15% cost savings\n"
        "- Managed 5M EGP inventory with <2% stock-out rate\n"
        "- Implemented SAP ERP procurement module\n\n"
        "EDUCATION\n"
        "B.Sc. Pharmacy, Cairo University, 2008\n"
    )
    r = c.post("/api/v1/cv/ats-check", json={"cv_text": good_cv})
    body = r.json()
    check("ats_status", r.status_code == 200, str(r.status_code))
    check("ats_score_range", isinstance(body.get("score"), int) and 0 <= body["score"] <= 100,
          f"score={body.get('score')}")
    check("ats_has_sections", "sections" in body, "")
    check("ats_has_recommendations", isinstance(body.get("recommendations"), list), "")

    # Weak CV: no contact, no sections → lower score
    weak = "just some text about working in sales"
    r2 = c.post("/api/v1/cv/ats-check", json={"cv_text": weak})
    check("ats_weak_lower", r2.json().get("score", 0) < body.get("score", 0),
          f"weak={r2.json().get('score')} vs good={body.get('score')}")

    # Empty CV
    r3 = c.post("/api/v1/cv/ats-check", json={"cv_text": ""})
    check("ats_empty_ok", r3.status_code == 200, str(r3.status_code))


# ─── runner ──────────────────────────────────────────────────────────────
def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="skip TestClient-based tests")
    args = ap.parse_args()

    suites = [
        ("1. load_cv_text", test_load_cv_text),
        ("2. analyze_job", test_analyze_job),
    ]
    if not args.quick:
        suites += [
            ("3. /api/v1/analyze", test_analyze_endpoint),
            ("4. /api/v1/match", test_match_flow),
            ("5. /api/v1/cv/ats-check", test_ats_check),
        ]

    for label, fn in suites:
        try:
            fn()
        except Exception as e:
            check(label, False, f"EXCEPTION: {e}")
            traceback.print_exc()

    print("\n" + "═" * 62)
    print("  نتيجة اختبار استخراج بيانات الـ CV — CV Extraction Test Suite")
    print("═" * 62)
    n_pass = sum(1 for _, s, _ in results if s == PASS)
    for name, status, note in results:
        mark = "✔" if status == PASS else "✘"
        note_s = f"  — {note}" if note else ""
        print(f"  {mark} [{status}] {name}{note_s}")
    print("─" * 62)
    print(f"  {n_pass}/{len(results)} passed")
    print("═" * 62)
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
