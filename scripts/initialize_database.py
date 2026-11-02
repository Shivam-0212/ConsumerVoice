#!/usr/bin/env python3
"""Database Initialization and Batch Seeding Script for ConsumerVoice.

Creates SQLite schema idempotently and imports cleaned Flipkart product reviews
in batches without duplicating records or overloading system memory.
"""

import json
import logging
import sqlite3
import sys
import time
from pathlib import Path

import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.core.config import settings
from backend.app.database.session import Base, engine
import backend.app.models.entities  # Ensure models are registered with Base.metadata
from backend.app.services.issue_detection import IssueDetector

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def init_db(limit_records: int = 50000):
    """Initialize SQLite database tables and seed with cleaned review records."""
    db_file = Path(settings.DATABASE_URL.replace("sqlite:///", ""))
    db_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Target SQLite database path: {db_file}")

    # 1. Create schema
    logger.info("Creating database tables if not already present...")
    Base.metadata.create_all(bind=engine)

    # 2. Check if already seeded
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM reviews")
    existing_count = cursor.fetchone()[0]

    if existing_count > 0:
        logger.info(f"Database already contains {existing_count:,} reviews. Skipping duplicate seeding.")
        conn.close()
        return

    csv_path = Path("data/processed/cleaned_reviews.csv")
    if not csv_path.exists():
        logger.error(f"Cleaned dataset not found at {csv_path}. Run scripts/prepare_dataset.py first.")
        conn.close()
        sys.exit(1)

    logger.info(f"Reading cleaned dataset from {csv_path} (seeding up to {limit_records:,} records)...")
    start_time = time.time()

    # Read CSV in chunks
    chunk_size = 10000
    total_inserted = 0

    insert_sql = """
    INSERT OR IGNORE INTO reviews (
        review_id, product_name, product_price, rate, cleaned_rate,
        review_text, summary, cleaned_summary, normalized_sentiment, is_benchmark
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    issue_insert_sql = """
    INSERT INTO issue_detections (
        review_id, category, aspect_sentiment, matched_evidence, confidence, detection_method
    ) VALUES (?, ?, ?, ?, ?, ?)
    """

    detector = IssueDetector()
    issues_to_insert = []

    for chunk in pd.read_csv(csv_path, chunksize=chunk_size, low_memory=False):
        records = []
        for _, row in chunk.iterrows():
            rev_id = str(row.get("review_id", f"REV_{total_inserted + len(records) + 1:06d}"))
            prod_name = str(row.get("product_name", "Unknown Product"))
            prod_price = str(row.get("product_price", ""))
            rate_raw = str(row.get("Rate", ""))
            rate_clean = float(row["cleaned_rate"]) if pd.notna(row.get("cleaned_rate")) else None
            rev_text = str(row.get("Review", "")) if pd.notna(row.get("Review")) else ""
            summary = str(row.get("Summary", "")) if pd.notna(row.get("Summary")) else ""
            cleaned_sum = str(row.get("cleaned_summary", "")) if pd.notna(row.get("cleaned_summary")) else summary
            norm_sentiment = str(row.get("normalized_sentiment", "neutral")).lower()
            is_bm = bool(row.get("is_benchmark", False))

            records.append((
                rev_id, prod_name, prod_price, rate_raw, rate_clean,
                rev_text, summary, cleaned_sum, norm_sentiment, is_bm
            ))

            # Detect issues for first 3,000 records to provide rich initial dashboard analytics
            if total_inserted + len(records) <= 3000:
                combined_text = f"{summary}. {rev_text}".strip()
                detected = detector.detect_issues(combined_text)
                for issue in detected:
                    issues_to_insert.append((
                        rev_id,
                        issue["category"],
                        issue["aspect_sentiment"],
                        issue["matched_evidence"],
                        issue["confidence"],
                        issue["detection_method"],
                    ))

            if total_inserted + len(records) >= limit_records:
                break

        cursor.executemany(insert_sql, records)
        conn.commit()
        total_inserted += len(records)
        logger.info(f"Inserted {total_inserted:,} / {limit_records:,} reviews...")

        if total_inserted >= limit_records:
            break

    # Insert seeded issue detections
    if issues_to_insert:
        logger.info(f"Seeding {len(issues_to_insert):,} pre-computed issue detections...")
        cursor.executemany(issue_insert_sql, issues_to_insert)
        conn.commit()

    conn.close()
    elapsed = time.time() - start_time
    logger.info(f"Database initialization complete in {elapsed:.2f} seconds. Total reviews: {total_inserted:,}.")


if __name__ == "__main__":
    init_db(limit_records=50000)
