"""Application Configuration for ConsumerVoice."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(ROOT_DIR / ".env")


def _normalize_db_url(url: str, base_dir: Path) -> str:
    """Ensure relative SQLite database URLs are anchored to project ROOT_DIR."""
    clean_url = (url or "").strip()
    if not clean_url:
        return f"sqlite:///{base_dir / 'backend' / 'consumervoice.db'}"
    if clean_url.startswith("sqlite"):
        try:
            from sqlalchemy.engine.url import make_url
            parsed = make_url(clean_url)
            if parsed.database and parsed.database != ":memory:":
                db_path = Path(parsed.database)
                if not db_path.is_absolute():
                    abs_path = (base_dir / db_path).resolve()
                    return f"sqlite:///{abs_path}"
        except Exception:
            clean = clean_url.split("sqlite:///")[-1]
            if clean and clean != ":memory:":
                p = Path(clean)
                if not p.is_absolute():
                    return f"sqlite:///{(base_dir / p).resolve()}"
    return clean_url


class Settings:
    PROJECT_NAME: str = "ConsumerVoice"
    API_V1_PREFIX: str = "/api"
    ROOT_DIR: Path = ROOT_DIR
    DATABASE_URL: str = _normalize_db_url(os.getenv("DATABASE_URL", ""), ROOT_DIR)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    SAVED_MODELS_DIR: Path = ROOT_DIR / "backend" / "saved_models"
    DATA_PROCESSED_DIR: Path = ROOT_DIR / "data" / "processed"


settings = Settings()
