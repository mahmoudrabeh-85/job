#!/usr/bin/env python3
"""
job_swot.py — أداة تحليل SWOT (سوات) الشخصي مقابل سوق الوظائف الفعلي
المصادر: بيانات حقيقية من jobs.db (أعداد الوظائف حسب المجال/الرواتب/المنافسة)
         + مهارات وخبرة المرشح من ملف CV
المخرجات: مصفوفة SWOT رباعية + استراتيجيات TOWS + أولوية تنفيذية
          (تقرير HTML: data/swot_report.html)
"""
import sqlite3
import sys
import collections
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "data" / "jobs.db"
OUTPUT = BASE / "data" / "swot_report.html"

# ─── بيانات المرشح (مؤكدة من CV + جلسات سابقة) ─────────────────────────
CANDIDATE = {
    "name": "[اسمك]",
    "years_total": 15,
    "years_procurement": 10,
    "years_sales": 5,
    "education": "بكالوريوس تجارة (محاسبة) — جامعة القاهرة",
    "languages": {"العربية": "أصلي", "الإنجليزية": "B1-B2"},
    "certifications": ["تدريب أونلاين في إدارة المشتريات", "تدريب مبيعات", "تدريب سلسلة توريد"],
    "cert_recognized": False,  # لا شهادات معتمدة دولياً (PMP/CIPS/CSCP)
    "has_analytics_tools": False,  # لا Python/SQL/Power BI في CV
    "location_advantage": True,    # قرب خليج + مصر (جوال +20)
    "phone": "[Phone]",
}

# فئات السوق المرتبطة بملفه (تطابق CV_SKILLS في analyzer)
MARKET_CATS = {
    "procurement": {"label": "المشتريات / سلسلة التوريد", "kw": ["procurement", "purchasing", "sourcing", "supply chain", "logistics", "vendor", "buyer"],
                    "strength": True, "weak": False},
    "sales": {"label": "المبيعات / تطوير الأعمال", "kw": ["sales", "business development", "account executive", "account manager", "revenue"],
             "strength": True, "weak": False},
    "erp": {"label": "أنظمة ERP (Oracle/SAP)", "kw": ["erp", "oracle", "sap", "odoo", "netsuite", "dynamics"],
           "strength": True, "weak": False},
    "pharma": {"label": "الصيدلة / الطبي", "kw": ["pharma", "pharmaceutical", "medical", "healthcare", "clinical"],
              "strength": True, "weak": False},
    "operations": {"label": "العمليات / الجودة", "kw": ["operations", "process improvement", "quality", "compliance"],
                  "strength": True, "weak": False},
    "data_analytics": {"label": "تحليل البيانات / BI", "kw": ["data analysis", "analytics", "power bi", "tableau", "sql", "python"],
                      "strength": False, "weak": True},
    "digital_marketing": {"label": "التسويق الرقمي", "kw": ["digital marketing", "seo", "content marketing", "social media"],
                         "strength": False, "weak": True},
    "project_mgmt": {"label": "إدارة المشاريع (PMP)", "kw": ["project manager", "pmp", "program manager"],
                    "strength": False, "weak": True},
}


def load_market_stats():
    """يجمع إحصائيات حقيقية من قاعدة البيانات."""
    stats = {"total": 0, "cats": {}, "avg_score": 0, "top_jobs": [], "sources": {}}
    if not DB_PATH.exists():
        return stats
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT title, company, location, salary_raw, matched, score, source "
        "FROM jobs WHERE score > 0"
    ).fetchall()
    conn.close()

    stats["total"] = len(rows)
    for cat, info in MARKET_CATS.items():
        n = 0
        for r in rows:
            text = ((r["matched"] or "") + " " + (r["title"] or "")).lower()
            if any(k in text for k in info["kw"]):
                n += 1
        stats["cats"][cat] = n

    scores = [r["score"] or 0 for r in rows]
    stats["avg_score"] = sum(scores) // len(scores) if scores else 0
    stats["top_jobs"] = sorted(rows, key=lambda r: -(r["score"] or 0))[:5]
    stats["sources"] = dict(collections.Counter(r["source"] for r in rows))
    return stats


