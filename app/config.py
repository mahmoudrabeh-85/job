"""
config.py — إعدادات التطبيق (Pydantic Settings)
يقرأ من .env أو متغيرات البيئة تلقائياً
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ─── Server ────────────────────────────────────
    PORT: int = 8767
    HOST: str = "127.0.0.1"

    # ─── Paths (relative to project root) ──────────
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DB_PATH: str = "data/jobs.db"
    CV_DIR: str = "cv"

    # ─── CORS ──────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:8767,http://127.0.0.1:8767"

    # ─── Optional API Keys ─────────────────────────
    ADZUNA_APP_ID: str = ""
    ADZUNA_APP_KEY: str = ""

    @property
    def db_full_path(self) -> Path:
        return self.BASE_DIR / self.DB_PATH

    @property
    def cv_full_path(self) -> Path:
        return self.BASE_DIR / self.CV_DIR

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def frontend_dir(self) -> Path:
        return self.BASE_DIR / "frontend"


settings = Settings()
