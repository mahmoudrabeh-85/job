#!/usr/bin/env python3
"""
job_analyzer.py — أداة تحليل الوظائف + تقييم CV + فجوة المهارات + قوالب HR
المخرجات: تقرير HTML شامل لكل وظيفة (رابط + تحليل + فجوة + رسالة HR + خطوات)
"""
import sqlite3
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "data" / "jobs.db"
CV_EN = BASE / "cv" / "candidate_EN.txt"
CV_AR = BASE / "cv" / "candidate_AR.txt"
OUTPUT = BASE / "data" / "analysis_report.html"

# ─── CV Skills Extraction ───────────────────────────────────────────────
CV_SKILLS = {
    "procurement": ["procurement", "purchasing", "sourcing", "buyer", "buying", "vendor management", "negotiation", "contract management", "rfq", "rfp", "tender"],
    "supply_chain": ["supply chain", "logistics", "inventory", "warehouse", "distribution", "stock", "procurement", "vendor", "supplier"],
    "sales": ["sales", "business development", "account executive", "account manager", "revenue", "client", "customer"],
    "erp": ["erp", "oracle", "sap", "odoo", "netsuite", "dynamics", "salesforce"],
    "pharma": ["pharmaceutical", "pharma", "drug", "medicine", "healthcare", "medical", "clinical", "fda", "gdp"],
    "management": ["manager", "leadership", "team lead", "supervision", "management", "director"],
    "excel": ["excel", "spreadsheet", "data analysis", "reporting", "dashboard"],
    "operations": ["operations", "process improvement", "quality", "compliance", "audit"],
}

CV_EXPERIENCE = {
    "years_total": 15,
    "years_procurement": 10,
    "years_sales": 5,
    "education": "Bachelor of Commerce (Accounting) - Cairo University",
    "certifications": ["Online training in Procurement Management", "Sales training", "Supply Chain training"],
    "languages": {"Arabic": "Native", "English": "B1-B2"},
}

# ─── Gap Analysis Templates ─────────────────────────────────────────────
GAP_ADVICE = {
    "oracle": {"course": "Oracle SCM Cloud Certification", "platform": "Oracle University / Coursera", "duration": "3-6 months", "cost": "$200-500"},
    "sap": {"course": "SAP MM/SD Certification", "platform": "SAP Learning Hub / Udemy", "duration": "2-4 months", "cost": "$100-300"},
    "pmp": {"course": "PMP Certification", "platform": "PMI / Coursera", "duration": "3-6 months", "cost": "$400-600"},
    "six_sigma": {"course": "Six Sigma Green Belt", "platform": "ASQ / Udemy", "duration": "2-3 months", "cost": "$200-400"},
    "python": {"course": "Python for Data Analysis", "platform": "Coursera / edX", "duration": "1-2 months", "cost": "Free-$50"},
    "power_bi": {"course": "Power BI Certification", "platform": "Microsoft Learn / Udemy", "duration": "1-2 months", "cost": "Free-$100"},
    "sql": {"course": "SQL for Business Analysis", "platform": "Codecademy / Coursera", "duration": "1-2 months", "cost": "Free-$50"},
    "digital_marketing": {"course": "Digital Marketing Certification", "platform": "Google / HubSpot", "duration": "1-2 months", "cost": "Free"},
    "data_analysis": {"course": "Data Analysis with Excel/Python", "platform": "Coursera / Google", "duration": "2-3 months", "cost": "Free-$100"},
    "project_management": {"course": "Project Management Fundamentals", "platform": "Coursera / LinkedIn Learning", "duration": "1-2 months", "cost": "Free-$50"},
    "lean": {"course": "Lean Management", "platform": "Coursera / Udemy", "duration": "1-2 months", "cost": "Free-$100"},
    "agile": {"course": "Agile/Scrum Certification", "platform": "Scrum.org / Udemy", "duration": "1-2 months", "cost": "$100-200"},
    "crm": {"course": "CRM Administration (Salesforce/HubSpot)", "platform": "Trailhead / HubSpot Academy", "duration": "1-2 months", "cost": "Free"},
    "power_automate": {"course": "Power Automate / RPA", "platform": "Microsoft Learn", "duration": "1 month", "cost": "Free"},
    "tableau": {"course": "Tableau Desktop Specialist", "platform": "Tableau Public / Coursera", "duration": "1-2 months", "cost": "Free-$100"},
    "ai_ml": {"course": "AI for Business", "platform": "Coursera / Google AI", "duration": "2-3 months", "cost": "Free-$100"},
    "cybersecurity": {"course": "Cybersecurity Fundamentals", "platform": "CompTIA / Coursera", "duration": "2-3 months", "cost": "$200-400"},
    "cloud": {"course": "AWS/Azure Fundamentals", "platform": "AWS / Microsoft Learn", "duration": "1-2 months", "cost": "Free-$100"},
    "scrum": {"course": "Scrum Master Certification", "platform": "Scrum.org / Udemy", "duration": "1-2 months", "cost": "$100-200"},
    "change_management": {"course": "Change Management", "platform": "Prosci / Coursera", "duration": "1-2 months", "cost": "$200-400"},
}