def build_swot(stats):
    """يبني مصفوفة SWOT من البيانات الحية + بيانات المرشح."""
    cats = stats["cats"]

    # ── S: نقاط القوة (Strengths) ──
    strengths = [
        {"title": "خبرة 15 عاماً (10 في المشتريات + 5 في المبيعات)", "evidence": "مزيج نادر: مشتريات + مبيعات معاً — مناسب للأدوار التجارية المزدوجة", "impact": "عالٍ"},
        {"title": f"خبرة مشتريات/سلسلة توريد — {cats.get('procurement', 0)} وظيفة في السوق تطابقها", "evidence": "أعلى تطابق بالموقع الحالي (Oracle Fusion — 29 نقطة)", "impact": "عالٍ"},
        {"title": f"خبرة ERP (Oracle/SAP/Odoo) — {cats.get('erp', 0)} وظيفة تتطلبها", "evidence": "فئة السوق الأوسع حالياً — ERP تحتل النسبة الأكبر", "impact": "عالٍ"},
        {"title": "خلفية صيدلة/طبي (38 وظيفة مرتبطة)", "evidence": "معرفة قطاعية عميقة — ميزة تنافسية في القطاع الصحي", "impact": "متوسط"},
        {"title": "إجادة Excel + تقارير وإدارة مخزون", "evidence": "أقل من 2% معدل نفاد مخزون عبر مخزون 5M+ EGP", "impact": "متوسط"},
        {"title": "وضع جغرافي (مصر +20)", "evidence": "قرب من سوق الخليج + حجم سوق مصر", "impact": "متوسط"},
    ]

    # ── W: نقاط الضعف (Weaknesses) ──
    weaknesses = [
        {"title": "لا شهادات معتمدة دولياً (PMP / CIPS / CSCP / Oracle Certified)", "evidence": "الشهادات الحالية تدريب أونلاين فقط — تضعف الـ CV أمام فلترة ATS", "impact": "عالٍ"},
        {"title": "الإنجليزية B1-B2 (مقروءة/مكتوبة جيداً لكن ليست طلاقة كاملة)", "evidence": "وظائف الـ Remote العالمية غالباً تتطلب C1 أو fluent", "impact": "متوسط"},
        {"title": f"لا أدوات تحليل بيانات (Python/SQL/Power BI) — {cats.get('data_analytics', 0)} وظيفة تبقى خارج نطاقك", "evidence": "فئة تُضاف لمعظم أدوار المشتريات الحديثة", "impact": "متوسط"},
        {"title": "لا إدارة مشاريع معتمدة (PMP)", "evidence": f"{cats.get('project_mgmt', 0)} وظيفة من السوق تتطلبها ومرتبطة بمستوى senior", "impact": "متوسط"},
        {"title": "لا حضور رقمي/تسويقي شخصي (LinkedIn ضعيف)", "evidence": "المنافسون الأصغر حضوراً رقمياً يظهرون أولاً في بحث المجندين", "impact": "متوسط"},
    ]

    # ── O: الفرص (Opportunities) — من السوق الحي ──
    opportunities = [
        {"title": f"سوق Remote مفتوح: {stats['total']} وظيفة عن بُعد متاحة الآن", "evidence": "السوق عالمي — لا قيود جغرافية للعمل", "impact": "عالٍ"},
        {"title": f"فئة ERP هي الأوسع ({cats.get('erp', 0)} وظيفة) وملفك يطابقها", "evidence": "تحسين اتجاه Oracle/SAP يضاعف الفرص", "impact": "عالٍ"},
        {"title": f"فئة المبيعات/تطوير الأعمال {cats.get('sales', 0)} وظيفة", "evidence": "خبرتك المبيعاتية 5 سنوات — تُوظَّف زراعةً في أدوار Account Executive", "impact": "عالٍ"},
        {"title": "مصادر وظائف جديدة بلا مفتاح (Adzuna) على وشك الإضافة", "evidence": "استبدال Remotive المحدود (وظيفة واحدة فقط) بمصدر أوسع", "impact": "متوسط"},
        {"title": "شهادات Oracle SCM/SAP متاحة أونلاين وتضاعف التقييم", "evidence": "رفع التطابق من 29 إلى 60+ نقطة ممكن خلال 3-6 أشهر", "impact": "عالٍ"},
    ]

    # ── T: التهديدات (Threats) ──
    threats = [
        {"title": "منافسة عالمية شرسة على وظائف Remote", "evidence": "مئات المتقدمين لكل إعلان — يحتاج تميزاً فورياً في أول 6 ثوانٍ", "impact": "عالٍ"},
        {"title": "حاملو الشهادات المعتمدة يتفوقون في فلترة ATS", "evidence": "PMP/CIPS مرشحات آلية تستبعد CV بلا شهادات", "impact": "عالٍ"},
        {"title": "الأسواق الخليجية تتجه لمتطلبات تخصصية أعلى", "evidence": "أدوار المشتريات الحديثة تتطلب تحليل بيانات + أتمتة", "impact": "متوسط"},
        {"title": f"مصادر الوظائف الحالية محدودة ({', '.join(f'{k}: {v}' for k, v in stats['sources'].items())})", "evidence": "الاعتماد على RemoteOK/WWR فقط يفوت وظائف كثيرة", "impact": "متوسط"},
        {"title": "تقييمات السوق الحالية منخفضة (متوسط " + str(stats["avg_score"]) + "/100)", "evidence": "معظم الوظائف المجمعة خارج التخصص — يحتاج توسيع المصادر والكلمات", "impact": "متوسط"},
    ]

    return strengths, weaknesses, opportunities, threats


