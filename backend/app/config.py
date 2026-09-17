import os
import sys
from functools import lru_cache
from typing import List

from dotenv import load_dotenv

# Load .env from backend directory or current working directory
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_env_path):
    load_dotenv(dotenv_path=_env_path, override=True)
else:
    load_dotenv(override=True)



def _require_postgresql_url(url: str | None) -> str:
    """
    Validates that DATABASE_URL is set and points to a PostgreSQL database.
    Raises a clear RuntimeError if the URL is missing or incorrectly configured
    as SQLite.  Never silently falls back to SQLite.
    """
    if not url:
        raise RuntimeError(
            "\n\n"
            "  [CircularFlow AI — Phase 13] PostgreSQL DATABASE_URL is not configured.\n\n"
            "  Please set DATABASE_URL in your backend/.env file:\n\n"
            "    DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE\n\n"
            "  Hosted options (free tiers available):\n"
            "    - Neon      https://neon.tech\n"
            "    - Supabase  https://supabase.com\n"
            "    - Railway   https://railway.app\n"
            "    - ElephantSQL https://www.elephantsql.com\n\n"
            "  Phase 13 requires a REAL hosted PostgreSQL database.\n"
            "  SQLite is no longer supported as a backend for this phase.\n"
        )

    # Reject SQLite explicitly
    if url.strip().startswith("sqlite"):
        raise RuntimeError(
            "\n\n"
            "  [CircularFlow AI — Phase 13] SQLite DATABASE_URL detected — this is not allowed.\n\n"
            "  Phase 13 requires a hosted PostgreSQL database.\n"
            "  Please update DATABASE_URL in backend/.env to a PostgreSQL connection string:\n\n"
            "    DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE\n\n"
            "  or (with SSL for hosted providers):\n\n"
            "    DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE?sslmode=require\n\n"
            "  SQLite is NOT accepted. Current value starts with: sqlite\n"
        )

    # Accept postgresql:// and postgres:// (Heroku/Railway alias)
    normalized = url.strip()
    if not (normalized.startswith("postgresql://") or normalized.startswith("postgres://")):
        raise RuntimeError(
            f"\n\n"
            f"  [CircularFlow AI — Phase 13] Unrecognized DATABASE_URL scheme.\n\n"
            f"  Expected: postgresql://USER:PASSWORD@HOST:PORT/DATABASE\n"
            f"  Got:      {normalized[:40]}...\n\n"
            f"  Only PostgreSQL is supported in Phase 13.\n"
        )

    # Validate that the URL looks like it has been filled in (not a template placeholder)
    from urllib.parse import urlparse
    try:
        parsed = urlparse(normalized)
        port = parsed.port  # raises ValueError for non-numeric ports (e.g., "PORT")
        if not parsed.hostname or parsed.hostname.upper() in ("HOST", "YOUR_HOST", "HOSTNAME"):
            raise ValueError("placeholder hostname detected")
        if not parsed.username or parsed.username.upper() in ("USER", "YOUR_USERNAME", "USERNAME"):
            raise ValueError("placeholder username detected")
    except ValueError as ve:
        raise RuntimeError(
            f"\n\n"
            f"  [CircularFlow AI - Phase 13] DATABASE_URL appears to be a template placeholder, not a real connection string.\n\n"
            f"  Detected issue: {ve}\n\n"
            f"  Please replace the placeholder in backend/.env with your real PostgreSQL credentials:\n\n"
            f"    DATABASE_URL=postgresql://<username>:<password>@<host>.neon.tech:5432/<dbname>\n\n"
            f"  Free hosted PostgreSQL options:\n"
            f"    Neon:      https://neon.tech\n"
            f"    Supabase:  https://supabase.com\n"
            f"    Railway:   https://railway.app\n"
        ) from ve

    return normalized



class Settings:
    PROJECT_NAME: str = "CircularFlow AI Backend"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")

    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # ── PostgreSQL Database URL (required — no SQLite fallback in Phase 13) ──
    DATABASE_URL: str = _require_postgresql_url(os.getenv("DATABASE_URL"))

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        core_origins = {
            self.FRONTEND_URL,
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://localhost:3000",
            "http://localhost:4173",
        }
        origins_str = os.getenv("ALLOWED_ORIGINS", "")
        if origins_str:
            for o in origins_str.split(","):
                if o.strip():
                    core_origins.add(o.strip())
        return sorted(list(core_origins))

    # ── LLM Configuration (Phase 15) ──────────────────────────────────────────
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")

    # ── ChromaDB Configuration ────────────────────────────────────────────────
    CHROMA_PERSIST_DIR: str = os.getenv(
        "CHROMA_PERSIST_DIR",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_data")
    )

    # ── JWT Authentication Configuration (Phase 17) ───────────────────────────
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "circularflow-vignan-governance-secret-key-2026-phase17-jwt-token-sec")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    @property
    def is_postgresql(self) -> bool:
        return self.DATABASE_URL.startswith(("postgresql://", "postgres://"))


@lru_cache()
def get_settings() -> Settings:
    return Settings()
