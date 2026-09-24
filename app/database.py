"""
database.py — SQLite access layer (sync for simplicity, thread-safe)
Provides paginated queries + helper utilities.
"""
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Any

from app.config import settings


def _ensure_db() -> bool:
    """Return True if the database file exists."""
    return settings.db_full_path.exists()


@contextmanager
def get_connection():
    """Thread-safe SQLite connection context manager."""
    if not _ensure_db():
        raise FileNotFoundError(f"Database not found: {settings.db_full_path}")
    conn = sqlite3.connect(str(settings.db_full_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def fetch_all(
    sql: str,
    params: list | None = None,
) -> list[dict[str, Any]]:
    """Execute a query and return all rows as dicts."""
    with get_connection() as conn:
        rows = conn.execute(sql, params or []).fetchall()
        return [dict(r) for r in rows]


def fetch_one(
    sql: str,
    params: list | None = None,
) -> dict[str, Any] | None:
    """Execute a query and return one row as dict or None."""
    with get_connection() as conn:
        row = conn.execute(sql, params or []).fetchone()
        return dict(row) if row else None


def paginate(
    sql_base: str,
    params: list | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """
    Add LIMIT/OFFSET to a query and return paginated results.
    Returns: {items, total, page, page_size, total_pages}
    """
    params = list(params or [])

    # Count total
    count_sql = f"SELECT COUNT(*) as cnt FROM ({sql_base})"
    with get_connection() as conn:
        total = conn.execute(count_sql, params).fetchone()["cnt"]

    # Paginate
    offset = (page - 1) * page_size
    paged_sql = f"{sql_base} LIMIT ? OFFSET ?"
    items = fetch_all(paged_sql, params + [page_size, offset])

    total_pages = max(1, (total + page_size - 1) // page_size)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def db_exists() -> bool:
    """Check if the database file exists."""
    return _ensure_db()