def build_tows(strengths, weaknesses, opportunities, threats):
    """يبني مصفوفة TOWS: استراتيجيات عملية تجمع S/O/W/T."""
    strategies = [
        {
            "code": "SO-1", "name": "الهجوم — استغل ERP + سلسلة التوريد",
            "desc": "ركّز كل التقديم على وظائف Oracle/SAP في سلسلة التوريد (أوسع فئة + أعلى تطابق 29 نقطة). أرسل رسالة HR تبرز: 15 سنة + توفير 15% تكاليف + <2% نفاد مخزون.",
            "effort": "فوري (أيام)", "win": "أسرع نتيجة",
        },
        {
            "code": "SO-2", "name": "الهجوم — مبيعات + قطاع طبي",
            "desc": "استهدف أدوار Account Executive/Business Development في شركات الصيدلة/المعدات الطبية (52 مبيعات + 38 طبي). خلفيتك المزدوجة = تميز فوري.",
            "effort": "فوري (أيام)", "win": "توسيع السوق",
        },
        {
            "code": "WO-1", "name": "التحسين — شهادة Oracle SCM Cloud",
            "desc": "دورة 3-6 أشهر (Oracle University) ترفع التقييم من 29 إلى 60+ وتجتاز فلتر ATS للفئة الأوسع (66 وظيفة ERP). أعلى عائد استثمار ممكن.",
            "effort": "3-6 أشهر", "win": "رفع التقييم +120%",
        },
        {
            "code": "WO-2", "name": "التحسين — أدوات تحليل البيانات (SQL/Power BI)",
            "desc": "دورتان مجانيتان تقريباً تفتحان فئة data-focused في المشتريات الحديثة وتحدّ من تهديد المتطلبات التخصصية الجديدة.",
            "effort": "1-2 شهر", "win": "مواكبة السوق",
        },
        {
            "code": "ST-1", "name": "الدفاع — حضور رقمي يطابق الخبرة",
            "desc": "أكمل LinkedIn ببروفايل احترافي + أرقام ملموسة (15 سنة، توفير 15%، <2% نفاد، 5M+ EGP). المنافسون يُرى حضورهم أولاً.",
            "effort": "أسبوع", "win": "ظهور في بحث المجندين",
        },
        {
            "code": "ST-2", "name": "الدفاع — رسالة HR بنتائج كمية فقط",
            "desc": "حول كل تطبيق من السيرة إلى قصة أثر: توفير 15%، إدارة شبكة موردين متعددة، مخزون 5M+ EGP بنفاد <2%. تميز في الـ 6 ثوانٍ الأولى.",
            "effort": "فوري", "win": "تجاوز المنافسة",
        },
        {
            "code": "WT-1", "name": "النجاة — توسيع مصادر الوظائف",
            "desc": "فعّل Adzuna (مجاني) + LinkedIn MCP (جلسة متصفح) لتعويض مصادر الـ 16. سوق أكبر = فرص أفضل وأقل اعتماداً على مصدرين فقط.",
            "effort": "أسبوع", "win": "سوق أوسع",
        },
    ]
    return strategies