def load_cv():
    """يقرأ ملف CV النصي ويستخرج المهارات."""
    cv_text = ""
    for p in [CV_EN, CV_AR]:
        if p.exists():
            cv_text += p.read_text(encoding="utf-8", errors="replace") + "\n"
    return cv_text.lower()

def match_cv_to_job(cv_text, job_title, job_desc):
    """يقارن CV مع وظيفة ويعطي تفصيلاً."""
    combined = (job_title + " " + job_desc).lower()
    
    matched = []
    missing = []
    score = 0
    
    for category, keywords in CV_SKILLS.items():
        cat_matched = [k for k in keywords if k in combined]
        if cat_matched:
            # spécial case: erp always missing per 2026-09-16 decision
            if category == "erp":
                missing.append({"category": category, "skills": cat_matched, "severity": "high"})
                score += 0  # لا تُحتسب أبداً ضمن matched
            else:
                # هل لدى المرشح هذه المهارة؟
                cv_has = [k for k in cat_matched if k in cv_text]
                if cv_has:
                    matched.append({"category": category, "skills": cv_has, "match": "strong"})
                    score += len(cv_has) * 3
                else:
                    # المهارة مطلوبة لكن ليست في CV
                    missing.append({"category": category, "skills": cat_matched, "severity": "high" if category in ["procurement", "supply_chain"] else "medium"})
                    score += 1  # نقطة صغيرة لأن التصنيف يطابق
    
    # نقاط إضافية للخبرة
    if any(w in combined for w in ["10+ years", "10 years", "15+", "senior", "lead", "director"]):
        if CV_EXPERIENCE["years_total"] >= 10:
            score += 5
    if any(w in combined for w in ["5+ years", "5 years"]):
        if CV_EXPERIENCE["years_total"] >= 5:
            score += 3
    
    return {
        "score": min(score, 100),
        "matched": matched,
        "missing": missing,
        "total_matched": len(matched),
        "total_missing": len(missing),
    }

def generate_hr_template(job, analysis, lang="en"):
    """يولّد رسالة HR مخصصة للوظيفة."""
    title = job.get("title", "Position")
    company = job.get("company", "Your Company")
    
    if lang == "en":
        template = f"""Subject: Application for {title} — [Your Name]

Dear Hiring Manager,

I am writing to express my strong interest in the {title} position at {company}. With over 15 years of experience in pharmaceutical procurement and supply chain management, I bring a proven track record of achieving 15% cost savings through strategic vendor negotiation and optimizing multi-vendor networks.

My key qualifications include:
• 10+ years managing procurement operations across Egypt and the Gulf
• Expertise in vendor negotiation, contract management, and cost reduction
• Dual background in Sales & Procurement — uniquely versatile for commercial roles
• ERP proficiency (Oracle, SAP, Odoo) with advanced Excel reporting
• Track record of maintaining <2% stock-out rates across 5M+ EGP inventory

I am confident that my combination of strategic procurement expertise and sales acumen would make me a valuable addition to {company}.

I would welcome the opportunity to discuss how my experience aligns with your needs.

Best regards,
[Your Name]
 | [Phone]
[Email]"""
    else:
        template = f"""الموضوع: طلب توظيف لوظيفة {title} — [اسمك]

عزيزي مدير التوظيف،

أكتب לכם للتعبير عن اهتمامي القوي بوظيفة {title} في {company}. مع أكثر من 15 عاماً من الخبرة في إدارة المشتريات وسلسلة التوريد في القطاع الدوائي، أحضر سجلاً حافلاً بالإنجازات بما في ذلك تحقيق وفورات 15% في التكاليف من خلال التفاوض الاستراتيجي مع الموردين.

مؤهلاتي الرئيسية تشمل:
• أكثر من 10 سنوات في إدارة عمليات المشتريات في مصر والخليج
• خبرة في التفاوض مع الموردين وإدارة العقود وتقليص التكاليف
• خلفية مزدوجة في المبيعات والمشتريات — مرونة فريدة للأدوار التجارية
• إتقان أنظمة ERP (Oracle, SAP, Odoo) مع تقارير Excel متقدمة
• سجل حافل بأقل من 2% معدل نفاد مخزون عبر مخزون بقيمة أكثر من 5 مليون جنيه

 أنا على ثقة بأن تركيبي من خبرة المشتريات الاستراتيجية وفطنة المبيعات سيشكّل إضافة قيّمة لـ {company}.

أتطلع إلى فرصة مناقشة مدى تطابق خبرتي مع احتياجاتكم.

مع خالص التقدير،
[اسمك]
 | [Phone]
[Email]"""
    
    return template

