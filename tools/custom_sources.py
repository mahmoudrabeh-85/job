#!/usr/bin/env python3
"""
custom_sources.py — إدارة مواقع التوظيف المخصصة في job-hunt
- إضافة/حذف مواقع جديدة
- إعادة البحث في مواقع مخصصة
- اقتراح مواقع غير مدرجة
"""
import json
import re
import sqlite3
import sys
import urllib.request
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "data"
SOURCES_FILE = DATA_DIR / "custom_sources.json"
DB_PATH = DATA_DIR / "jobs.db"

# ─── المصادر المخصصة (قابلة للتعديل) ──────────────────────────────────
DEFAULT_SOURCES = [
    {
        "id": "linkedin",
        "name": "LinkedIn",
        "type": "scraping",
        "url": "https://www.linkedin.com/jobs/search/?keywords={query}&location=Remote",
        "enabled": False,
        "requires_login": True,
        "description": "أكبر منصة توظيف — يحتاج تسجيل دخول",
        "icon": "💼"
    },
    {
        "id": "bayt",
        "name": "Bayt.com",
        "type": "scraping",
        "url": "https://www.bayt.com/en/remote-jobs/",
        "enabled": False,
        "requires_login": False,
        "description": "الوظائف عن بُعد — خليجي + عربي",
        "icon": "🏗️"
    },
    {
        "id": "wuzzuf",
        "name": "Wuzzuf",
        "type": "scraping",
        "url": "https://wuzzuf.net/jobs/q/{query}",
        "enabled": False,
        "requires_login": False,
        "description": "سوق العمل المصري — وظائف محلية",
        "icon": "🇪🇬"
    },
    {
        "id": "glasdoor",
        "name": "Glassdoor",
        "type": "api",
        "url": "https://www.glassdoor.com/Job/remote-jobs-SRCH_IL.0,6_IS11047_KO7,19.htm",
        "enabled": False,
        "requires_login": False,
        "description": "رواتب + تقييمات الشركات",
        "icon": "🏢"
    },
    {
        "id": "adzuna",
        "name": "Adzuna",
        "type": "api",
        "url": "https://www.adzuna.com/search?q={query}&loc=0&loc=0&w=Remote",
        "enabled": False,
        "requires_login": False,
        "description": "محرك بحث وظائف — بيانات مفتوحة",
        "icon": "🔍"
    },
    {
        "id": "upwork",
        "name": "Upwork",
        "type": "scraping",
        "url": "https://www.upwork.com/nx/search/jobs/?q={query}&sort=recency",
        "enabled": False,
        "requires_login": True,
        "description": "العمل الحر — مشاريع متعددة",
        "icon": "💻"
    },
    {
        "id": "freelancer",
        "name": "Freelancer",
        "type": "scraping",
        "url": "https://www.freelancer.com/jobs/?keyword={query}",
        "enabled": False,
        "requires_login": False,
        "description": "منصة عمل حر عالمية",
        "icon": "🌐"
    },
    {
        "id": "indeed",
        "name": "Indeed",
        "type": "scraping",
        "url": "https://www.indeed.com/jobs?q={query}&l=Remote",
        "enabled": False,
        "requires_login": False,
        "description": "أكبر محرك بحث وظائف في العالم",
        "icon": "🔎"
    },
    {
        "id": "careerjet",
        "name": "CareerJet",
        "type": "api",
        "url": "https://www.careerjet.com/search/jobs?s={query}&l=Remote&radius=25",
        "enabled": False,
        "requires_login": False,
        "description": "محرك بحث وظائف — يجمع من مواقع متعددة",
        "icon": "📊"
    },
    {
        "id": "remoteok_api",
        "name": "RemoteOK (إضافي)",
        "type": "api",
        "url": "https://remoteok.com/api",
        "enabled": False,
        "requires_login": False,
        "description": "API عام — فلاتر مختلفة",
        "icon": "📡"
    }
]

