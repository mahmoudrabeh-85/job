#!/usr/bin/env python3
"""
auto_apply.py — مساعد تعبئة بشري آمن (OPT-IN, وظيفة واحدة فقط)
─────────────────────────────────────────────────────────────
هذا ليس بوت تقديم جماعي. القواعد الصارمة:
1. يعمل على وظيفة واحدة يحددها المستخدم صراحة (--job-id).
2. لا يحفظ أي كلمات سر إطلاقاً — يستخدم جلسة متصفحك المسجلة فقط.
3. لا يضغط زر الإرسال النهائي أبداً — أنت تراجع وتضغط بنفسك.
4. أي موقع يمنع الأتمتة في شروطه يُستخدم معه وضع الفتح-فقط.

الاستخدام:
  python tools/auto_apply.py --job-id "<id>"            # فتح صفحة التقديم + نسخ الرسالة للحافظة
  python tools/auto_apply.py --job-id "<id>" --mark     # نفس السابق + تسجيل قدمت بعد تأكيدك

يتطلب: pip install playwright && playwright install chromium
"""
import argparse
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "data" / "jobs.db"


def get_job(job_id: str) -> dict | None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", [job_id]).fetchone()
    conn.close()
    return dict(row) if row else None


def mark_applied(job_id: str):
    import urllib.request, json
    body = json.dumps({"job_id": job_id, "title": "", "company": "", "url": ""}).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:8767/api/v1/applications", data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            print("[i] tracker:", r.read().decode()[:120])
    except Exception as e:
        print(f"[!] tracker unreachable (is the server on 8767 running?): {e}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Safe single-job apply assistant (no auto-submit)")
    ap.add_argument("--job-id", required=True, help="Job id from jobs.db")
    ap.add_argument("--mark", action="store_true", help="Record as applied after YOUR manual submit")
    args = ap.parse_args()

    job = get_job(args.job_id)
    if not job:
        print(f"[!] job not found: {args.job_id}")
        return 1

    print(f"\n[+] {job.get('title')}")
    print(f"    {job.get('company')} | {job.get('url')}")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[!] playwright not installed: pip install playwright && playwright install chromium")
        print(f"[!] open manually instead: {job.get('url')}")
        return 2

    print("[i] opening apply page in YOUR logged-in browser profile...")
    print("[i] I will NEVER press submit — review and submit yourself, then close the browser.")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            str(BASE / "data" / "browser_profile"), headless=False)
        page = browser.new_page()
        page.goto(job.get("url") or "about:blank")
        print("[i] browser open — complete the application yourself, then close it.")
        try:
            page.wait_for_event("close", timeout=600000)
        except Exception:
            pass
        browser.close()

    if args.mark:
        confirm = input("Did YOU submit the application? type YES to record: ").strip()
        if confirm == "YES":
            mark_applied(args.job_id)
        else:
            print("[i] not recorded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
