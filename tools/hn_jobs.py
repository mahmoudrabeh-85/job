#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hn_jobs.py — جلب وظائف Ask HN: Who is hiring? (Hacker News, API عام بلا مفتاح)
─────────────────────────────────────────────────────────────
المصدر: HN Algolia API (عام ومجاني). تعليق واحد ≈ إعلان واحد
بصيغة «الشركة | الوظيفة | الموقع | الراتب». يحفظ في data/jobs.db
بنفس شكل جدول الوظائف (14 عمودًا) ليتوافق مع باقي الأدوات.

الاستخدام:
  python tools/hn_jobs.py --hits 120 --min-score 2
  python tools/hn_jobs.py --hits 60 --dry-run     # عرض فقط بلا حفظ

بنية stdlib فقط (urllib + sqlite3) — يعمل على أي جهاز بلا تثبيت.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sqlite3
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "data" / "jobs.db"
HN_API = "https://hn.algolia.com/api/v1"
UA = {"User-Agent": "job-hunt-monitor/1.0"}

# تصنيف الأقسام الستة (EN + AR) — نفس taxonomy المشروع.
DEPT_KEYWORDS = {
    "procurement": ["procurement", "purchasing", "sourcing", "buyer", "vendor",
                    "negotiation", "contract", "rfq", "tender", "مشتريات", "توريد", "تفاوض"],
    "supply_chain": ["supply chain", "logistics", "inventory", "warehouse",
                     "distribution", "stock", "supplier", "التوريد", "لوجستيات",
                     "مخازن", "مخزون", "توزيع", "شحن"],
    "sales": ["sales", "business development", "account executive", "revenue",
              "client", "customer", "مبيعات", "تطوير أعمال", "عملاء"],
    "pharma": ["pharmaceutical", "pharma", "drug", "medicine", "healthcare",
               "medical", "clinical", "gdp", "صيدلة", "أدوية", "طبي"],
    "management": ["manager", "leadership", "director", "supervision",
                   "management", "مدير", "إدارة", "قيادة"],
    "operations": ["operations", "process", "quality", "compliance", "audit",
                   "analyst", "excel", "تشغيل", "عمليات", "جودة"],
}


def _get_json(url: str):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _strip_html(text: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or ""))).strip()


def _salary_field(text: str) -> str:
    """يستخرج الراتب من نص التعليق بصيغة سنوية (‎$120-180k → 120000-180000 yearly)."""
    num = (r"(?:\$|€|£|USD\s?)\s?\d{1,3}(?:,\d{3})+(?:\.\d+)?\s?[kK]?|"
           r"\$?\s?\d{2,3}(?:\.\d+)?\s?[kK]\b|\$\s?\d{2,3}(?:\.\d+)?\b|\d{2,3}\b")
    m = re.search(f"({num})\\s*(?:[-–—]|to)\\s*({num})", text)
    if m and ("$" in m.group(0) or "k" in m.group(0).lower()):
        def norm(tok):
            t = tok.replace("$", "").replace("€", "").replace("£", "").replace("USD", "").replace(" ", "")
            if t.lower().endswith("k"):
                t = t[:-1] + "000"
            t = t.replace(",", "").split(".")[0]
            if len(t) <= 3 and t.isdigit():
                t += "000"
            return t
        lo, hi = norm(m.group(1)), norm(m.group(2))
        if lo.isdigit() and hi.isdigit() and int(hi) <= 2_000_000:
            return f"{lo}-{hi} yearly"
    m = re.search(r"\$\s?(\d{2,3})\s?[kK]\b", text)
    if m:
        return f"{m.group(1)}000 yearly"
    return ""


def fetch_hn_whoishiring(hits: int = 120) -> list:
    """آخر خيط Ask HN: Who is hiring? — الردود غير الإعلانية تُستبعد تلقائيًا."""
    q = urllib.parse.quote('"Ask HN: Who is hiring?"')
    story = _get_json(f"{HN_API}/search_by_date?tags=story&query={q}&hitsPerPage=1")["hits"][0]
    sid = story["objectID"]
    comments = _get_json(
        f"{HN_API}/search_by_date?tags=comment,story_{sid}&hitsPerPage={hits}").get("hits", [])
    jobs = []
    for c in comments:
        text = _strip_html(c.get("comment_text") or "")
        if len(text) < 40:
            continue
        first_line = text.split(". ")[0][:200]
        parts = [p.strip() for p in first_line.split("|") if p.strip()]
        if len(parts) < 2 or len(parts[0]) > 60 or len(parts[1]) < 3:
            continue
        company, role = parts[0], parts[1][:120]
        loc = "Remote (HN)" if re.search(r"\bremote\b", text, re.I) else "HN"
        jobs.append({
            "id": "hn-%s" % c.get("objectID"),
            "title": role,
            "company": company,
            "location": loc,
            "salary_raw": _salary_field(text),
            "url": "https://news.ycombinator.com/item?id=%s" % c.get("objectID"),
            "text": text[:2500],
            "posted": (c.get("created_at") or "")[:10],
        })
    return jobs


def classify(title: str, text: str):
    """تصنيف القسم + نقاط من الكلمات المفتاحية (نفس الأقسام الستة)."""
    hay = ("%s %s" % (title, text)).casefold()
    best, best_n, matched = "operations", 0, []
    for dept, kws in DEPT_KEYWORDS.items():
        hits = [k for k in kws if k in hay]
        if len(hits) > best_n:
            best, best_n, matched = dept, len(hits), hits
    score = min(10 + best_n * 8, 95) if best_n else 5
    return best, score, ",".join(matched[:8])


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch HN Who-is-hiring jobs into data/jobs.db")
    ap.add_argument("--hits", type=int, default=120)
    ap.add_argument("--min-score", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    jobs = fetch_hn_whoishiring(hits=args.hits)
    print("[i] hn: fetched %d comments-as-jobs" % len(jobs))
    if args.dry_run:
        for j in jobs[:10]:
            print("  - %s @ %s" % (j["title"][:60], j["company"][:40]))
        return 0
    # fix column order: (id, source, title, company, location, salary_raw,
    # url, category, score, matched, posted, fetched_at)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY,
        source TEXT, title TEXT, company TEXT, location TEXT, salary_raw TEXT,
        salary_currency TEXT, salary_annual NUMERIC, url TEXT, category TEXT,
        score INTEGER DEFAULT 0, matched TEXT, posted TEXT,
        fetched_at TEXT DEFAULT (datetime('now')))""")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    new = 0
    for j in jobs:
        cat, score, matched = classify(j["title"], j["text"])
        if score < args.min_score:
            continue
        conn.execute("""INSERT OR REPLACE INTO jobs (id, source, title,
            company, location, salary_raw, url, category, score, matched,
            posted, fetched_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (j["id"], "hn", j["title"], j["company"], j["location"],
             j["salary_raw"], j["url"], cat, score, matched,
             j["posted"] or None, now))
        new += 1
    conn.commit()
    conn.close()
    print("[i] hn: upserted %d jobs into %s" % (new, DB_PATH))
    return 0


if __name__ == "__main__":
    sys.exit(main())