# ─── اقتراحات مواقع جديدة ──────────────────────────────────────────────
SUGGESTIONS = [
    {
        "name": "FlexJobs",
        "url": "https://www.flexjobs.com",
        "reason": "متخصصة في الوظائف المرنة عن بُعد — موثوقة جداً",
        "category": "remote"
    },
    {
        "name": "We Work Remotely",
        "url": "https://weworkremotely.com",
        "reason": "أقدم منصة وظائف عن بُعد — مجانية بالكامل",
        "category": "remote"
    },
    {
        "name": "Remote.co",
        "url": "https://remote.co",
        "reason": "منصة وظائف عن بُعد + موارد للعمل عن بُعد",
        "category": "remote"
    },
    {
        "name": "Working Nomads",
        "url": "https://www.workingnomads.com",
        "reason": "وظائف للرحلة الرقمية — تصميم/تسويق/تطوير",
        "category": "digital_nomad"
    },
    {
        "name": "Toptal",
        "url": "https://www.toptal.com",
        "reason": "أفضل 3% من_freelancers — رواتب عالية جداً",
        "category": "freelance_premium"
    },
    {
        "name": "AngelList",
        "url": "https://angel.co/jobs",
        "reason": "وظائف الشركات الناشئة — رواتب + أسهم",
        "category": "startup"
    },
    {
        "name": "Glassdoor",
        "url": "https://www.glassdoor.com",
        "reason": "رواتب + تقييمات + وظائف — معلومات شاملة",
        "category": "research"
    },
    {
        "name": "Indeed",
        "url": "https://www.indeed.com",
        "reason": "أكبر محرك بحث وظائف في العالم — ملايين الوظائف",
        "category": "general"
    },
    {
        "name": "ZipRecruiter",
        "url": "https://www.ziprecruiter.com",
        "reason": "منصة وظائف ذكية — يطابق CV مع الوظائف",
        "category": "general"
    },
    {
        "name": "SimplyHired",
        "url": "https://www.simplyhired.com",
        "reason": "محرك بحث وظائف — يجمع من مواقع متعددة",
        "category": "general"
    },
    {
        "name": "Jobspresso",
        "url": "https://jobspresso.co",
        "reason": "وظائف عن بُعد فقط — فلترة جيدة",
        "category": "remote"
    },
    {
        "name": "Himalayas",
        "url": "https://himalayas.app/jobs/worldwide",
        "reason": "منصة وظائف عالمية — واجهة جميلة + شفافية رواتب",
        "category": "remote"
    },
    {
        "name": "RemoteOK",
        "url": "https://remoteok.com",
        "reason": "منصة وظائف عن بُعد — API مجاني",
        "category": "remote"
    },
    {
        "name": "Remotive",
        "url": "https://remotive.com",
        "reason": "وظائف عن بُعد — مجانية مع API",
        "category": "remote"
    },
    {
        "name": "Gun.io",
        "url": "https://gun.io",
        "reason": "منصة للمطورين الأكادرين — رواتب عالية",
        "category": "freelance_premium"
    },
    {
        "name": "Contra",
        "url": "https://contra.com",
        "reason": "منصة عمل حر — بدون عمولات",
        "category": "freelance"
    },
    {
        "name": "Fiverr",
        "url": "https://www.fiverr.com",
        "reason": "منصة خدمات — مبيعات/تسويق/تصميم",
        "category": "freelance"
    },
    {
        "name": "PeoplePerHour",
        "url": "https://www.peopleperhour.com",
        "reason": "منصة عمل حر أوروبية — مشاريع متنوعة",
        "category": "freelance"
    },
]

def load_sources() -> list[dict]:
    """Load custom sources from file"""
    if SOURCES_FILE.exists():
        try:
            return json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return DEFAULT_SOURCES.copy()

def save_sources(sources: list[dict]):
    """Save custom sources to file"""
    DATA_DIR.mkdir(exist_ok=True)
    SOURCES_FILE.write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8")

def add_source(source: dict) -> bool:
    """Add a new custom source"""
    sources = load_sources()
    # Check if already exists
    if any(s["id"] == source["id"] for s in sources):
        return False
    sources.append(source)
    save_sources(sources)
    return True

def remove_source(source_id: str) -> bool:
    """Remove a custom source"""
    sources = load_sources()
    before = len(sources)
    sources = [s for s in sources if s["id"] != source_id]
    if len(sources) < before:
        save_sources(sources)
        return True
    return False

def toggle_source(source_id: str) -> bool:
    """Toggle enabled/disabled for a source"""
    sources = load_sources()
    for s in sources:
        if s["id"] == source_id:
            s["enabled"] = not s.get("enabled", False)
            save_sources(sources)
            return s["enabled"]
    return False

def get_enabled_sources() -> list[dict]:
    """Get only enabled sources"""
    return [s for s in load_sources() if s.get("enabled", False)]

def get_suggestions() -> list[dict]:
    """Get suggested job sites"""
    return SUGGESTIONS