def generate_html_report(jobs, cv_text):
    """يولّد تقرير HTML شامل."""
    analyses = []
    for job in jobs:
        title = job.get("title", "")
        company = job.get("company", "")
        desc = job.get("description", "")
        url = job.get("url", "")
        score = job.get("score", 0)
        
        analysis = match_cv_to_job(cv_text, title, desc)
        hr_en = generate_hr_template(job, analysis, "en")
        hr_ar = generate_hr_template(job, analysis, "ar")
        
        # نصائح لكل مهارة ناقصة
        gap_details = []
        for gap in analysis["missing"]:
            for skill in gap["skills"]:
                if skill in GAP_ADVICE:
                    gap_details.append({"skill": skill, **GAP_ADVICE[skill]})
                else:
                    gap_details.append({"skill": skill, "course": f"دورة في {skill}", "platform": "Coursera/Udemy", "duration": "1-2 أشهر", "cost": "Free-$100"})
        
        analyses.append({
            "job": job,
            "analysis": analysis,
            "hr_en": hr_en,
            "hr_ar": hr_ar,
            "gap_details": gap_details,
        })
    
    # ترتيب حسب النقاط
    analyses.sort(key=lambda x: x["analysis"]["score"], reverse=True)
    
    # بناء HTML
    html_parts = []
    for i, item in enumerate(analyses):
        job = item["job"]
        a = item["analysis"]
        
        matched_html = ""
        for m in a["matched"]:
            skills = ", ".join(m["skills"][:5])
            matched_html += f'<span class="tag match">{m["category"]}: {skills}</span>'
        
        missing_html = ""
        for g in item["gap_details"]:
            missing_html += f'''
            <div class="gap-item">
              <div class="gap-skill">{g["skill"]}</div>
              <div class="gap-detail">📚 {g["course"]} — {g["platform"]}</div>
              <div class="gap-detail">⏱️ {g["duration"]} | 💰 {g["cost"]}</div>
            </div>'''
        
        hr_tabs = f'''
        <div class="hr-tabs">
          <button class="tab-btn active" onclick="showTab('en-{i}')">English</button>
          <button class="tab-btn" onclick="showTab('ar-{i}')">عربي</button>
        </div>
        <div class="tab-content active" id="en-{i}"><pre>{item["hr_en"]}</pre></div>
        <div class="tab-content" id="ar-{i}"><pre>{item["hr_ar"]}</pre></div>'''
        
        score_color = "#7ee0a3" if a["score"] >= 60 else "#ffd166" if a["score"] >= 30 else "#ff6b6b"
        
        html_parts.append(f'''
        <div class="job-card">
          <div class="job-header">
            <div class="job-title">{job.get("title", "")}</div>
            <div class="job-company">{job.get("company", "")} · {job.get("location", "Remote")}</div>
            <div class="job-score" style="color:{score_color}">{a["score"]}/100</div>
          </div>
          <div class="job-match">
            <strong>✅ المهارات المطابقة ({a["total_matched"]}):</strong><br>
            {matched_html if matched_html else '<span class="tag match">الخبرة العامة مطابقة</span>'}
          </div>
          <div class="job-missing">
            <strong>⚠️ الفجوة ({a["total_missing"]} مهارة ناقصة):</strong>
            {missing_html if missing_html else '<span class="tag ok">لا توجد فجوات رئيسية</span>'}
          </div>
          <div class="job-links">
            <a href="{job.get("url", "#")}" target="_blank" class="btn-apply">🚀 قدّم الآن</a>
          </div>
          <div class="job-hr">
            <strong>📝 رسالة HR:</strong>
            {hr_tabs}
          </div>
        </div>''')
    
    return "\n".join(html_parts)

