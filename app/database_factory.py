"""
database_factory.py — Unified database interface (SQLite local, PostgreSQL on Render)
Automatically chooses the right backend based on DATABASE_URL.
"""
import os
from typing import Any

# Check if we're using PostgreSQL (Supabase) or SQLite (local)
_DATABASE_URL = os.getenv("DATABASE_URL", "")

if _DATABASE_URL and _DATABASE_URL.startswith("postgresql"):
    # PostgreSQL mode (Supabase on Render)
    from app.database_pg import (
        get_connection,
        fetch_all,
        fetch_one,
        execute,
        paginate,
        db_exists,
        init_db,
        close_pools,
    )
    _BACKEND = "postgresql"
else:
    # SQLite mode (local development)
    from app.database import (
        get_connection,
        fetch_all,
        fetch_one,
        paginate,
        db_exists,
    )
    # SQLite doesn't have execute, init_db, close_pools in the same way
    def execute(sql: str, params: list | None = None) -> int:
        import sqlite3
        from app.config import settings
        conn = sqlite3.connect(str(settings.db_full_path), check_same_thread=False)
        try:
            cur = conn.cursor()
            cur.execute(sql, params or [])
            conn.commit()
            return cur.rowcount
        finally:
            conn.close()

    def init_db():
        pass  # SQLite tables created by job_aggregator

    def close_pools():
        pass  # No pools in SQLite

    _BACKEND = "sqlite"


# Re-export the unified interface
__all__ = [
    "get_connection",
    "fetch_all",
    "fetch_one",
    "execute",
    "paginate",
    "db_exists",
    "init_db",
    "close_pools",
    "_BACKEND",
]