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
# Optional external database asset endpoint (empty by default; uses data/seed_sample.json)
DB_GZ_URL = os.environ.get("DATABASE_ASSET_URL", "").strip()

TARGET_BASELINE_PATH = ROOT_DIR / "backend" / "saved_models" / "sentiment_baseline.joblib"
SEED_SAMPLE_PATH = ROOT_DIR / "data" / "seed_sample.json"


def get_target_db_path() -> Path:
    """Resolve the SQLite database path matching FastAPI's configured DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL", "").strip()
    if not db_url:
        try:
            sys.path.insert(0, str(ROOT_DIR))
            from backend.app.core.config import settings
            db_url = settings.DATABASE_URL.strip()
        except Exception:
            pass

    if db_url.startswith("sqlite"):
        try:
            from sqlalchemy.engine.url import make_url
            parsed = make_url(db_url)
            if parsed.database and parsed.database != ":memory:":
                p = Path(parsed.database)
                return p.resolve() if p.is_absolute() else (ROOT_DIR / p).resolve()
        except Exception:
            clean = db_url.split("sqlite:///")[-1]
            if clean and clean != ":memory:":
                p = Path(clean)
                return p.resolve() if p.is_absolute() else (ROOT_DIR / p).resolve()

    return (ROOT_DIR / "backend" / "consumervoice.db").resolve()


TARGET_DB_PATH = get_target_db_path()


def download_with_curl_or_urllib(url: str, dest_path: Path) -> bool:
    """Download a remote file trying curl first, then urllib with custom headers."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")

    # 1. Try curl (using -f / --fail so HTTP 4xx/5xx return non-zero exit codes)
    try:
        cmd = ["curl", "-sSLf", "--connect-timeout", "15", "--max-time", "120", url, "-o", str(temp_path)]
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


def ensure_database(target_db_path: Path = None) -> bool:
    """Ensure SQLite database is present and populated with authentic reviews.

    If target_db_path is not specified, resolves dynamically via get_target_db_path().
    """
    target_path = target_db_path or get_target_db_path()

    if target_path.exists() and target_path.stat().st_size > 5000:
        try:
            conn = sqlite3.connect(target_path)
            # Sanitize any text cleaned_rate values to prevent type conversion errors
            try:
                conn.execute("UPDATE reviews SET cleaned_rate = CAST(rate AS REAL) WHERE typeof(cleaned_rate) = 'text'")
                conn.commit()
            except Exception:
                pass
            count = conn.execute("SELECT count(*) FROM reviews").fetchone()[0]
            conn.close()
            if count > 0:
                logger.info(f"Database already populated at {target_path} with {count:,} reviews.")
                return True
        except Exception:
            pass

    # Optional: If DATABASE_ASSET_URL is explicitly configured, download external database
    db_gz_url = os.environ.get("DATABASE_ASSET_URL", DB_GZ_URL).strip()
    if db_gz_url:
        gz_temp = target_path.with_suffix(".db.gz")
        temp_extracted = target_path.with_suffix(".decompressed.tmp")
        logger.info(f"Fetching compressed database from configured DATABASE_ASSET_URL: {db_gz_url}...")
        if download_with_curl_or_urllib(db_gz_url, gz_temp):
            try:
                logger.info(f"Decompressing {gz_temp} to staging file {temp_extracted}...")
                with gzip.open(gz_temp, "rb") as f_in, open(temp_extracted, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

                # Validate decompressed SQLite database integrity before replacing target
                conn = sqlite3.connect(temp_extracted)
                integrity = conn.execute("PRAGMA integrity_check;").fetchone()
                if not integrity or integrity[0] != "ok":
                    conn.close()
                    raise ValueError(f"SQLite integrity check failed: {integrity}")

                try:
                    conn.execute("UPDATE reviews SET cleaned_rate = CAST(rate AS REAL) WHERE typeof(cleaned_rate) = 'text'")
                    conn.commit()
                except Exception:
                    pass

                count = conn.execute("SELECT count(*) FROM reviews").fetchone()[0]
                conn.close()

                if count == 0:
                    raise ValueError("Decompressed database contains 0 reviews.")

                # Atomic replacement of target path with verified database
                temp_extracted.replace(target_path)
                gz_temp.unlink(missing_ok=True)
                logger.info(f"Database restored successfully at {target_path} with {count:,} indexed records.")
                return True
            except Exception as e:
                logger.warning(f"Validation or decompression of remote database failed: {e}. Falling back to embedded seed dataset.")
                temp_extracted.unlink(missing_ok=True)
                gz_temp.unlink(missing_ok=True)
        else:
            logger.warning(f"Failed to download database from {db_gz_url}. Falling back to embedded seed dataset.")
            gz_temp.unlink(missing_ok=True)
    else:
        logger.info("No external DATABASE_ASSET_URL configured. Initializing from embedded seed dataset.")

    # Initialize / Seed from seed_sample.json
    if SEED_SAMPLE_PATH.exists():
        logger.info(f"Initializing database at {target_path} from data/seed_sample.json...")
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # If target_path exists but is invalid or empty, remove it before initializing
            if target_path.exists():
                try:
                    test_conn = sqlite3.connect(target_path)
                    test_res = test_conn.execute("PRAGMA integrity_check;").fetchone()
                    test_conn.close()
                    if not test_res or test_res[0] != "ok":
                        target_path.unlink(missing_ok=True)
                except Exception:
                    target_path.unlink(missing_ok=True)

            # Initialize schema directly on target_path
            sys.path.insert(0, str(ROOT_DIR))
            from sqlalchemy import create_engine
            from backend.app.database.session import Base
            import backend.app.models.entities  # register models

            db_engine = create_engine(f"sqlite:///{target_path}")
            Base.metadata.create_all(bind=db_engine)
            db_engine.dispose()

            with open(SEED_SAMPLE_PATH, "r", encoding="utf-8") as f:
                sample_data = json.load(f)

            conn = sqlite3.connect(target_path)
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
            logger.info(f"Database seeded successfully at {target_path} with {count:,} authentic Flipkart reviews.")
            return True
        except Exception as e:
            logger.error(f"Fallback seeding failed: {e}")
            if target_path.exists():
                try:
                    conn.close()
                except Exception:
                    pass

    return False


def main():
    logger.info("Starting ConsumerVoice production asset verification...")
    model_ok = ensure_baseline_model()
    db_ok = ensure_database()
    logger.info(f"Asset check complete: baseline_model={model_ok}, database={db_ok}")


if __name__ == "__main__":
    main()
