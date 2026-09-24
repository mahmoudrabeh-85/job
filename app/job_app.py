#!/usr/bin/env python3
"""
job_app.py — الواجهة الذكية لتحليل الوظائف
خادم Python يعمل على http://127.0.0.1:8767/
يقرأ من SQLite + يحلل CV + يعرض نتائج تفاعلية
"""
import sqlite3
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
import threading
import webbrowser
from datetime import datetime

PORT = 8767
BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "data" / "jobs.db"
CV_EN = BASE / "cv" / "candidate_EN.txt"
CV_AR = BASE / "cv" / "candidate_AR.txt"
HTML_FILE = BASE / "frontend" / "index.html"
PROFILE_FILE = BASE / "data" / "profile.json"
APPLICATIONS_FILE = BASE / "data" / "applications.json"

# ─── CV Analysis Engine ─────────────────────────────────────────────────
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
    "erp": {"course": "ERP Proficiency — Oracle / SAP / Odoo (Fundamentals)", "platform": "Oracle University / SAP Learning / Udemy", "duration": "2-3 months", "cost": "Free-$250", "priority": "high"},
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

def load_cv():
    cv_text = ""
    for p in [CV_EN, CV_AR]:
        if p.exists():
            cv_text += p.read_text(encoding="utf-8", errors="replace") + "\n"
    return cv_text.lower()

def analyze_job(cv_text, title, description):
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
                missing.append({"category": cat, "skills": cat_matched[:3], "severity": "high" if info["weight"] >= 7 else "medium"})
                score += info["weight"] * 0.3  # جزئي لأن التصنيف يطابق
    
    # نقاط الخبرة
    if any(w in combined for w in ["10+ years", "10 years", "15+", "senior", "lead", "director"]):
        score += 5; max_score += 5
    elif any(w in combined for w in ["5+ years", "5 years", "3+ years"]):
        score += 3; max_score += 3
    
    pct = min(int((score / max(max_score, 1)) * 100), 100) if max_score > 0 else 0
    
    return {
        "score": pct,
        "matched": matched,
        "missing": missing,
        "matched_count": len(matched),
        "missing_count": len(missing),
    }

def generate_hr_template(title, company, lang="en"):
    if lang == "en":
        return f"""Subject: Application for {title} — [Your Name]

Dear Hiring Manager,

I am writing to express my strong interest in the {title} position at {company}. With over 15 years of experience in pharmaceutical procurement and supply chain management in Egypt & Gulf, I bring a proven track record of achieving 11.5% cost savings through strategic vendor negotiation and supply localization.

Key qualifications:
• 18+ years in procurement, supply chain & distribution (20M+ EGP monthly volume)
• Expertise in vendor negotiation, contract management, sourcing & inventory governance
• Dual background in Sales & Procurement — bridging commercial & operational gaps
• Currently upskilling: ERP (Oracle / SAP / Odoo) — enrolled (2-3 months track)
• <2% stock-out rate across high-value inventory

I would welcome the opportunity to discuss how my experience aligns with your needs.

Best regards,
[Your Name] | [Phone] | [Email] | WhatsApp: https://wa.me/[phone] | Telegram: https://t.me/[phone] | LinkedIn: https://linkedin.com/in/[your-profile]"""
    else:
        return f"""الموضوع: طلب توظيف — [اسمك]

عزيزي مدير التوظيف،

أكتب للتعبير عن اهتمامي بوظيفة {title} في {company}. مع أكثر من 18 عاماً من الخبرة في إدارة المشتريات وسلسلة التوريد والتوزيع في مصر والخليج (حجم تداول 20M+ جنيه شهرياً)، أحقق وفراً 11٫5% عبر التفاوض وتوطين الموردين.

مؤهلاتي الرئيسية:
• 18+ عاماً في المشتريات وسلاسل الإمداد والتوزيع الدوائي
• خبرة في التفاوض، إدارة العقود، التوريد وحوكمة المخزون
• خلفية مزدوجة في المبيعات والمشتريات
• قيد التطوير حالياً: أنظمة ERP (Oracle / SAP / Odoo) — مسار 2-3 أشهر
• أقل من 2% معدل نفاد مخزون

أتطلع لمناقشة كيف تلائم خبرتي احتياجاتكم.

[اسمك] | ‎[Phone] | [Email] | واتساب: https://wa.me/[phone] | تليجرام: https://t.me/[phone] | لينكدإن: https://linkedin.com/in/[your-profile]"""

