"""
routers/refresh.py — Protected admin endpoint to refresh direct-employer jobs
POST /api/v1/admin/refresh-direct?source=greenhouse&token=...

Runs tools/direct_employers.py fetchers inside the serverless function (which
has the real DATABASE_URL) and upserts into the jobs table.

Protection:
  - Disabled unless env ADMIN_REFRESH_TOKEN is set (any non-empty value).
  - Request must pass ?token=... (or X-Admin-Token header) matching it exactly.
  - One ATS platform per call (?source=greenhouse|lever|ashby|arbeitnow|jazz)
    to fit serverless execution windows; use source=all for the CLI/local path.

Response includes partial=true when the soft time budget was hit, so the caller
can re-invoke the same source later (upserts are idempotent).
"""
from __future__ import annotations

import os
import secrets
import time

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse


def _deny(body: dict, http_status: int) -> JSONResponse:
    """رفض برمز HTTP حقيقي مع الحفاظ على شكل الجسم القديم (توافقية)."""
    return JSONResponse(status_code=http_status, content=body)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# Soft wall-clock budget for one invocation (serverless-safe).
TIME_BUDGET_SECONDS = float(os.getenv("REFRESH_TIME_BUDGET", "50"))


def _authorized(request: Request, token: str) -> bool:
    """Constant-time token check; endpoint is dead (403) when unset."""
    expected = os.getenv("ADMIN_REFRESH_TOKEN", "")
    if not expected:
        return False
    supplied = token or request.headers.get("x-admin-token", "")
    if not supplied:
        return False
    return secrets.compare_digest(supplied, expected)


@router.post("/refresh-direct")
def refresh_direct(
    request: Request,
    source: str = Query("all", description="greenhouse|lever|ashby|arbeitnow|jazz|all"),
    min_score: int = Query(2, ge=0, le=50),
    token: str = Query("", description="Admin refresh token (ADMIN_REFRESH_TOKEN)"),
):
    if not _authorized(request, token):
        return _deny({
            "ok": False,
            "status": 403,
            "error": "forbidden — set ADMIN_REFRESH_TOKEN env and pass ?token=",
        }, 403)

    # Import lazily: heavy module, and startup must stay fast.
    import sys
    from pathlib import Path

    root = str(Path(__file__).resolve().parent.parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)

    from tools import direct_employers as de

    started = time.monotonic()

    if source == "all":
        fetchers = dict(de.FETCHERS)
    elif source in de.FETCHERS:
        fetchers = {source: de.FETCHERS[source]}
    else:
        return _deny({"ok": False, "status": 400, "error": f"unknown source '{source}'",
                "allowed": [*de.FETCHERS, "all"]}, 400)

    raw = 0
    kept: list[dict] = []
    partial = False
    per_source = {}
    for name, fn in fetchers.items():
        if time.monotonic() - started > TIME_BUDGET_SECONDS:
            partial = True
            break
        try:
            batch = fn()
            raw += len(batch)
            kept.extend(de.rank_and_filter(batch, min_score))
            per_source[name] = {"fetched": len(batch), "kept": len(kept)}
        except Exception as e:  # one platform failing must not kill the call
            per_source[name] = {"error": str(e)[:200]}

    if not kept:
        return {
            "ok": True, "source": source, "fetched": raw, "upserted": 0,
            "partial": partial, "elapsed_s": round(time.monotonic() - started, 1),
            "detail": per_source,
        }

    conn, backend = de._connect_db()
    try:
        if backend == "pg":
            # Ensure table exists (matches supabase_schema.sql jobs shape).
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS jobs (
                        id TEXT PRIMARY KEY,
                        source TEXT NOT NULL,
                        title TEXT NOT NULL,
                        company TEXT,
                        location TEXT,
                        salary_raw TEXT,
                        salary_currency TEXT,
                        salary_annual DOUBLE PRECISION,
                        url TEXT,
                        category TEXT,
                        score INTEGER,
                        matched TEXT,
                        posted DATE,
                        fetched_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
            conn.commit()
        upserted = de.upsert_jobs(conn, kept, backend)
    finally:
        conn.close()

    return {
        "ok": True,
        "source": source,
        "backend": backend,
        "fetched": raw,
        "kept": len(kept),
        "upserted": upserted,
        "partial": partial,
        "elapsed_s": round(time.monotonic() - started, 1),
        "detail": per_source,
    }


@router.get("/refresh-direct/status")
def refresh_status(
    request: Request,
    token: str = Query("", description="Admin refresh token"),
):
    """Counts of direct-employer rows currently in the jobs table.
    Token accepted via ?token= or X-Admin-Token header."""
    if not _authorized(request, token):
        return _deny({"ok": False, "status": 403, "error": "forbidden"}, 403)
    from app.database_factory import fetch_all, db_exists
    if not db_exists():
        return {"ok": True, "total": 0, "sources": {}}
    rows = fetch_all(
        "SELECT source, COUNT(*) AS n FROM jobs GROUP BY source ORDER BY n DESC"
    )
    sources = {r["source"]: r["n"] for r in rows if (r.get("source") or "").startswith(
        ("greenhouse", "lever", "ashby", "arbeitnow", "jazz")
    )}
    return {"ok": True, "total": sum(sources.values()), "sources": sources}