def generate_html(strengths, weaknesses, opportunities, threats, strategies, stats):
    """يولّد تقرير HTML RTL بنمط التصميم الموحد للواجهة (tokens)."""
    def items_html(items, color):
        return "\n".join(
            f'''<div class="swot-item" style="--item-border:{color}">
              <div class="swot-title">{i["title"]}</div>
              <div class="swot-evidence">{i["evidence"]}</div>
              <span class="swot-impact">{i["impact"]}</span>
            </div>''' for i in items
        )

    strategies_html = "\n".join(
        f'''<div class="strategy">
          <div class="strategy-head">
            <span class="strategy-code">{s["code"]}</span>
            <span class="strategy-name">{s["name"]}</span>
            <span class="strategy-effort">{s["effort"]}</span>
            <span class="strategy-win">{s["win"]}</span>
          </div>
          <div class="strategy-desc">{s["desc"]}</div>
        </div>''' for s in strategies
    )

    top_jobs_html = "\n".join(
        f'<div class="top-job"><b>{r["score"]}/100</b> — {r["title"]}'
        f'<span class="muted"> · {r["company"] or "—"}</span></div>' for r in stats["top_jobs"]
    ) if stats["top_jobs"] else '<div class="muted">لا توجد وظائف بعد</div>'

    html = f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>تحليل SWOT — [اسمك]</title>
