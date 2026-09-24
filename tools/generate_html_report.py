#!/usr/bin/env python3
"""Generate an HTML report (clickable) with ALL jobs from jobs.db — RTL, Arabic-friendly."""
import sqlite3
import sys
from datetime import date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "data" / "jobs.db"
OUT = BASE / "data" / f"all_jobs_{date.today().isoformat()}.html"

conn = sqlite3.connect(DB)
rows = conn.execute("""
    SELECT title, company, location, salary_raw, salary_currency, salary_annual,
           url, score, matched, posted, source
    FROM jobs WHERE score > 0
    ORDER BY score DESC, salary_annual IS NULL, salary_annual DESC
""").fetchall()

SRC_LABEL = {"remoteok": "RemoteOK", "weworkremotely": "WeWorkRemotely", "remotive": "Remotive"}

cards = []
for i, (t, c, loc, sraw, scur, sann, url, score, matched, posted, src) in enumerate(rows, 1):
    sal = ""
    if sraw:
        sal = f"<span class='sal'>{sraw[:60]}</span>"
    elif sann:
        sal = f"<span class='sal'>{scur.upper()} ${sann:,.0f}/yr</span>"
    else:
        sal = "<span class='sal muted'>غير مذكور</span>"
    cards.append(f"""
    <a class="card" href="{url}" target="_blank" rel="noopener">
      <div class="rank">{i}</div>
      <div class="body">
        <div class="title">{t}</div>
        <div class="meta">{c or '?'} · {loc or 'Remote'} · {SRC_LABEL.get(src, src)} · {posted or '?'}</div>
        <div class="bottom">{sal} <span class="score">نقاط {score}</span></div>
        <div class="matched">{matched}</div>
      </div>
    </a>""")

html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>تقرير الوظائف — {len(rows)} وظيفة ({date.today().isoformat()})</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #0f1222; color: #e6e9f5; padding: 24px; }}
  h1 {{ font-size: 22px; margin-bottom: 4px; color: #ffd166; }}
  .sub {{ color: #8fa0c8; margin-bottom: 20px; font-size: 13px; }}
  .grid {{ display: grid; gap: 10px; }}
  .card {{ display: flex; gap: 12px; background: #171b33; border: 1px solid #262c4d; border-radius: 10px;
          padding: 12px 14px; text-decoration: none; color: inherit; transition: border-color .15s, transform .15s; }}
  .card:hover {{ border-color: #ffd166; transform: translateY(-1px); }}
  .rank {{ font-size: 17px; font-weight: 700; color: #ffd166; min-width: 34px; text-align: center; line-height: 1.8; }}
  .body {{ flex: 1; min-width: 0; }}
  .title {{ font-size: 15px; font-weight: 600; color: #fff; }}
  .meta {{ font-size: 12px; color: #8fa0c8; margin: 3px 0 6px; }}
  .bottom {{ display: flex; justify-content: space-between; align-items: center; gap: 8px; }}
  .sal {{ font-size: 12.5px; color: #7ee0a3; }}
  .sal.muted {{ color: #6b789e; }}
  .score {{ background: #2a3160; color: #ffd166; border-radius: 20px; padding: 2px 10px; font-size: 12px; font-weight: 600; }}
  .matched {{ font-size: 11px; color: #aab6d8; margin-top: 5px; }}
  .stats {{ display: flex; gap: 14px; margin: 14px 0 20px; flex-wrap: wrap; }}
  .stat {{ background: #171b33; border: 1px solid #262c4d; border-radius: 8px; padding: 8px 14px; font-size: 12.5px; }}
  .stat b {{ color: #ffd166; }}
</style>
</head>
<body>
  <h1>تقرير الوظائف — كل المطابقات</h1>
  <div class="sub">تم الجلب من 3 مصادر مجانية بلا مفتاح · أُعد {date.today().isoformat()} · اضغط أي بطاقة لفتح الوظيفة</div>
  <div class="stats">
    <div class="stat">📌 <b>{len(rows)}</b> وظيفة مطابقة</div>
    <div class="stat">🔗 كلها Remote</div>
    <div class="stat">💰 راتب ≥ $12k/سنة (≈ 30k ج.م/شهر)</div>
  </div>
  <div class="grid">{''.join(cards)}</div>
</body>
</html>"""

OUT.write_text(html, encoding="utf-8")
print(f"HTML written: {OUT} ({len(html)} bytes, {len(rows)} jobs)")
conn.close()