def main():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)
    
    cv_text = load_cv()
    if not cv_text.strip():
        print("ERROR: CV files not found or empty")
        sys.exit(1)
    
    # قراءة الوظائف من قاعدة البيانات
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT title, company, location, salary_raw, matched, url, score, source
        FROM jobs WHERE score > 0
        ORDER BY score DESC LIMIT 20
    """)
    
    jobs = []
    for row in cursor.fetchall():
        jobs.append({
            "title": row["title"] or "",
            "company": row["company"] or "",
            "location": row["location"] or "Remote",
            "salary": row["salary_raw"] or "unknown",
            "url": row["url"] or "#",
            "score": row["score"] or 0,
            "matched_skills": row["matched"] or "",
            "description": row["matched"] or "",
            "source": row["source"] or "",
        })
    conn.close()
    
    if not jobs:
        print("ERROR: No jobs found in database")
        sys.exit(1)
    
    # توليد التقرير
    report_html = generate_html_report(jobs, cv_text)
    
    # ملف HTML كامل
    full_html = f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>📊 تحليل الوظائف — [Your Name]</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #0f1222; color: #e6e9f5; padding: 20px; }}
  h1 {{ color: #ffd166; font-size: 22px; margin-bottom: 6px; }}
  .subtitle {{ color: #8fa0c8; font-size: 13px; margin-bottom: 20px; }}
  .stats {{ display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }}
  .stat {{ background: #171b33; border: 1px solid #262c4d; border-radius: 8px; padding: 10px 18px; }}
  .stat b {{ color: #ffd166; }}
  .job-card {{ background: #171b33; border: 1px solid #262c4d; border-radius: 12px; padding: 18px; margin-bottom: 16px; }}
  .job-header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }}
  .job-title {{ font-size: 16px; font-weight: 700; color: #ffd166; }}
  .job-company {{ color: #8fa0c8; font-size: 13px; }}
  .job-score {{ font-size: 20px; font-weight: 900; }}
  .job-match, .job-missing {{ margin: 10px 0; font-size: 13px; }}
  .tag {{ display: inline-block; background: #232a4d; color: #e6e9f5; border-radius: 6px; padding: 4px 10px; margin: 3px 4px; font-size: 11.5px; }}
  .tag.match {{ background: #1a3a2a; color: #7ee0a3; border: 1px solid #2a5a3a; }}
  .tag.missing {{ background: #3a2a1a; color: #ffd166; border: 1px solid #5a4a2a; }}
  .tag.ok {{ background: #1a3a2a; color: #7ee0a3; }}
  .gap-item {{ background: #1a1530; border: 1px solid #2a2050; border-radius: 8px; padding: 10px; margin: 6px 0; }}
  .gap-skill {{ font-weight: 700; color: #ffd166; font-size: 13px; }}
  .gap-detail {{ color: #8fa0c8; font-size: 12px; margin-top: 3px; }}
  .btn-apply {{ display: inline-block; background: #ffd166; color: #0f1222; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 700; text-decoration: none; font-size: 14px; margin: 8px 0; }}
  .btn-apply:hover {{ background: #ffe08a; }}
  .job-hr {{ margin-top: 14px; }}
  .hr-tabs {{ display: flex; gap: 6px; margin-bottom: 8px; }}
  .tab-btn {{ background: #232a4d; color: #ffd166; border: 0; border-radius: 6px; padding: 6px 14px; cursor: pointer; font-size: 12px; }}
  .tab-btn.active {{ background: #ffd166; color: #0f1222; }}
  .tab-content {{ display: none; }}
  .tab-content.active {{ display: block; }}
  .tab-content pre {{ background: #0b0e1e; border: 1px solid #2a3160; border-radius: 8px; padding: 12px; font-size: 12px; direction: ltr; text-align: left; white-space: pre-wrap; word-break: break-word; font-family: Consolas, monospace; color: #b8f5c9; max-height: 400px; overflow-y: auto; }}
</style>
</head>
<body>
<h1>📊 تحليل الوظائف — تقييم CV + فجوة المهارات + قوالب HR</h1>
<div class="subtitle">المُعد: [اسمك] · {len(jobs)} وظيفة محللة · آخر تحديث: 2026-09-15</div>
<div class="stats">
  <div class="stat">📋 وظائف: <b>{len(jobs)}</b></div>
  <div class="stat">📊 متوسط التقييم: <b>{sum(j["score"] for j in jobs)//len(jobs) if jobs else 0}</b></div>
</div>
{report_html}
<script>
function showTab(id) {{
  const card = document.getElementById(id).closest('.job-card');
  card.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  card.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  event.target.classList.add('active');
}}
</script>
</body>
</html>'''
    
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(full_html, encoding="utf-8")
    print(f"[OK] Analysis report: {OUTPUT}")
    print(f"[OK] Jobs analyzed: {len(jobs)}")
    print(f"[OK] Top match: {jobs[0]['title'] if jobs else 'N/A'} (score: {jobs[0]['score'] if jobs else 0})")

if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()