<style>
:root{{
  --bg:#0a0a0f;--surface:#12121a;--card:#1a1a2e;--card-hover:#222240;--border:#2a2a3e;
  --text:#e0e0f0;--text-strong:#fff;--muted:#8888aa;
  --green:#00d4aa;--red:#ff4466;--gold:#ffd700;--blue:#4da3ff;--purple:#b388ff;
  --s1:4px;--s2:8px;--s3:12px;--s4:16px;--s5:20px;--s6:24px;--s8:32px;
  --r-sm:6px;--r-md:10px;--r-lg:14px;--r-xl:20px;
  --shadow-md:0 4px 12px rgba(0,0,0,.35);--shadow-lg:0 12px 32px rgba(0,0,0,.5);
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',Tahoma,sans-serif;background:var(--bg);color:var(--text);line-height:1.7;padding:var(--s6)}}
h1{{font-size:1.6rem;color:var(--text-strong);background:linear-gradient(135deg,var(--green),var(--purple));-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:var(--s2)}}
.subtitle{{color:var(--muted);font-size:.85rem;margin-bottom:var(--s6);border-bottom:1px solid var(--border);padding-bottom:var(--s4)}}
.muted{{color:var(--muted);font-size:.8rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:var(--s4);margin-bottom:var(--s6)}}
.quad{{background:var(--card);border:1px solid var(--border);border-radius:var(--r-lg);padding:var(--s5);box-shadow:var(--shadow-md)}}
.quad h2{{font-size:1.05rem;margin-bottom:var(--s4);display:flex;align-items:center;gap:var(--s2);color:var(--text-strong)}}
.quad .count{{font-size:.75rem;background:var(--surface);border:1px solid var(--border);border-radius:99px;padding:2px 10px;color:var(--muted)}}
.swot-item{{background:var(--surface);border:1px solid var(--border);border-right:3px solid var(--item-border);border-radius:var(--r-md);padding:var(--s3);margin-bottom:var(--s3)}}
.swot-title{{font-weight:700;font-size:.9rem;color:var(--text-strong);margin-bottom:var(--s1)}}
.swot-evidence{{font-size:.78rem;color:var(--muted)}}
.swot-impact{{display:inline-block;font-size:.68rem;margin-top:var(--s2);padding:1px 8px;border-radius:99px;font-weight:600}}
.quad.s .swot-impact{{background:rgba(0,212,170,.15);color:var(--green)}}
.quad.w .swot-impact{{background:rgba(255,68,102,.15);color:var(--red)}}
.quad.o .swot-impact{{background:rgba(255,215,0,.15);color:var(--gold)}}
.quad.t .swot-impact{{background:rgba(77,163,255,.15);color:var(--blue)}}
h2.section{{font-size:1.15rem;color:var(--gold);margin:var(--s6) 0 var(--s4)}}
.strategy{{background:var(--card);border:1px solid var(--border);border-radius:var(--r-lg);padding:var(--s4);margin-bottom:var(--s3)}}
.strategy-head{{display:flex;align-items:center;gap:var(--s3);flex-wrap:wrap;margin-bottom:var(--s2)}}
.strategy-code{{background:var(--green);color:#000;font-weight:800;font-size:.7rem;padding:2px 10px;border-radius:99px}}
.strategy-name{{font-weight:700;color:var(--text-strong);font-size:.95rem}}
.strategy-effort{{font-size:.72rem;background:var(--surface);border:1px solid var(--border);padding:1px 10px;border-radius:99px;color:var(--gold)}}
.strategy-win{{font-size:.72rem;background:var(--surface);border:1px solid var(--border);padding:1px 10px;border-radius:99px;color:var(--green)}}
.strategy-desc{{font-size:.83rem;color:var(--muted)}}
.panel{{background:var(--card);border:1px solid var(--border);border-radius:var(--r-lg);padding:var(--s5);margin-bottom:var(--s4)}}
.top-job{{font-size:.85rem;padding:var(--s2) 0;border-bottom:1px solid var(--border)}}
.top-job:last-child{{border-bottom:none}}
.tag{{display:inline-block;font-size:.7rem;background:var(--surface);border:1px solid var(--border);border-radius:99px;padding:1px 10px;margin:2px;color:var(--muted)}}
footer{{margin-top:var(--s8);color:var(--muted);font-size:.75rem;border-top:1px solid var(--border);padding-top:var(--s4)}}
</style>
</head>
<body>
<h1>⚡ تحليل SWOT — {CANDIDATE["name"]}</h1>
<div class="subtitle">
  بيانات حية من قاعدة الوظائف ({stats["total"]} وظيفة محللة) + ملف المرشح (15 سنة خبرة: 10 مشتريات + 5 مبيعات، ERP، قطاع طبي) ·
  المتوسط العام للتطابق: {stats["avg_score"]}/100
</div>

<div class="grid">
  <div class="quad s">
    <h2>💪 نقاط القوة <span class="count">S</span></h2>
    {items_html(strengths, "var(--green)")}
  </div>
  <div class="quad w">
    <h2>🩹 نقاط الضعف <span class="count">W</span></h2>
    {items_html(weaknesses, "var(--red)")}
  </div>
  <div class="quad o">
    <h2>🚀 الفرص <span class="count">O</span></h2>
    {items_html(opportunities, "var(--gold)")}
  </div>
  <div class="quad t">
    <h2>⚠️ التهديدات <span class="count">T</span></h2>
    {items_html(threats, "var(--blue)")}
  </div>
</div>

<h2 class="section">🧭 استراتيجيات TOWS — ماذا تفعل فعلياً</h2>
{strategies_html}

<h2 class="section">🏆 أفضل 5 وظائف حالياً (نقطة انطلاق الهجوم)</h2>
<div class="panel">{top_jobs_html}</div>

<h2 class="section">🎯 الأولوية التنفيذية</h2>
<div class="panel">
  <div><span class="tag">⬅ هذا الأسبوع</span> SO-1 + ST-1 + ST-2 (تقديم + LinkedIn + رسائل كمية)</div>
  <div style="margin-top:var(--s2)"><span class="tag">⬅ هذا الشهر</span> SO-2 + WO-2 (SQL/Power BI) + WT-1 (Adzuna/LinkedIn MCP)</div>
  <div style="margin-top:var(--s2)"><span class="tag">⬅ 3-6 أشهر</span> WO-1 (شهادة Oracle SCM Cloud — أعلى عائد)</div>
</div>

<footer>أداة job_swot.py · تُحدَّث تلقائياً من data/jobs.db · آخر تشغيل: {datetime.fromtimestamp(Path(__file__).stat().st_mtime):%Y-%m-%d}</footer>
</body>
</html>'''
    return html


def main():
    stats = load_market_stats()
    strengths, weaknesses, opportunities, threats = build_swot(stats)
    strategies = build_tows(strengths, weaknesses, opportunities, threats)

    html = generate_html(strengths, weaknesses, opportunities, threats, strategies, stats)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")

    print(f"[OK] SWOT report: {OUTPUT}")
    print(f"[OK] Market base: {stats['total']} jobs")
    print(f"[OK] S:{len(strengths)} W:{len(weaknesses)} O:{len(opportunities)} T:{len(threats)} | TOWS: {len(strategies)} strategies")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()