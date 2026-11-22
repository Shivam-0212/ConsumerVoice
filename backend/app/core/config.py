"""Application Configuration for ConsumerVoice."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(ROOT_DIR / ".env")


class Settings:
    PROJECT_NAME: str = "ConsumerVoice"
    API_V1_PREFIX: str = "/api"
    ROOT_DIR: Path = ROOT_DIR
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{ROOT_DIR / 'backend' / 'consumervoice.db'}")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    SAVED_MODELS_DIR: Path = ROOT_DIR / "backend" / "saved_models"
    DATA_PROCESSED_DIR: Path = ROOT_DIR / "data" / "processed"


settings = Settings()
