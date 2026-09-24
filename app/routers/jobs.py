"""
routers/jobs.py — Jobs API endpoints
GET /api/v1/jobs          → paginated list with analysis
GET /api/v1/jobs/{job_id} → single job detail
GET /api/v1/search        → advanced search with filters
GET /api/v1/stats         → dashboard statistics
"""
from fastapi import APIRouter, Query
from typing import Optional
from pydantic import BaseModel
from app.database import paginate, fetch_all, fetch_one, db_exists, get_connection
from app.routers.analysis import analyze_job, load_cv_text

router = APIRouter(prefix="/api/v1", tags=["jobs"])

APP_STATUSES = ("applied", "interview", "offer", "rejected", "withdrawn")


def _ensure_apps_table():
    with get_connection() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS applications ("
            "job_id TEXT PRIMARY KEY, title TEXT, company TEXT, url TEXT, "
            "status TEXT DEFAULT 'applied', notes TEXT DEFAULT '', "
            "applied_at TEXT DEFAULT (datetime('now','localtime')))"
        )
        conn.commit()


class ApplyRequest(BaseModel):
    job_id: str
    title: str = ""
    company: str = ""
    url: str = ""


class ApplyStatusRequest(BaseModel):
    status: str = "applied"
    notes: str = ""


@router.get("/jobs")
def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """Return paginated list of jobs with analysis scores."""
    if not isinstance(page, int):
        page = getattr(page, "default", 1) or 1
    if not isinstance(page_size, int):
        page_size = getattr(page_size, "default", 500) or 500

    if not db_exists():
        return {"items": [], "total": 0, "page": 1, "page_size": page_size, "total_pages": 0}

    result = paginate(
        "SELECT * FROM jobs WHERE score > 0 ORDER BY score DESC",
        page=page,
        page_size=page_size,
    )

    cv_text = load_cv_text()
    enriched = []
    for j in result["items"]:
        analysis = analyze_job(cv_text, j.get("title", ""), j.get("matched", "") or j.get("title", ""))
        enriched.append(_format_job(j, analysis))

    result["items"] = enriched
    return result


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    """Return single job with full analysis."""
    if not db_exists():
        return {"error": "Database not found"}

    job = fetch_one("SELECT * FROM jobs WHERE id = ?", [job_id])
    if not job:
        return {"error": "Job not found"}

    cv_text = load_cv_text()
    analysis = analyze_job(cv_text, job.get("title", ""), job.get("matched", "") or job.get("title", ""))
    return _format_job(job, analysis)


@router.get("/search")
def search_jobs(
    q: str = Query("", description="Search query"),
    source: Optional[str] = Query(None, description="Comma-separated sources"),
    work_type: Optional[str] = Query(None, description="remote|onsite|hybrid"),
    min_score: int = Query(0, ge=0, le=100),
    max_score: int = Query(100, ge=0, le=100),
    skills: Optional[str] = Query(None, description="Comma-separated skill categories"),
    location: Optional[str] = Query(None),
    sort_by: str = Query("score_desc", description="score_desc|score_asc|date_desc|title_asc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Advanced Enterprise search with multi-facet filters, smart ranking, and aggregations."""
    if not db_exists():
        return {
            "items": [], "total": 0, "page": page, "page_size": page_size,
            "total_pages": 0, "facets": {}, "filters": {}
        }

    # Fetch candidate jobs
    jobs = fetch_all("SELECT * FROM jobs ORDER BY id DESC")
    cv_text = load_cv_text()

    # Pre-parse query terms for smart multi-term matching
    query_terms = [term.strip().lower() for term in q.split() if term.strip()]
    selected_sources = [s.strip().lower() for s in source.split(",")] if source else []
    selected_skills = [s.strip().lower() for s in skills.split(",")] if skills else []

    all_sources: dict[str, int] = {}
    work_types_count = {"all": 0, "remote": 0, "onsite": 0, "hybrid": 0}
    skill_counts: dict[str, int] = {}
    score_bracket_counts = {"high": 0, "mid": 0, "low": 0}

    filtered_jobs = []

    for j in jobs:
        analysis = analyze_job(cv_text, j.get("title", ""), j.get("matched", "") or j.get("title", ""))
        score = analysis.get("score", 0)
        formatted = _format_job(j, analysis)

        # Determine work type
        loc = (j.get("location", "") or "").lower()
        title_lower = (j.get("title", "") or "").lower()
        combined_text = f"{title_lower} {loc} {(j.get('company', '') or '').lower()} {(j.get('matched', '') or '').lower()}"

        job_work_type = "onsite"
        if "remote" in loc or "remote" in title_lower or "عن بعد" in combined_text:
            job_work_type = "remote"
        elif "hybrid" in loc or "هجين" in combined_text:
            job_work_type = "hybrid"
        formatted["work_type"] = job_work_type

        # Track facets for all jobs
        src = (j.get("source") or "other").lower()
        all_sources[src] = all_sources.get(src, 0) + 1
        work_types_count["all"] += 1
        work_types_count[job_work_type] = work_types_count.get(job_work_type, 0) + 1

        if score >= 75:
            score_bracket_counts["high"] += 1
        elif score >= 40:
            score_bracket_counts["mid"] += 1
        else:
            score_bracket_counts["low"] += 1

        matched_skills_names = [m.get("category", "").lower() for m in analysis.get("matched", [])]
        for sk in matched_skills_names:
            skill_counts[sk] = skill_counts.get(sk, 0) + 1

        # Apply Filters
        # 1. Smart Query: all terms must be found in title, company, location, or matched skills
        if query_terms:
            if not all(term in combined_text for term in query_terms):
                continue

        # 2. Source filter
        if selected_sources and src not in selected_sources:
            continue

        # 3. Location filter
        if location and location.lower() not in loc:
            continue

        # 4. Work Type filter
        if work_type and work_type.lower() != "all":
            if work_type.lower() != job_work_type:
                continue

        # 5. Score range filter
        if not (min_score <= score <= max_score):
            continue

        # 6. Skill tags filter
        if selected_skills:
            if not any(req_skill in matched_skills_names for req_skill in selected_skills):
                continue

        filtered_jobs.append(formatted)

    # Sorting
    if sort_by == "score_desc":
        filtered_jobs.sort(key=lambda x: x.get("analysis", {}).get("score", 0), reverse=True)
    elif sort_by == "score_asc":
        filtered_jobs.sort(key=lambda x: x.get("analysis", {}).get("score", 0))
    elif sort_by == "date_desc":
        filtered_jobs.sort(key=lambda x: str(x.get("posted", "")), reverse=True)
    elif sort_by == "title_asc":
        filtered_jobs.sort(key=lambda x: x.get("title", "").lower())
    else:
        filtered_jobs.sort(key=lambda x: x.get("analysis", {}).get("score", 0), reverse=True)

    total = len(filtered_jobs)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start_idx = (page - 1) * page_size
    page_items = filtered_jobs[start_idx : start_idx + page_size]

    return {
        "items": page_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "facets": {
            "sources": all_sources,
            "work_types": work_types_count,
            "scores": score_bracket_counts,
            "top_skills": sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:15],
        },
        "filters": {
            "q": q, "source": source, "work_type": work_type,
            "min_score": min_score, "max_score": max_score,
            "skills": skills, "location": location, "sort_by": sort_by
        },
    }


@router.post("/applications")
def mark_applied(req: ApplyRequest):
    """Record that the user applied to a job (tracker)."""
    _ensure_apps_table()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO applications (job_id, title, company, url, status) VALUES (?,?,?,?, 'applied') "
            "ON CONFLICT(job_id) DO UPDATE SET status='applied', applied_at=datetime('now','localtime')",
            [req.job_id, req.title, req.company, req.url],
        )
        conn.commit()
    return {"ok": True, "job_id": req.job_id, "status": "applied"}


