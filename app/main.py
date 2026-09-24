"""
main.py — FastAPI application entry point
Run with: uvicorn app.main:app --port 8767 --reload
"""
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.routers import jobs, analysis, vet

# ─── App Creation ────────────────────────────────────────────────────────
app = FastAPI(
    title="Smart Job Matcher",
    description="منصة ذكية لمطابقة الوظائف وتحليل السيرة الذاتية",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ─── CORS ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────
app.include_router(jobs.router)
app.include_router(analysis.router)
app.include_router(vet.router)


# ─── Health Check ────────────────────────────────────────────────────────
@app.get("/api/v1/health")
def health_check():
    from app.database import db_exists
    return {
        "status": "ok",
        "db_exists": db_exists(),
        "version": "2.0.0",
    }


# ─── Static Files (Frontend) ────────────────────────────────────────────
# ─── Static Files & SPA Routes ──────────────────────────────────────────
frontend_dir = settings.frontend_dir

@app.get("/")
def serve_index():
    """Serve the SPA index.html."""
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    return {"message": "Smart Job Matcher API — visit /api/docs for documentation"}


@app.get("/landing")
def serve_landing():
    """Serve the landing page."""
    landing = frontend_dir / "landing.html"
    if landing.exists():
        return FileResponse(str(landing), media_type="text/html")
    return {"message": "Landing page not found"}


# ─── Legacy API compatibility ────────────────────────────────────────────
@app.get("/api/jobs")
def legacy_jobs(page: int = 1, page_size: int = 500):
    """Legacy endpoint — redirect to v1."""
    return jobs.list_jobs(page=page, page_size=page_size)


@app.get("/api/stats")
def legacy_stats():
    return jobs.get_stats()


# ─── Static Assets Handler ───────────────────────────────────────────────
@app.get("/{filename:path}")
def serve_static(filename: str):
    """Serve static frontend files (style.css, app.js, images)."""
    file_path = frontend_dir / filename
    if file_path.exists() and file_path.is_file():
        # Choose media type
        suffix = file_path.suffix.lower()
        media_types = {
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".ico": "image/x-icon",
            ".html": "text/html",
        }
        return FileResponse(str(file_path), media_type=media_types.get(suffix))
    # Fallback to index.html for SPA routing
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    return {"detail": "File not found"}


@app.get("/api/analyze")
def legacy_analyze(title: str = "", desc: str = "", company: str = ""):
    from app.routers.analysis import AnalyzeRequest
    return analysis.analyze_endpoint(AnalyzeRequest(title=title, description=desc, company=company))


# ─── CLI Entry Point ────────────────────────────────────────────────────
def main():
    import uvicorn
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(f"\n🎯 Smart Job Matcher على: http://{settings.HOST}:{settings.PORT}/")
    print(f"📚 API Docs: http://{settings.HOST}:{settings.PORT}/api/docs")
    print(f"🏠 Landing:  http://{settings.HOST}:{settings.PORT}/landing\n")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )


if __name__ == "__main__":
    main()
