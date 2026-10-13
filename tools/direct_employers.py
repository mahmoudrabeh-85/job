#!/usr/bin/env python3
"""
direct_employers.py — وظائف من أصحاب الشركات مباشرة (Direct Employers)
───────────────────────────────────────────────────────────────────────
يسحب الإعلانات الرسمية من أنظمة التوظيف (ATS) العامة التي تستضيفها الشركات
نفسها — بلا مفاتيح. كل وظيفة تذهب apply URL لصفحة الشركة الأصلية.

المنصات المدعومة (مُختبرة حيًا 2026-09-27):
  - Greenhouse boards API        → عشرات الشركات incl. Careem/Jumia (المنطقة)
  - Lever postings API           → Spotify/Palantir/...
  - Ashby posting API            → Supabase/Ramp/Linear/...
  - Arbeitnow job board API      → أوروبا (325/صفحة)
  - JazzHR apply-to-job JSON     → شركات أمريكية متوسطة

الترشيح: محلي بنفس منطق job_aggregator (keywords مشتريات/مبيعات/سلاسل توريد)
الرفع: DATABASE_URL (Supabase/PostgreSQL) — أو SQLite المحلي كبديل.

Usage:
  python -m tools.direct_employers --dry-run          # بدون كتابة DB
  python -m tools.direct_employers --all              # كل المنصات → DB
  python -m tools.direct_employers --source greenhouse --limit 30
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "data"
DB_PATH = DATA_DIR / "jobs.db"

UA = {"User-Agent": "job-hunt-aggregator/2.0 (+https://winner-jobs.vercel.app)"}

# ─── قوائم الشركات (قابلة للتوسيع — كل slug مُختبر أو متوقع بصيغة الرسمية) ──
# Greenhouse: أغلب شركات SaaS/تجارة إلكترونية العالمية + شركات المنطقة
GREENHOUSE_BOARDS = [
    # المنطقة العربية / آسيا (شركات محلية تستضيف على Greenhouse)
    "careem", "jumia",
    # تجارة إلكترونية / توصيل (مشتريات + سلاسل توريد فعلية)
    "instacart", "deliveroo", "flexport", "lyft",
    # تقنية عالمية (أحجام كبيرة — ترشيح محلي يبقي المتوافق فقط)
    "stripe", "airbnb", "databricks", "coinbase", "figma", "cloudflare",
    "pinterest", "reddit", "twilio", "duolingo", "dropbox", "notion",
    "datadog", "elastic", "mongodb", "yugabyte", "singlestore",
    "cockroachlabs", "neo4j", "netlify", "wise",
]

LEVER_COMPANIES = [
    "spotify", "palantir", "brex", "plaid", "nubank", "attentive",
    "nium", "neon", "ebay", "clerk", "hims", "hims-hers", "vercel",
]

ASHBY_COMPANIES = [
    "supabase", "ramp", "linear", "deepl", "watershed", "anyscale",
    "clerk", "delphi",
]

JAZZHR_SUBDOMAINS: list[str] = []  # JazzHR يعيد HTML للجذر — يتطلب قائمة subdomains مؤكدة لكل شركة

ARBEITNOW_PAGES = 3  # كل صفحة ~325 وظيفة

# ─── الترشيح المحلي (نفس روح KEYWORDS في job_aggregator) ─────────────────
KEYWORDS = {
    "procurement": 3, "purchasing": 3, "purchase": 2, "buyer": 2,
    "supply chain": 3, "supply-chain": 3, "logistics": 2, "sourcing": 2,
    "vendor": 1, "supplier": 1, "inventory": 1, "warehouse": 1,
    "distribution": 2, "pharma": 3, "pharmaceutical": 3,
    "operations manager": 2, "media buyer": 3, "media buying": 3,
    "account manager": 2, "business development": 2,
    "category manager": 3, "fleet": 1, "fulfillment": 2, "storekeeper": 1,
}
TITLE_ONLY_KEYWORDS = {
    "sales": 2, "selling": 1, "medical": 2, "healthcare": 1,
    "operations": 1, "marketing": 1, "analyst": 1,
}
EXCLUDE_TITLES = [
    "software engineer", "frontend", "backend", "full-stack", "fullstack",
    "data scientist", "data engineer", "devops", "sre ", "qa engineer",
    "ux designer", "ui designer", "game developer", "intern",
    "machine learning", "security engineer", "platform engineer",
]


def _get_json(url: str, timeout: int = 25) -> dict | list:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "")[:8000]


def score_job(job: dict) -> tuple[int, str]:
    """نفس منطق job_aggregator.score_job — يرشّح المتوافق فقط."""
    title = (job.get("title") or "").lower()
    category = (job.get("category") or "").lower()
    desc = (job.get("description") or "").lower()[:6000]
    hay_title = f"{title} {category}"
    hay_all = f"{hay_title} {desc}"
    score = 0
    matched = []
    for kw, weight in KEYWORDS.items():
        if kw in hay_title:
            score += weight * 3
            matched.append(kw)
        elif kw in hay_all:
            score += weight
            matched.append(kw)
    for kw, weight in TITLE_ONLY_KEYWORDS.items():
        if kw in hay_title:
            score += weight * 2
            matched.append(kw)
    return score, ", ".join(dict.fromkeys(matched))


def is_excluded(job: dict) -> bool:
    title = (job.get("title") or "").lower()
    return any(bad in title for bad in EXCLUDE_TITLES)


# ─── Fetchers: كل دالة ترجع قائمة بالشكل الداخلي الموحد ──────────────────
def fetch_greenhouse() -> list[dict]:
    jobs: list[dict] = []
    for board in GREENHOUSE_BOARDS:
        try:
            data = _get_json(
                f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=false"
            )
        except Exception as e:
            print(f"[!] greenhouse/{board}: {str(e)[:60]}", file=sys.stderr)
            continue
        company = board.replace("-", " ").title()
        for j in data.get("jobs", []):
            loc = ((j.get("location") or {}).get("name") or "").strip()
            published = (j.get("first_published") or j.get("updated_at") or "")[:10]
            jobs.append({
                "id": f"gh-{j.get('id')}",
                "title": (j.get("title") or "").strip(),
                "company_name": (j.get("company_name") or company).strip(),
                "location": loc or "Remote",
                "salary": "",
                "url": j.get("absolute_url") or "",
                "category": "direct_employer",
                "description": "",  # content=false — الأداء أهم، التقييم بالعنوان
                "publication_date": published,
                "_source": f"greenhouse:{board}",
            })
        print(f"[i] greenhouse/{board}: {data.get('meta', {}).get('total', 0)} jobs")
    return jobs


def fetch_lever() -> list[dict]:
    jobs: list[dict] = []
    for comp in LEVER_COMPANIES:
        try:
            data = _get_json(f"https://api.lever.co/v0/postings/{comp}?mode=json")
        except Exception as e:
            print(f"[!] lever/{comp}: {str(e)[:60]}", file=sys.stderr)
            continue
        for j in data:
            cats = j.get("categories") or {}
            loc = (cats.get("location") or "").strip()
            created = j.get("createdAt")
            posted = ""
            if created:
                posted = datetime.fromtimestamp(created / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            jobs.append({
                "id": f"lever-{j.get('id')}",
                "title": (j.get("text") or "").strip(),
                "company_name": comp.replace("-", " ").title(),
                "location": loc or (j.get("workplaceType") or "Remote").title(),
                "salary": "",
                "url": j.get("hostedUrl") or "",
                "category": (cats.get("department") or "direct_employer").strip(),
                "description": _clean_html(j.get("descriptionPlain") or j.get("description") or ""),
                "publication_date": posted,
                "_source": f"lever:{comp}",
            })
        print(f"[i] lever/{comp}: {len(data)} jobs")
    return jobs


def fetch_ashby() -> list[dict]:
    jobs: list[dict] = []
    for comp in ASHBY_COMPANIES:
        try:
            data = _get_json(f"https://api.ashbyhq.com/posting-api/job-board/{comp}")
        except Exception as e:
            print(f"[!] ashby/{comp}: {str(e)[:60]}", file=sys.stderr)
            continue
        for j in data.get("jobs", []):
            loc = (j.get("location") or (j.get("address") or {}).get("fullAddress") or "Remote").strip()
            published = (j.get("publishedAt") or j.get("updatedAt") or "")[:10]
            jobs.append({
                "id": f"ashby-{j.get('id')}",
                "title": (j.get("title") or "").strip(),
                "company_name": (j.get("companyName") or comp.title()).strip() or comp.title(),
                "location": loc,
                "salary": "",
                "url": j.get("jobUrl") or f"https://jobs.ashbyhq.com/{comp}",
                "category": (j.get("department") or "direct_employer").strip(),
                "description": _clean_html(j.get("descriptionPlain") or j.get("descriptionHtml") or ""),
                "publication_date": published,
                "_source": f"ashby:{comp}",
            })
        print(f"[i] ashby/{comp}: {len(data.get('jobs', []))} jobs")
    return jobs


def fetch_arbeitnow(pages: int = ARBEITNOW_PAGES) -> list[dict]:
    jobs: list[dict] = []
    for page in range(1, pages + 1):
        try:
            data = _get_json(f"https://www.arbeitnow.com/api/job-board-api?page={page}")
        except Exception as e:
            print(f"[!] arbeitnow p{page}: {str(e)[:60]}", file=sys.stderr)
            break
        items = data.get("data")
        if not isinstance(items, list):
            print(f"[!] arbeitnow p{page}: unexpected payload", file=sys.stderr)
            break
        for j in items:
            remote = bool(j.get("remote"))
            jobs.append({
                "id": f"arbeitnow-{j.get('slug')}",
                "title": (j.get("title") or "").strip(),
                "company_name": (j.get("company_name") or "").strip(),
                "location": "Remote" if remote else (j.get("location") or "Europe").strip(),
                "salary": "",
                "url": j.get("url") or "",
                "category": "direct_employer",
                "description": _clean_html(j.get("description") or ""),
                "publication_date": str(j.get("created_at") or "")[:10],
                "_source": "arbeitnow",
            })
        print(f"[i] arbeitnow p{page}: {len(items)} jobs")
    return jobs


def fetch_jazzhr() -> list[dict]:
    jobs: list[dict] = []
    for sub in JAZZHR_SUBDOMAINS:
        try:
            data = _get_json(f"https://{sub}.applytojob.com/apply/jobs/json/")
        except Exception as e:
            print(f"[!] jazz/{sub}: {str(e)[:60]}", file=sys.stderr)
            continue
        for j in data if isinstance(data, list) else []:
            jobs.append({
                "id": f"jazz-{j.get('id')}",
                "title": (j.get("title") or "").strip(),
                "company_name": (j.get("company") or j.get("hiringOrganization") or sub.title()).strip(),
                "location": (j.get("location") or "United States").strip(),
                "salary": "",
                "url": j.get("url") or "",
                "category": "direct_employer",
                "description": _clean_html(j.get("description") or ""),
                "publication_date": (j.get("created_at") or "")[:10],
                "_source": f"jazz:{sub}",
            })
        print(f"[i] jazz/{sub}: {len(data) if isinstance(data, list) else 0} jobs")
    return jobs


FETCHERS = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
    "arbeitnow": fetch_arbeitnow,
    "jazz": fetch_jazzhr,
}


# ─── Ranking + Store ─────────────────────────────────────────────────────
def rank_and_filter(jobs: list[dict], min_score: int = 2) -> list[dict]:
    kept = []
    for j in jobs:
        if not j.get("title") or is_excluded(j):
            continue
        sc, matched = score_job(j)
        if sc < min_score:
            continue
        j["_score"] = sc
        j["_matched"] = matched
        kept.append(j)
    kept.sort(key=lambda j: -j["_score"])
    return kept


def _connect_db():
    db_url = os.getenv("DATABASE_URL", "")
    if db_url.startswith("postgresql"):
        import psycopg2
        conn = psycopg2.connect(db_url)
        return conn, "pg"
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            company TEXT,
            location TEXT,
            salary_raw TEXT,
            salary_currency TEXT,
            salary_annual REAL,
            url TEXT,
            category TEXT,
            score INTEGER,
            matched TEXT,
            posted DATE,
            fetched_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn, "sqlite"


def upsert_jobs(conn, jobs: list[dict], backend: str) -> int:
    new = 0
    for j in jobs:
        jid = j["id"]
        if jid.find("-") > 0 and not jid.startswith(("gh-", "lever-", "ashby-", "arbeitnow-", "jazz-")):
            jid = f"{j.get('_source', 'direct')}:{j['id']}"
        posted = (j.get("publication_date") or "")[:10] or None
        if backend == "pg":
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO jobs (id, source, title, company, location, salary_raw,
                                  salary_currency, salary_annual, url, category,
                                  score, matched, posted)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title, url = EXCLUDED.url,
                    matched = EXCLUDED.matched, score = EXCLUDED.score,
                    posted = EXCLUDED.posted, fetched_at = NOW()
                """,
                (jid, j.get("_source"), j.get("title"), j.get("company_name"),
                 j.get("location"), j.get("salary") or None, None, None,
                 j.get("url"), j.get("category"), j.get("_score"),
                 j.get("_matched"), posted),
            )
            new += cur.rowcount if cur.rowcount > 0 else 0
        else:
            conn.execute(
                """
                INSERT OR REPLACE INTO jobs
                (id, source, title, company, location, salary_raw, salary_currency,
                 salary_annual, url, category, score, matched, posted)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (jid, j.get("_source"), j.get("title"), j.get("company_name"),
                 j.get("location"), j.get("salary") or None, None, None,
                 j.get("url"), j.get("category"), j.get("_score"),
                 j.get("_matched"), posted),
            )
            new += 1
    conn.commit()
    return new


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description="Direct Employers Aggregator")
    ap.add_argument("--source", choices=[*FETCHERS, "all"], default="all")
    ap.add_argument("--min-score", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    sources = FETCHERS if args.source == "all" else {args.source: FETCHERS[args.source]}
    all_jobs: list[dict] = []
    for name, fn in sources.items():
        try:
            all_jobs.extend(fn())
        except Exception as e:
            print(f"[!] {name} failed: {e}", file=sys.stderr)

    print(f"\n[i] fetched raw: {len(all_jobs)}")
    kept = rank_and_filter(all_jobs, args.min_score)
    print(f"[i] after ranking (score >= {args.min_score}): {len(kept)}")
    if not kept:
        return 1

    if args.dry_run:
        for j in kept[:25]:
            print(f"  [{j['_score']:3d}] {j['title'][:55]} @ {j['company_name'][:25]} ({j['_source']})")
        return 0

    conn, backend = _connect_db()
    added = upsert_jobs(conn, kept, backend)
    conn.close()
    print(f"[i] DB ({backend}): {added} rows upserted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