def get_jobs_from_db():
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM jobs WHERE score > 0 ORDER BY score DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ─── HTTP Server ────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass
    
    def _send(self, code, body, ctype="application/json", raw=False):
        if raw:
            data = body if isinstance(body, bytes) else body.encode("utf-8") if isinstance(body, str) else body
        else:
            data = (body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)).encode("utf-8")
        self.send_response(code)
        ct = ctype if raw else ctype + "; charset=utf-8"
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)
    
    def do_GET(self):
        parsed = urlparse(self.path)
        route = parsed.path
        qs = parse_qs(parsed.query)
        
        if route == "/" or route == "/index.html":
            html = HTML_FILE.read_text(encoding="utf-8")
            self._send(200, html, "text/html")
            return

        # ─── Static Files (CSS, JS, images from frontend/) ──────────────
        FRONTEND_DIR = HTML_FILE.parent
        static_exts = {".css": "text/css", ".js": "application/javascript", ".json": "application/json",
                        ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml",
                        ".ico": "image/x-icon", ".woff2": "font/woff2", ".woff": "font/woff"}
        for ext, mime in static_exts.items():
            if route.endswith(ext):
                fpath = FRONTEND_DIR / route.lstrip("/")
                if fpath.exists():
                    self._send(200, fpath.read_bytes(), mime, raw=True)
                    return
                # Also try relative path without leading slash
                fpath2 = FRONTEND_DIR / route[1:] if route.startswith("/") else FRONTEND_DIR / route
                if fpath2.exists():
                    self._send(200, fpath2.read_bytes(), mime, raw=True)
                    return
        
        if route == "/api/jobs":
            jobs = get_jobs_from_db()
            cv_text = load_cv()
            results = []
            for j in jobs:
                analysis = analyze_job(cv_text, j.get("title", ""), j.get("matched", "") or j.get("title", ""))
                results.append({
                    "id": j.get("id", ""),
                    "title": j.get("title", ""),
                    "company": j.get("company", "") or "",
                    "location": j.get("location", "") or "Remote",
                    "salary": j.get("salary_raw", "") or "",
                    "url": j.get("url", "#"),
                    "source": j.get("source", ""),
                    "posted": j.get("posted", ""),
                    "score_db": j.get("score", 0),
                    "analysis": analysis,
                })
            self._send(200, {"jobs": results, "total": len(results)})
            return
        
        if route == "/api/analyze":
            title = unquote(qs.get("title", [""])[0])
            desc = unquote(qs.get("desc", [""])[0])
            company = unquote(qs.get("company", [""])[0])
            cv_text = load_cv()
            analysis = analyze_job(cv_text, title, desc)
            hr_en = generate_hr_template(title, company, "en")
            hr_ar = generate_hr_template(title, company, "ar")
            
            gaps_with_advice = []
            for g in analysis["missing"]:
                advice = GAP_ADVICE.get(g["category"], {"course": f"دورة في {g['category']}", "platform": "Coursera/Udemy", "duration": "1-2 months", "cost": "Free-$100", "priority": "medium"})
                gaps_with_advice.append({**g, **advice})
            
            self._send(200, {
                "analysis": analysis,
                "hr_en": hr_en,
                "hr_ar": hr_ar,
                "gaps": gaps_with_advice,
            })
            return
        
        if route == "/api/search":
            try:
                # فلترة متقدمة للوظائف
                src_filter = qs.get("source", [None])[0]
                work_type = qs.get("work_type", [None])[0]
                min_score = int(qs.get("min_score", [0])[0])
                query = unquote(qs.get("q", [""])[0]).lower()
                skills = qs.get("skills", [None])[0]
                emp_type = qs.get("emp_type", [None])[0]
                location = qs.get("location", [None])[0]
                limit = int(qs.get("limit", [200])[0])
                
                if not DB_PATH.exists():
                    self._send(200, {"jobs": [], "total": 0, "filters": {}})
                    return
                
                conn = sqlite3.connect(str(DB_PATH))
                conn.row_factory = sqlite3.Row
                
                sql = "SELECT * FROM jobs WHERE 1=1"
                params = []
                
                if src_filter:
                    sources = [s.strip() for s in src_filter.split(",")]
                    placeholders = ",".join(["?" for _ in sources])
                    sql += f" AND source IN ({placeholders})"
                    params.extend(sources)
                
                if query:
                    sql += " AND (LOWER(title) LIKE ? OR LOWER(company) LIKE ? OR LOWER(location) LIKE ?)"
                    like_q = f"%{query}%"
                    params.extend([like_q, like_q, like_q])
                
                if location:
                    sql += " AND LOWER(location) LIKE ?"
                    params.append(f"%{location.lower()}%")
                
                sql += " ORDER BY score DESC LIMIT ?"
                params.append(limit)
                
                rows = conn.execute(sql, params).fetchall()
                conn.close()
                
                cv_text = load_cv()
                results = []
                for j in rows:
                    j = dict(j)  # sqlite3.Row → dict
                    analysis = analyze_job(cv_text, j.get("title", ""), j.get("matched", "") or j.get("title", ""))
                    
                    # تصفية حسب work_type
                    loc = (j.get("location", "") or "").lower()
                    if work_type == "remote" and "remote" not in loc:
                        continue
                    elif work_type == "onsite" and "remote" in loc:
                        continue
                    
                    # تصفية حسب المهارات
                    if skills:
                        skill_list = [s.strip().lower() for s in skills.split(",")]
                        matched_cats = [m["category"].lower() for m in analysis.get("matched", [])]
                        if not any(s in matched_cats for s in skill_list):
                            continue
                    
                    # تصفية حسب الحد الأدنى للتقييم
                    if analysis["score"] < min_score:
                        continue
                    
                    results.append({
                        "id": j.get("id", ""),
                        "title": j.get("title", ""),
                        "company": j.get("company", "") or "",
                        "location": j.get("location", "") or "Remote",
                        "salary": j.get("salary_raw", "") or "",
                        "url": j.get("url", "#"),
                        "source": j.get("source", ""),
                        "posted": j.get("posted", ""),
                        "score_db": j.get("score", 0),
                        "analysis": analysis,
                    })
                
                self._send(200, {
                    "jobs": results,
                    "total": len(results),
                    "filters": {
                        "source": src_filter,
                        "work_type": work_type,
                        "min_score": min_score,
                        "query": query,
                        "skills": skills,
                    }
                })
            except Exception as e:
                self._send(500, {"error": str(e)})
            return
        
        if route == "/api/stats":
            jobs = get_jobs_from_db()
            cv_text = load_cv()
            scores = []
            dist = {"0-24": 0, "25-49": 0, "50-69": 0, "70-84": 0, "85-100": 0}
            sources = {}
            for j in jobs:
                a = analyze_job(cv_text, j.get("title", ""), j.get("matched", "") or j.get("title", ""))
                s = a["score"]
                scores.append(s)
                if s < 25: dist["0-24"] += 1
                elif s < 50: dist["25-49"] += 1
                elif s < 70: dist["50-69"] += 1
                elif s < 85: dist["70-84"] += 1
                else: dist["85-100"] += 1
                src = j.get("source","other")
                sources[src] = sources.get(src,0)+1
            self._send(200, {
                "total_jobs": len(jobs),
                "total": len(jobs),
                "avg_score": sum(scores) // len(scores) if scores else 0,
                "max_score": max(scores) if scores else 0,
                "min_score": min(scores) if scores else 0,
                "score_distribution": dist,
                "sources": sources,
            })
            return
        
        # ─── Skill Gap Analysis Endpoints ────────────────────────────
        if route == "/api/gaps":
            self._send(200, analyze_skill_gaps())
            return

        if route == "/api/profile":
            profile = {}
            if PROFILE_FILE.exists():
                try:
                    profile = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
                except Exception:
                    pass
            if not profile:
                profile = {"name": "[Your Name]", "title": "Senior Procurement Manager",
                           "skills": ["purchasing","supply chain","distribution","ERP","cost reduction","negotiation","procurement","sales","media buying","pharma"]}
            self._send(200, profile)
            return

        if route == "/api/jobs_by_skill":
            skill = parse_qs(parsed.query).get("skill", [""])[0]
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT id, title, company, salary_raw, salary_annual, url, matched FROM jobs WHERE matched LIKE ? OR title LIKE ? ORDER BY COALESCE(score,0) DESC LIMIT 20",
                (f"%{skill}%", f"%{skill}%")
            ).fetchall()
            conn.close()
            self._send(200, {"skill": skill, "count": len(rows), "jobs": [dict(r) for r in rows]})
            return

        # ─── /api/v1/* aliases & new endpoints ───────────────────────────
        if route == "/api/v1/jobs":
            jobs = get_jobs_from_db()
            cv_text = load_cv()
            results = []
            for j in jobs:
                analysis = analyze_job(cv_text, j.get("title", ""), j.get("matched", "") or j.get("title", ""))
                results.append({
                    "id": j.get("id", ""),
                    "title": j.get("title", ""),
                    "company": j.get("company", "") or "",
                    "location": j.get("location", "") or "Remote",
                    "salary": j.get("salary_raw", "") or "",
                    "url": j.get("url", "#"),
                    "source": j.get("source", ""),
                    "posted": j.get("posted", ""),
                    "score_db": j.get("score", 0),
                    "analysis": analysis,
                })
            self._send(200, {"jobs": results, "total": len(results)})
            return

        if route == "/api/v1/stats":
            jobs = get_jobs_from_db()
            cv_text = load_cv()
            scores = []
            dist = {"0-24": 0, "25-49": 0, "50-69": 0, "70-84": 0, "85-100": 0}
            sources = {}
            for j in jobs:
                a = analyze_job(cv_text, j.get("title", ""), j.get("matched", "") or j.get("title", ""))
                s = a["score"]
                scores.append(s)
                if s < 25: dist["0-24"] += 1
                elif s < 50: dist["25-49"] += 1
                elif s < 70: dist["50-69"] += 1
                elif s < 85: dist["70-84"] += 1
                else: dist["85-100"] += 1
                src = j.get("source","other")
                sources[src] = sources.get(src,0)+1
            self._send(200, {
                "total_jobs": len(jobs),
                "total": len(jobs),
                "avg_score": sum(scores) // len(scores) if scores else 0,
                "max_score": max(scores) if scores else 0,
                "min_score": min(scores) if scores else 0,
                "score_distribution": dist,
                "sources": sources,
            })
            return

        if route == "/api/v1/swot":
            self._send(200, generate_swot())
            return

        if route == "/api/v1/company-vet":
            company = unquote(qs.get("company", [""])[0])
            self._send(200, company_vet(company))
            return

        if route == "/api/v1/applications":
            apps = load_applications()
            self._send(200, apps)
            return

        self._send(404, {"error": "not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        route = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        if route == "/api/v1/analyze":
            title = data.get("title", "")
            description = data.get("description", "")
            company = data.get("company", "")
            cv_text = load_cv()
            analysis = analyze_job(cv_text, title, description)
            hr_en = generate_hr_template(title, company, "en")
            hr_ar = generate_hr_template(title, company, "ar")
            
            gaps_with_advice = []
            for g in analysis["missing"]:
                advice = GAP_ADVICE.get(g["category"], {"course": f"دورة في {g['category']}", "platform": "Coursera/Udemy", "duration": "1-2 months", "cost": "Free-$100", "priority": "medium"})
                gaps_with_advice.append({**g, **advice})
            
            self._send(200, {
                "analysis": analysis,
                "hr_en": hr_en,
                "hr_ar": hr_ar,
                "gaps": gaps_with_advice,
            })
            return

        if route == "/api/v1/applications":
            apps = load_applications()
            new_app = {
                "job_id": data.get("job_id", ""),
                "title": data.get("title", ""),
                "company": data.get("company", ""),
                "url": data.get("url", ""),
                "status": data.get("status", "applied"),
                "applied_at": datetime.now().isoformat(),
            }
            apps["items"].append(new_app)
            save_applications(apps)
            self._send(201, new_app)
            return

        if route == "/api/v1/hr-template":
            title = data.get("title", "")
            company = data.get("company", "")
            lang = data.get("lang", "en")
            template = generate_hr_template(title, company, lang)
            self._send(200, {"template": template})
            return

        self._send(404, {"error": "not found"})

    def do_PATCH(self):
        parsed = urlparse(self.path)
        route = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        if route.startswith("/api/v1/applications/"):
            job_id = route.split("/")[-1]
            apps = load_applications()
            for app in apps["items"]:
                if app.get("job_id") == job_id:
                    if "status" in data:
                        app["status"] = data["status"]
                    if "notes" in data:
                        app["notes"] = data["notes"]
                    app["updated_at"] = datetime.now().isoformat()
                    save_applications(apps)
                    self._send(200, app)
                    return
            self._send(404, {"error": "application not found"})
            return

        self._send(404, {"error": "not found"})

# ═══════════════════════════════════════════════════════════════════════════
# Skill Gap Analysis Engine (from dev_dashboard_server.py)
# ═══════════════════════════════════════════════════════════════════════════
SKILL_PATTERNS = {
    "oracle":       [r"\boracle\b", r"oracle\s*(fusion|cloud|scm|erp|ebs)"],
    "sap":          [r"\bsap\b", r"sap\s*(mm|sd|s/?4hana|erp|bw|fico)"],
    "erp":          [r"\berp\b", r"enterprise resource planning", r"netsuite", r"dynamics\s*365", r"odoo"],
    "sql":          [r"\bsql\b", r"t-?sql", r"pl/?sql", r"postgresql", r"mysql", r"mssql"],
    "python":       [r"\bpython\b", r"\bpandas\b", r"\bnumpy\b", r"\bspark\b"],
    "power_bi":     [r"power\s*bi", r"powerbi"],
    "tableau":      [r"\btableau\b"],
    "crm":          [r"\bcrm\b", r"\bsalesforce\b", r"\bhubspot\b", r"dynamics\s*365", r"zoho\s*crm"],
    "data_analysis":[r"data\s*analysis", r"business\s*intelligence", r"\bbi\b.*analyst", r"data\s*analytics"],
    "project_management": [r"project\s*management", r"project\s*manager", r"\bpmp\b"],
    "pmp":          [r"\bpmp\b", r"project\s*management\s*professional"],
    "procurement":  [r"\bprocurement\b", r"purchasing", r"sourcing", r"vendor\s*management", r"strategic\s*sourcing"],
    "supply_chain": [r"supply\s*chain", r"logistics", r"warehouse", r"inventory\s*management", r"distribution"],
    "six_sigma":    [r"six\s*sigma", r"lean\s*six\s*sigma", r"green\s*belt", r"black\s*belt"],
    "lean":         [r"\blean\b", r"lean\s*management", r"\bkaizen\b", r"continuous\s*improvement"],
    "agile":        [r"\bagile\b", r"\bscrum\b", r"\bkanban\b", r"sprint"],
    "negotiation":  [r"\bnegotiat", r"contract\s*management", r"stakeholder\s*management"],
    "management":   [r"\bmanagement\b", r"\bdirector\b", r"\bvp\b", r"\bhead\s*of\b", r"\bleader"],
    "operations":   [r"\boperations\b", r"\bops\b", r"business\s*operations"],
    "pharma":       [r"\bpharma\b", r"pharmaceutical", r"\bdrug\b", r"biotech", r"clinical"],
    "medical":      [r"\bmedical\b", r"\bhealthcare\b", r"\bhealth\s*care\b", r"\bhospital\b"],
    "sales":        [r"\bsales\b", r"business\s*development", r"\bb2b\b", r"\bb2c\b", r"account\s*executive", r"revenue"],
    "marketing":    [r"\bmarketing\b", r"\bseo\b", r"\bsem\b", r"\bsocial\s*media\b", r"brand\s*management", r"content\s*marketing"],
    "english":      [r"english.*(?:c1|c2|fluent|advanced|native)", r"bilingual", r"multilingual"],
    "finance":      [r"\bfinance\b", r"\bfinancial\b", r"\baccounting\b", r"\bcfa\b", r"\bfp&a\b"],
    "excel":        [r"\bexcel\b", r"advanced\s*excel", r"vba", r"spreadsheet"],
    "ciprs":        [r"\bcips\b", r"chartered\s*institute.*procurement"],
}

USER_SKILLS = {"procurement","purchasing","supply_chain","distribution","cost_reduction","negotiation","sales","pharma","management","operations","excel","media_buying"}

SKILL_RESOURCES = {
    "oracle":           {"name":"Oracle SCM Cloud",       "course":"Oracle SCM Certification",     "platform":"Oracle University", "duration":"3-6 months",  "cost":"$200-500",  "priority":"high",   "salary_boost":"$15-25k"},
    "sap":              {"name":"SAP MM/SD",              "course":"SAP Certification",             "platform":"SAP Learning Hub",  "duration":"2-4 months",  "cost":"$100-300",  "priority":"high",   "salary_boost":"$10-20k"},
    "erp":              {"name":"ERP Systems",            "course":"ERP Fundamentals",              "platform":"Coursera/Udemy",    "duration":"1-2 months",  "cost":"Free-$50",  "priority":"medium", "salary_boost":"$5-10k"},
    "pmp":              {"name":"PMP",                    "course":"PMP Certification",             "platform":"PMI / Coursera",    "duration":"3-6 months",  "cost":"$400-600",  "priority":"high",   "salary_boost":"$10-15k"},
    "project_management":{"name":"Project Management",    "course":"PM Fundamentals",               "platform":"Coursera",          "duration":"1-2 months",  "cost":"Free-$50",  "priority":"medium", "salary_boost":"$5-10k"},
    "six_sigma":        {"name":"Six Sigma",              "course":"Six Sigma Green Belt",          "platform":"ASQ / Udemy",       "duration":"2-3 months",  "cost":"$200-400",  "priority":"medium", "salary_boost":"$5-10k"},
    "python":           {"name":"Python for Data",        "course":"Python Data Analysis",          "platform":"Coursera/edX",      "duration":"1-2 months",  "cost":"Free-$50",  "priority":"medium", "salary_boost":"$5-10k"},
    "power_bi":         {"name":"Power BI",               "course":"Power BI Certification",        "platform":"Microsoft Learn",   "duration":"1-2 months",  "cost":"Free-$100", "priority":"high",   "salary_boost":"$8-15k"},
    "sql":              {"name":"SQL",                    "course":"SQL for Business",              "platform":"Codecademy",        "duration":"1-2 months",  "cost":"Free-$50",  "priority":"high",   "salary_boost":"$5-10k"},
    "data_analysis":    {"name":"Data Analysis",          "course":"Data Analysis Professional",    "platform":"Google/Coursera",   "duration":"3-6 months",  "cost":"Free-$300", "priority":"high",   "salary_boost":"$10-20k"},
    "crm":              {"name":"CRM Systems",            "course":"Salesforce/HubSpot",            "platform":"Trailhead",         "duration":"1-2 months",  "cost":"Free",       "priority":"medium", "salary_boost":"$3-8k"},
    "negotiation":      {"name":"Negotiation",            "course":"Negotiation Mastery",           "platform":"Coursera/Harvard",  "duration":"1-2 months",  "cost":"Free-$100", "priority":"medium", "salary_boost":"$5-10k"},
    "management":       {"name":"Management",             "course":"Leadership & Management",       "platform":"Coursera",          "duration":"1-3 months",  "cost":"Free-$100", "priority":"medium", "salary_boost":"$5-15k"},
    "operations":       {"name":"Operations",             "course":"Operations Management",         "platform":"Coursera",          "duration":"1-2 months",  "cost":"Free-$50",  "priority":"medium", "salary_boost":"$5-10k"},
    "pharma":           {"name":"Pharmaceutical",         "course":"Pharma Industry Knowledge",     "platform":"Industry certs",    "duration":"3-6 months",  "cost":"$200-500",  "priority":"medium", "salary_boost":"$5-15k"},
    "sales":            {"name":"Sales",                  "course":"B2B Sales Strategy",            "platform":"Coursera",          "duration":"1-2 months",  "cost":"Free-$50",  "priority":"medium", "salary_boost":"$5-10k"},
    "excel":            {"name":"Excel Advanced",         "course":"Excel Advanced Formulas",       "platform":"LinkedIn Learning", "duration":"1 month",     "cost":"Free-$30",  "priority":"low",    "salary_boost":"$2-5k"},
    "finance":          {"name":"Finance",                "course":"Financial Analysis",            "platform":"Coursera",          "duration":"3-6 months",  "cost":"$200-500",  "priority":"medium", "salary_boost":"$5-10k"},
    "english":          {"name":"English C1",             "course":"Business English C1",           "platform":"British Council",   "duration":"6-12 months", "cost":"$200-500",  "priority":"high",   "salary_boost":"$10-20k"},
    "ciprs":            {"name":"CIPS",                   "course":"CIPS Level 4-6",                "platform":"CIPS.org",          "duration":"12-24 months","cost":"$1-3k",      "priority":"high",   "salary_boost":"$15-30k"},
    "procurement":      {"name":"Procurement",            "course":"Advanced Procurement",          "platform":"CIPS/Coursera",     "duration":"3-6 months",  "cost":"$200-500",  "priority":"high",   "salary_boost":"$5-15k"},
    "supply_chain":     {"name":"Supply Chain",           "course":"Supply Chain Management",       "platform":"Coursera/edX",      "duration":"3-6 months",  "cost":"$200-500",  "priority":"high",   "salary_boost":"$10-20k"},
}

def extract_skills_from_text(text):
    if not text:
        return set()
    combined = text.lower()
    found = set()
    for skill, patterns in SKILL_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, combined):
                found.add(skill)
                break
    return found

def analyze_skill_gaps():
    jobs = get_jobs_from_db()
    profile = {}
    if PROFILE_FILE.exists():
        try:
            profile = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    user_skills = set()
    for s in profile.get("skills", []):
        user_skills.add(s.lower().replace(" ", "_").replace("-", "_"))
    user_skills |= USER_SKILLS

    total = len(jobs)
    skill_frequency = {}
    skill_jobs = {}
    for job in jobs:
        parts = [job.get("title",""), job.get("matched",""), job.get("category",""), job.get("location","")]
        combined_text = " ".join(parts)
        required = extract_skills_from_text(combined_text)
        for skill in required:
            skill_frequency[skill] = skill_frequency.get(skill, 0) + 1
            if skill not in skill_jobs:
                skill_jobs[skill] = []
            if len(skill_jobs[skill]) < 5:
                salary_info = ""
                if job.get("salary_annual"):
                    salary_info = f"${int(job['salary_annual']):,}/yr"
                elif job.get("salary_raw"):
                    salary_info = job["salary_raw"]
                skill_jobs[skill].append({"title": job.get("title",""), "company": job.get("company",""), "salary": salary_info})

    gaps = []
    for skill, freq in sorted(skill_frequency.items(), key=lambda x: -x[1]):
        if skill not in user_skills and freq >= 2:
            res = SKILL_RESOURCES.get(skill, {})
            gaps.append({
                "skill": skill, "name": res.get("name", skill.replace("_"," ").title()),
                "frequency": freq, "total_jobs": total,
                "percentage": round(freq / total * 100, 1) if total else 0,
                "priority": res.get("priority", "medium"), "course": res.get("course",""),
                "platform": res.get("platform",""), "duration": res.get("duration","1-2 months"),
                "cost": res.get("cost","Free-$100"), "salary_boost": res.get("salary_boost","$3-8k"),
                "example_jobs": skill_jobs.get(skill, [])[:3]
            })

    matched = []
    for skill in user_skills:
        if skill in skill_frequency:
            res = SKILL_RESOURCES.get(skill, {})
            matched.append({"skill": skill, "name": res.get("name", skill.replace("_"," ").title()),
                           "frequency": skill_frequency[skill],
                           "percentage": round(skill_frequency[skill] / total * 100, 1) if total else 0})
    matched.sort(key=lambda x: -x["frequency"])

    return {"gaps": gaps, "matched": matched, "total_high_pay_jobs": total,
            "total_jobs_analyzed": total, "gaps_count": len(gaps), "matched_count": len(matched),
            "user_skills_count": len(user_skills)}

# ─── Applications Storage ─────────────────────────────────────────────────
def load_applications():
    if APPLICATIONS_FILE.exists():
        try:
            return json.loads(APPLICATIONS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"items": []}

def save_applications(data):
    APPLICATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    APPLICATIONS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def generate_swot():
    jobs = get_jobs_from_db()
    cv_text = load_cv()

    all_skills = set()
    high_score_jobs = []
    companies = set()
    locations = set()

    for j in jobs:
        a = analyze_job(cv_text, j.get("title", ""), j.get("matched", "") or j.get("title", ""))
        if a["score"] >= 70:
            high_score_jobs.append(j)
        companies.add(j.get("company", ""))
        locations.add(j.get("location", ""))
        for m in a.get("matched", []):
            all_skills.add(m["category"])
        for m in a.get("missing", []):
            all_skills.add(m["category"])

    # Build SWOT as objects expected by frontend: {title, evidence, impact}
    strengths = [{"title": s.replace("_"," ").title(), "evidence": f"متوفرة في سيرتك — مطلوبة في {len(jobs)} وظيفة", "impact": "قوة"} for s in list(all_skills)[:8]] or [{"title": "خبرة المشتريات والسلاسل", "evidence": "18+ سنة في التوريد الدوائي", "impact": "عالي"}]
    weaknesses_raw = []
    for cat in ["erp","python", "sql", "power_bi", "pmp", "six_sigma", "crm", "agile", "ai_ml"]:
        if cat not in all_skills or cat == "erp":
            adv = GAP_ADVICE.get(cat, {})
            if adv.get("priority") == "high" or cat == "erp":
                weaknesses_raw.append({"title": cat.replace("_"," ").title() + (" (قيد التعلم)" if cat=="erp" else ""), "evidence": adv.get("course","دورة مقترحة"), "impact": adv.get("priority","متوسط")})
    weaknesses = weaknesses_raw[:4]

    opportunities = []
    if len(high_score_jobs) > 0:
        opportunities.append({"title": f"{len(high_score_jobs)} وظيفة تطابق عالي (≥70%)", "evidence": "جاهزة للتقديم المجاني المباشر", "impact": "فرصة"})
    if any("remote" in (loc or "").lower() for loc in locations):
        opportunities.append({"title": "وظائف عن بُعد متاحة", "evidence": "190 وظيفة Remote في القاعدة", "impact": "فرصة"})
    if "pharma" in all_skills and "procurement" in all_skills:
        opportunities.append({"title": "تخصص فارما + مشتريات — طلب عالٍ في الخليج", "evidence": "ميزة تنافسية نادرة", "impact": "فرصة"})
    if not opportunities:
        opportunities.append({"title": "توسيع المصادر يزيد الفرص", "evidence": "أضف Bayt و LinkedIn", "impact": "فرصة"})

    threats = []
    if len(jobs) < 50:
        threats.append({"title": "حوض وظائف محدود", "evidence": "المصادر الحالية محدودة", "impact": "مخاطر"})
    else:
        threats.append({"title": "منافسة عالية على الأدوار العليا", "evidence": "362 وظيفة تطابق قوي — تميّز بسيرتك", "impact": "مخاطر"})
    if not any(c for c in companies if c):
        threats.append({"title": "بيانات شركات ناقصة", "evidence": "يصعب فحص جهة التوظيف", "impact": "مخاطر"})

    # Strategies with codes expected by frontend
    strategies = [
        {"code": "SO-1", "name": "استهدف الوظائف عالية التطابق أولاً", "desc": "قدّم على 70%+ عبر الزر المجاني ثم لينكدإن", "win": "أسرع عائد"},
        {"code": "WO-1", "name": "أكمل ERP كأولوية تعلم", "desc": "دورة Oracle/SAP (2-3 أشهر) — ترفع تطابقك 15%", "win": "فجوة حرجة"},
        {"code": "ST-1", "name": "فعّل تنبيهات LinkedIn", "desc": "ابحث بنفس الكلمات يومياً", "win": "تغطية"},
        {"code": "WT-1", "name": "وسّع إلى Bayt/Wuzzuf", "desc": "الخليج ومصر — مصادر جديدة", "win": "تنويع"},
    ]

    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "opportunities": opportunities,
        "threats": threats,
        "strategies": strategies,
        "stats": {"total": len(jobs)},
    }

def company_vet(company_name):
    if not company_name:
        return {"name": "", "vetted": False, "risk": "unknown", "signals": []}
    
    jobs = get_jobs_from_db()
    company_jobs = [j for j in jobs if j.get("company", "").lower() == company_name.lower()]
    
    signals = []
    if company_jobs:
        signals.append(f"Found {len(company_jobs)} job(s) in our database")
        sources = set(j.get("source", "") for j in company_jobs)
        signals.append(f"Sources: {', '.join(sources)}")
        titles = [j.get("title", "") for j in company_jobs[:3]]
        signals.append(f"Recent roles: {', '.join(titles)}")
    else:
        signals.append("No prior jobs found in database")
    
    risk = "low" if company_jobs else "unknown"
    
    return {
        "name": company_name,
        "vetted": len(company_jobs) > 0,
        "risk": risk,
        "job_count": len(company_jobs),
        "signals": signals,
    }

def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/"
    print(f"Job Analyzer Smart UI على: {url}")
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()