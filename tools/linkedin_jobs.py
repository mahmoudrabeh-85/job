#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""linkedin_jobs.py — جلب وظائف LinkedIn عبر واجهة الضيف العامة (بلا تسجيل)
─────────────────────────────────────────────────────────────
يستخدم LinkedIn Guest Jobs API (نفس ما يعرضه المتصفح للزوار) —
~10 بطاقات لكل طلب، حجم منخفض. قد يتغير شكل الصفحة في أي وقت
(إن فشل الجلب بطريقة غريبة فالسبب غالبًا تغيير LinkedIn نفسه).

ملاحظة: التزم باستخدام شخصي معقول + شروط LinkedIn. لا مفاتيح ولا جلسات.

الاستخدام:
  python tools/linkedin_jobs.py --query "procurement manager" --location "Saudi Arabia"
  python tools/linkedin_jobs.py --query "sales" --remote --pages 3
  python tools/linkedin_jobs.py --query "pharmacist" --country ae --dry-run

بنية stdlib فقط (urllib + sqlite3) + مصنف hn_jobs للأقسام والحفظ.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "tools"))
from hn_jobs import classify, DB_PATH  # noqa: E402  (تصنيف الأقسام الستة + مسار DB)

_LI_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
}

GULF_LOC = {
    "sa": ("saudi", "riyadh", "jeddah", "dammam", "khobar", "ksa"),
    "ae": ("united arab", "dubai", "abu dhabi", "sharjah", "uae"),
    "qa": ("qatar", "doha"),
    "kw": ("kuwait",),
}


def _strip_tags(s: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip())


def fetch_linkedin(keywords: str, location: str | None = None,
                   remote: bool = False, source_tag: str = "linkedin",
                   start: int = 0) -> list:
    """صفحة ضيف واحدة (~10 بطاقات). source_tag مثل linkedin:sa أو linkedin:remote."""
    params = {"keywords": keywords, "start": start}
    if location:
        params["location"] = location
    if remote:
        params["f_WT"] = "2"
    url = ("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?"
           + urllib.parse.urlencode(params))
    req = urllib.request.Request(url, headers=_LI_HEADERS)
    with urllib.request.urlopen(req, timeout=25) as resp:
        page = resp.read().decode("utf-8", errors="replace")
    jobs = []
    for card in re.findall(r"<div class=\"base-card[^>]*>.*?</div>\s*</div>", page, re.S):
        link_m = re.search(r'href="(https://[^"]*?/jobs/view/[^"]+)"', card)
        title_m = re.search(r'base-search-card__title[^>]*>([^<]+)<', card)
        if not (link_m and title_m):
            continue
        comp_m = re.search(r'base-search-card__subtitle[^>]*>\s*<a[^>]*>([^<]+)</a>', card)
        loc_m = re.search(r'job-search-card__location[^>]*>([^<]+)<', card)
        date_m = re.search(r'datetime="(\d{4}-\d{2}-\d{2})"', card)
        jid_m = re.search(r"/jobs/view/[^/?]*?(\d{6,})", link_m.group(1))
        jobs.append({
            "id": "li-%s" % (jid_m.group(1) if jid_m else abs(hash(link_m.group(1)))),
            "title": _strip_tags(title_m.group(1)),
            "company": _strip_tags(comp_m.group(1)) if comp_m else "",
            "location": _strip_tags(loc_m.group(1)) if loc_m else "",
            "salary_raw": "",
            "url": link_m.group(1).split("?")[0],
            "text": _strip_tags(title_m.group(1)),
            "posted": date_m.group(1) if date_m else "",
            "_source": source_tag,
        })
    return jobs


def run(query: str, locations: list, remote: bool, pages: int,
        min_score: int, dry_run: bool) -> int:
    import sqlite3
    from datetime import datetime, timezone

    all_jobs = []
    if remote or not locations:
        for p in range(pages):
            all_jobs += fetch_linkedin(query, remote=True,
                                       source_tag="linkedin:remote", start=p * 10)
    for loc in locations:
        for p in range(pages):
            all_jobs += fetch_linkedin(query, location=loc,
                                       source_tag="linkedin:" + loc, start=p * 10)
    print("[i] linkedin: fetched %d cards" % len(all_jobs))
    if dry_run:
        for j in all_jobs[:10]:
            print("  - %s @ %s (%s)" % (j["title"][:55], j["company"][:35], j["location"][:30]))
        return 0
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY,
        source TEXT, title TEXT, company TEXT, location TEXT, salary_raw TEXT,
        salary_currency TEXT, salary_annual NUMERIC, url TEXT, category TEXT,
        score INTEGER DEFAULT 0, matched TEXT, posted TEXT,
        fetched_at TEXT DEFAULT (datetime('now')))""")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    new = 0
    for j in all_jobs:
        if not j["title"]:
            continue
        cat, score, matched = classify(j["title"], j["title"])
        if score < min_score:
            continue
        conn.execute("""INSERT OR REPLACE INTO jobs (id, source, title,
            company, location, salary_raw, url, category, score, matched,
            posted, fetched_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (j["id"], j["_source"], j["title"], j["company"], j["location"],
             "", j["url"], cat, score, matched, j["posted"] or None, now))
        new += 1
    conn.commit()
    conn.close()
    print("[i] linkedin: upserted %d jobs into %s" % (new, DB_PATH))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch LinkedIn guest jobs into data/jobs.db")
    ap.add_argument("--query", required=True, help="مثال: procurement manager")
    ap.add_argument("--location", action="append", default=[],
                    help="يُكرر لكل دولة: --location 'Saudi Arabia' --location 'United Arab Emirates'")
    ap.add_argument("--remote", action="store_true", help="وظائف عن بُعد أيضًا")
    ap.add_argument("--pages", type=int, default=2, help="صفحات لكل بحث (~10/صفحة)")
    ap.add_argument("--min-score", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    return run(args.query, args.location, args.remote, max(1, args.pages),
               args.min_score, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