@router.get("/applications")
def list_applications():
    """List all tracked applications, newest first."""
    _ensure_apps_table()
    return {"items": fetch_all("SELECT * FROM applications ORDER BY applied_at DESC")}


@router.patch("/applications/{job_id}")
def update_application(job_id: str, req: ApplyStatusRequest):
    """Update status/notes of a tracked application."""
    _ensure_apps_table()
    if req.status not in APP_STATUSES:
        return {"ok": False, "error": f"status must be one of {APP_STATUSES}"}
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE applications SET status=?, notes=? WHERE job_id=?",
            [req.status, req.notes, job_id],
        )
        conn.commit()
        if cur.rowcount == 0:
            return {"ok": False, "error": "not tracked yet"}
    return {"ok": True, "job_id": job_id, "status": req.status}


@router.get("/stats")
def get_stats():
    """Dashboard statistics."""
    if not db_exists():
        return {"total_jobs": 0, "avg_score": 0, "max_score": 0, "min_score": 0,
                "high_match": 0, "mid_match": 0, "low_match": 0, "sources": {}}

    jobs = fetch_all("SELECT * FROM jobs WHERE score > 0 ORDER BY score DESC")
    cv_text = load_cv_text()

    scores = []
    source_counts: dict[str, int] = {}
    for j in jobs:
        a = analyze_job(cv_text, j.get("title", ""), j.get("matched", "") or j.get("title", ""))
        scores.append(a["score"])
        src = j.get("source", "unknown")
        source_counts[src] = source_counts.get(src, 0) + 1

    high = len([s for s in scores if s > 50])
    mid = len([s for s in scores if 25 <= s <= 50])
    low = len([s for s in scores if s < 25])

    return {
        "total_jobs": len(jobs),
        "avg_score": sum(scores) // len(scores) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "min_score": min(scores) if scores else 0,
        "high_match": high,
        "mid_match": mid,
        "low_match": low,
        "sources": source_counts,
        "score_distribution": {
            "0-19": len([s for s in scores if s < 20]),
            "20-39": len([s for s in scores if 20 <= s < 40]),
            "40-59": len([s for s in scores if 40 <= s < 60]),
            "60-79": len([s for s in scores if 60 <= s < 80]),
            "80-100": len([s for s in scores if s >= 80]),
        },
    }


def _format_job(j: dict, analysis: dict) -> dict:
    """Standardize job output format."""
    return {
        "id": j.get("id", ""),
        "title": j.get("title", ""),
        "company": j.get("company", "") or "",
        "location": j.get("location", "") or "Remote",
        "salary": j.get("salary_raw", "") or "",
        "url": j.get("url", "#"),
        "source": j.get("source", ""),
        "category": j.get("category", "") or "",
        "posted": j.get("posted", ""),
        "score_db": j.get("score", 0),
        "analysis": analysis,
    }
