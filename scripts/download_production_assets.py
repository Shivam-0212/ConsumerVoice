#!/usr/bin/env python3
"""Production Assets Downloader and Database Initializer for ConsumerVoice.

Automatically retrieves production model weights and pre-seeded SQLite database
from verified GitHub release assets during cloud deployment (e.g., Render, Railway).
Gracefully falls back to local seed datasets if network access is restricted.
"""

import gzip
import json
import logging
import os
import shutil
import sqlite3
import subprocess
import sys
import urllib.request
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("consumervoice.deploy")

ROOT_DIR = Path(__file__).resolve().parent.parent

# GitHub Release v1.0.0 CDN endpoints
BASELINE_URL = os.environ.get(
    "BASELINE_MODEL_URL",
    "https://github.com/Shivam-0212/ConsumerVoice/releases/download/v1.0.0/sentiment_baseline.joblib",
)
DB_GZ_URL = os.environ.get(
    "DATABASE_ASSET_URL",
    "https://github.com/Shivam-0212/ConsumerVoice/releases/download/v1.0.0/consumervoice.db.gz",
)

TARGET_BASELINE_PATH = ROOT_DIR / "backend" / "saved_models" / "sentiment_baseline.joblib"
TARGET_DB_PATH = ROOT_DIR / "backend" / "consumervoice.db"
SEED_SAMPLE_PATH = ROOT_DIR / "data" / "seed_sample.json"


def download_with_curl_or_urllib(url: str, dest_path: Path) -> bool:
    """Download a remote file trying curl first, then urllib with custom headers."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")

    # 1. Try curl
    try:
        cmd = ["curl", "-sSL", "--connect-timeout", "15", "--max-time", "120", url, "-o", str(temp_path)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and temp_path.exists() and temp_path.stat().st_size > 500:
            temp_path.replace(dest_path)
            logger.info(f"Successfully downloaded via curl: {dest_path.name} ({dest_path.stat().st_size:,} bytes)")
            return True
    except Exception as e:
        logger.warning(f"Curl download failed for {url}: {e}")

    # 2. Try urllib with realistic User-Agent
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; ConsumerVoiceDeploy/1.0)",
                "Accept": "*/*",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp, open(temp_path, "wb") as out:
            shutil.copyfileobj(resp, out)
        if temp_path.exists() and temp_path.stat().st_size > 500:
            temp_path.replace(dest_path)
            logger.info(f"Successfully downloaded via urllib: {dest_path.name} ({dest_path.stat().st_size:,} bytes)")
            return True
    except Exception as e:
        logger.warning(f"Urllib download failed for {url}: {e}")

    if temp_path.exists():
        temp_path.unlink()
    return False


def ensure_baseline_model() -> bool:
    """Ensure sentiment_baseline.joblib is present."""
    if TARGET_BASELINE_PATH.exists() and TARGET_BASELINE_PATH.stat().st_size > 1000:
        logger.info(f"Baseline model already present at {TARGET_BASELINE_PATH}")
        return True

    logger.info(f"Fetching baseline model from {BASELINE_URL}...")
    success = download_with_curl_or_urllib(BASELINE_URL, TARGET_BASELINE_PATH)
    if success:
        return True
    logger.warning("Could not download baseline model. Backend will report model_weights_not_deployed.")
    return False


def ensure_database() -> bool:
    """Ensure consumervoice.db is present and populated with authentic reviews."""
    if TARGET_DB_PATH.exists() and TARGET_DB_PATH.stat().st_size > 5000:
        try:
            conn = sqlite3.connect(TARGET_DB_PATH)
            count = conn.execute("SELECT count(*) FROM reviews").fetchone()[0]
            conn.close()
            if count > 0:
                logger.info(f"Database already populated with {count:,} reviews.")
                return True
        except Exception:
            pass

    # Try downloading compressed full database (50,000 records)
    gz_temp = TARGET_DB_PATH.with_suffix(".db.gz")
    logger.info(f"Fetching compressed 50,000-review database from {DB_GZ_URL}...")
    if download_with_curl_or_urllib(DB_GZ_URL, gz_temp):
        try:
            logger.info(f"Decompressing {gz_temp} to {TARGET_DB_PATH}...")
            with gzip.open(gz_temp, "rb") as f_in, open(TARGET_DB_PATH, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            gz_temp.unlink(missing_ok=True)
            conn = sqlite3.connect(TARGET_DB_PATH)
            count = conn.execute("SELECT count(*) FROM reviews").fetchone()[0]
            conn.close()
            logger.info(f"Database restored successfully with {count:,} indexed records.")
            return True
        except Exception as e:
            logger.warning(f"Decompression of database failed: {e}")
            gz_temp.unlink(missing_ok=True)

    # Fallback: Seed from seed_sample.json if present
    if SEED_SAMPLE_PATH.exists():
        logger.info("Initializing fallback database from data/seed_sample.json...")
        try:
            # Initialize schema via SQLAlchemy
            sys.path.insert(0, str(ROOT_DIR))
            from backend.app.database.session import Base, engine
            import backend.app.models.entities  # register models

            Base.metadata.create_all(bind=engine)

            with open(SEED_SAMPLE_PATH, "r", encoding="utf-8") as f:
                sample_data = json.load(f)

            conn = sqlite3.connect(TARGET_DB_PATH)
            cursor = conn.cursor()
            insert_sql = """
            INSERT OR IGNORE INTO reviews (
                review_id, product_name, product_price, rate, cleaned_rate,
                review_text, summary, cleaned_summary, normalized_sentiment, is_benchmark
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            for row in sample_data:
                cursor.execute(
                    insert_sql,
                    (
                        row.get("review_id"),
                        row.get("product_name"),
                        row.get("product_price"),
                        row.get("rate"),
                        row.get("cleaned_rate"),
                        row.get("review_text"),
                        row.get("summary"),
                        row.get("cleaned_summary"),
                        row.get("normalized_sentiment"),
                        True,
                    ),
                )
            conn.commit()
            count = cursor.execute("SELECT count(*) FROM reviews").fetchone()[0]
            conn.close()
            logger.info(f"Fallback database seeded with {count:,} authentic Flipkart reviews.")
            return True
        except Exception as e:
            logger.error(f"Fallback seeding failed: {e}")

    return False


def main():
    logger.info("Starting ConsumerVoice production asset verification...")
    model_ok = ensure_baseline_model()
    db_ok = ensure_database()
    logger.info(f"Asset check complete: baseline_model={model_ok}, database={db_ok}")


if __name__ == "__main__":
    main()
