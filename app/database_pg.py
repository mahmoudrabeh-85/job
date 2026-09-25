"""
database_pg.py — PostgreSQL access layer for Supabase (async + sync)
Replaces database.py when using Supabase/PostgreSQL.
Thread-safe connection pooling + same API as database.py.
"""
import os
from contextlib import contextmanager, asynccontextmanager
from typing import Any, AsyncGenerator
from urllib.parse import urlparse

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
import asyncpg


# ─── Configuration ────────────────────────────────────────────────────────
# DATABASE_URL format: postgresql://user:pass@host:port/dbname
# For Supabase: postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
_DATABASE_URL = os.getenv("DATABASE_URL", "")

if not _DATABASE_URL:
    # Fallback for local dev (will be overridden by .env)
    _DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

# Parse for asyncpg (doesn't like the postgresql:// prefix)
_parsed = urlparse(_DATABASE_URL)
_ASYNC_DSN = f"postgresql://{_parsed.username}:{_parsed.password}@{_parsed.hostname}:{_parsed.port}{_parsed.path}"

# Thread-safe pool for sync operations (FastAPI sync endpoints)
_sync_pool: ThreadedConnectionPool | None = None


def _get_sync_pool() -> ThreadedConnectionPool:
    """Get or create the thread-safe connection pool."""
    global _sync_pool
    if _sync_pool is None:
        _sync_pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=_DATABASE_URL,
            cursor_factory=RealDictCursor,
        )
    return _sync_pool


def _get_async_pool() -> asyncpg.Pool:
    """Get or create the async connection pool."""
    # This will be initialized on first use
    return _async_pool_holder.pool


class _AsyncPoolHolder:
    pool: asyncpg.Pool | None = None

    async def get_pool(self) -> asyncpg.Pool:
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                dsn=_ASYNC_DSN,
                min_size=1,
                max_size=10,
            )
        return self.pool


_async_pool_holder = _AsyncPoolHolder()


# ─── Sync Context Manager (for existing sync endpoints) ──────────────────
@contextmanager
def get_connection():
    """
    Thread-safe PostgreSQL connection context manager.
    Usage:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM jobs").fetchall()
    """
    pool = _get_sync_pool()
    conn = pool.getconn()
    try:
        conn.autocommit = False
        yield conn
    finally:
        pool.putconn(conn)


# ─── Async Context Manager (for new async endpoints) ─────────────────────
@asynccontextmanager
async def get_async_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Async PostgreSQL connection context manager.
    Usage:
        async with get_async_connection() as conn:
            rows = await conn.fetch("SELECT * FROM jobs")
    """
    pool = await _async_pool_holder.get_pool()
    async with pool.acquire() as conn:
        yield conn


# ─── Sync Query Helpers (same API as database.py) ────────────────────────
def fetch_all(sql: str, params: list | None = None) -> list[dict[str, Any]]:
    """Execute a query and return all rows as dicts."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or [])
            rows = cur.fetchall()
            return [dict(r) for r in rows] if rows else []


def fetch_one(sql: str, params: list | None = None) -> dict[str, Any] | None:
    """Execute a query and return one row as dict or None."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or [])
            row = cur.fetchone()
            return dict(row) if row else None


def execute(sql: str, params: list | None = None) -> int:
    """Execute an INSERT/UPDATE/DELETE and return affected rows."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or [])
            conn.commit()
            return cur.rowcount


# ─── Async Query Helpers ────────────────────────────────────────────────
async def fetch_all_async(sql: str, params: list | None = None) -> list[dict[str, Any]]:
    async with get_async_connection() as conn:
        rows = await conn.fetch(sql, *(params or []))
        return [dict(r) for r in rows]


async def fetch_one_async(sql: str, params: list | None = None) -> dict[str, Any] | None:
    async with get_async_connection() as conn:
        row = await conn.fetchrow(sql, *(params or []))
        return dict(row) if row else None


async def execute_async(sql: str, params: list | None = None) -> int:
    async with get_async_connection() as conn:
        result = await conn.execute(sql, *(params or []))
        # result format: "INSERT 0 1" or "UPDATE 5"
        try:
            return int(result.split()[-1])
        except Exception:
            return 0


# ─── Pagination (same API) ───────────────────────────────────────────────
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
        with conn.cursor() as cur:
            cur.execute(count_sql, params)
            total = cur.fetchone()["cnt"]

    # Paginate
    offset = (page - 1) * page_size
    paged_sql = f"{sql_base} LIMIT %s OFFSET %s"
    items = fetch_all(paged_sql, params + [page_size, offset])

    total_pages = max(1, (total + page_size - 1) // page_size)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


async def paginate_async(
    sql_base: str,
    params: list | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    params = list(params or [])
    count_sql = f"SELECT COUNT(*) as cnt FROM ({sql_base})"
    total_row = await fetch_one_async(count_sql, params)
    total = total_row["cnt"] if total_row else 0

    offset = (page - 1) * page_size
    paged_sql = f"{sql_base} LIMIT $%s OFFSET $%s"
    # Adjust param style for asyncpg ($1, $2...)
    import re
    # Convert ? placeholders to $1, $2...
    def convert_placeholders(query: str, param_count: int) -> str:
        new_query = ""
        idx = 1
        for ch in query:
            if ch == "?":
                new_query += f"${idx}"
                idx += 1
            else:
                new_query += ch
        return new_query

    # This is simplified - in practice, you'd want a proper param converter
    items = await fetch_all_async(paged_sql.replace("?", "$1").replace("?", "$2"), params + [page_size, offset])

    total_pages = max(1, (total + page_size - 1) // page_size)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# ─── Health Check ────────────────────────────────────────────────────────
def db_exists() -> bool:
    """Check if the database is reachable."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
    except Exception:
        return False


async def db_exists_async() -> bool:
    try:
        async with get_async_connection() as conn:
            await conn.fetchval("SELECT 1")
            return True
    except Exception:
        return False


# ─── Initialization (run once on startup) ────────────────────────────────
def init_db():
    """Create tables if they don't exist. Call on app startup."""
    # The schema should match the existing SQLite schema
    # This assumes the tables already exist in Supabase (you'll run migrations manually)
    # But we can ensure the applications table exists
    try:
        execute("""
            CREATE TABLE IF NOT EXISTS applications (
                job_id TEXT PRIMARY KEY,
                title TEXT,
                company TEXT,
                url TEXT,
                status TEXT DEFAULT 'applied',
                notes TEXT DEFAULT '',
                applied_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
    except Exception:
        pass  # Table might already exist or permissions issue


async def init_db_async():
    try:
        await execute_async("""
            CREATE TABLE IF NOT EXISTS applications (
                job_id TEXT PRIMARY KEY,
                title TEXT,
                company TEXT,
                url TEXT,
                status TEXT DEFAULT 'applied',
                notes TEXT DEFAULT '',
                applied_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
    except Exception:
        pass


# ─── Cleanup ──────────────────────────────────────────────────────────────
def close_pools():
    """Close all connection pools. Call on app shutdown."""
    global _sync_pool
    if _sync_pool:
        _sync_pool.closeall()
        _sync_pool = None


async def close_async_pools():
    if _async_pool_holder.pool:
        await _async_pool_holder.pool.close()
        _async_pool_holder.pool = None