def search_custom_source(source: dict, query: str = "") -> list[dict]:
    """Search a custom source (basic implementation)"""
    url = source.get("url", "").format(query=query or "remote")
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        # Basic job extraction (varies by site)
        return _extract_jobs_from_html(html, source["id"])
    except Exception as e:
        print(f"[!] {source['name']} failed: {e}", file=sys.stderr)
        return []

def _extract_jobs_from_html(html: str, source_id: str) -> list[dict]:
    """Basic job extraction from HTML"""
    jobs = []
    # Simple patterns for common job listing sites
    title_patterns = [
        r'<h2[^>]*class="[^"]*job[^"]*"[^>]*>([^<]+)</h2>',
        r'<a[^>]*class="[^"]*job-title[^"]*"[^>]*>([^<]+)</a>',
        r'<span[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</span>',
    ]
    for pattern in title_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for title in matches[:20]:  # Limit to 20
            title = title.strip()
            if len(title) > 10:  # Skip very short matches
                jobs.append({
                    "title": title,
                    "company_name": source_id,
                    "location": "Remote",
                    "url": "",
                    "description": "",
                    "source": source_id
                })
        if jobs:
            break
    return jobs


# ─── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    
    import argparse
    ap = argparse.ArgumentParser(description="Custom sources manager")
    sub = ap.add_subparsers(dest="cmd")
    
    sub.add_parser("list", help="List all sources")
    sub.add_parser("enabled", help="List enabled sources")
    sub.add_parser("suggest", help="Show suggested sites")
    
    p_add = sub.add_parser("add", help="Add a source")
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--url", required=True)
    p_add.add_argument("--type", default="scraping", choices=["api", "scraping", "rss"])
    
    p_rm = sub.add_parser("remove", help="Remove a source")
    p_rm.add_argument("--id", required=True)
    
    p_toggle = sub.add_parser("toggle", help="Toggle source on/off")
    p_toggle.add_argument("--id", required=True)
    
    p_search = sub.add_parser("search", help="Search a custom source")
    p_search.add_argument("--id", required=True)
    p_search.add_argument("--query", default="remote")
    
    args = ap.parse_args()
    
    if args.cmd == "list":
        sources = load_sources()
        print(f"\n📋 المصادر المخصصة ({len(sources)}):")
        print("-" * 60)
        for s in sources:
            status = "✅" if s.get("enabled") else "❌"
            print(f"  {status} {s['icon']} {s['name']} ({s['type']})")
            print(f"     {s['description']}")
            print()
    
    elif args.cmd == "enabled":
        sources = get_enabled_sources()
        print(f"\n✅ المصادر المفعّلة ({len(sources)}):")
        for s in sources:
            print(f"  {s['icon']} {s['name']}")
    
    elif args.cmd == "suggest":
        suggestions = get_suggestions()
        print(f"\n💡 اقتراحات مواقع توظيف ({len(suggestions)}):")
        print("-" * 60)
        for s in suggestions:
            print(f"  🌐 {s['name']}")
            print(f"     {s['reason']}")
            print(f"     {s['url']}")
            print()
    
    elif args.cmd == "add":
        new_source = {
            "id": args.name.lower().replace(" ", "_"),
            "name": args.name,
            "type": args.type,
            "url": args.url,
            "enabled": True,
            "requires_login": False,
            "description": f"مصدر مخصص — {args.name}",
            "icon": "➕"
        }
        if add_source(new_source):
            print(f"✅ تمت إضافة {args.name}")
        else:
            print(f"⚠️ {args.name} موجود بالفعل")
    
    elif args.cmd == "remove":
        if remove_source(args.id):
            print(f"✅ تمت إزالة {args.id}")
        else:
            print(f"❌ {args.id} غير موجود")
    
    elif args.cmd == "toggle":
        result = toggle_source(args.id)
        if result is not None:
            status = "تفعيل" if result else "تعطيل"
            print(f"✅ {status} {args.id}")
        else:
            print(f"❌ {args.id} غير موجود")
    
    elif args.cmd == "search":
        sources = load_sources()
        source = next((s for s in sources if s["id"] == args.id), None)
        if not source:
            print(f"❌ المصدر {args.id} غير موجود")
            sys.exit(1)
        print(f"🔍 البحث في {source['name']}...")
        jobs = search_custom_source(source, args.query)
        print(f"📊 نتائج: {len(jobs)} وظيفة")
        for j in jobs[:10]:
            print(f"  • {j['title']}")
    
    else:
        ap.print_help()
